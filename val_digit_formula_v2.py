"""VAL digit Box v4: online cumulative-evidence experts plus calibrated Box ranking.

This replaces the *formula*, not just the scoring infrastructure. The
candidate experts model history-dependent digit probabilities; live probability
mass is moved away from uniform ONLY if chronological calibration establishes
an improvement with conservative, family-adjusted uncertainty bounds.
An unsuccessful search returns mathematically fair 10% digit probabilities,
not an invented winning advantage.

Models:
* long_1500: position-specific persistent bias with a Dirichlet prior.
* recent_100: recent position changes, strongly smoothed.
* same_session: Day/Night-specific position distributions.
* markov: previous completed draw -> next drawing, same digit position.
* internal_chain: digit at current position conditioned on previous position
  *within the target combination*. Joint ticket odds use the full chain.

A true joint mixture, not a product of separately averaged marginals, is
used for all ordered combination likelihoods. Up to 3 candidate tickets are
chosen by a beam-search approximation to the largest joint probabilities
ONLY when the signal gate passes; otherwise unique fair random picks are
returned. All code is standard-library Python 3.11+.
"""
from __future__ import annotations

import hashlib
from itertools import combinations_with_replacement
from val_box import any_order_prize, box_ways, distinct_permutations, random_box_picks
import heapq
import math
import random
from collections import defaultdict, deque
from val_box_challenger import BoxEvidence, EXPERTS as ONLINE_EXPERT_NAMES, LOG_GATE as ONLINE_LOG_GATE
from datetime import datetime
from val import GAMES,ET

VERSION = "digit_box_v4"
EXPERT_NAMES = ("long_1500", "recent_100", "same_session",
                "markov", "internal_chain")
LONG_WINDOW = 1500
SHORT_WINDOW = 100
SESSION_WINDOW = 900
VALIDATION_DRAWS = 420
VALIDATION_STRIDE = 3
MIN_VALIDATION = 70
# One-sided threshold is intentionally more conservative than 95%,
# because five expert families, three games and ongoing probes are tested.
EVIDENCE_Z = 3.20
MIN_LOG_GAIN = .002
BEAM_WIDTH = 450
# Before a cumulative online expert can generate production numbers, its
# prequential likelihood must show improvement in BOTH recent subperiods.
ONLINE_CONFIRM_DRAWS = 400
ONLINE_CONFIRM_MIN = 240
ONLINE_MIN_MEAN_GAIN = .002
# Fixed regimes reset obsolete evidence debt without repeatedly searching
# arbitrary sliding-window origins. Epoch index is deterministic from the
# official draw count after a fixed 2024-01-01 anchor. Fair-null alpha is
# allocated across ALL future epochs as 1/((epoch+1)*(epoch+2)).
ONLINE_EPOCH_ANCHOR = "2024-01-01"
ONLINE_EPOCH_DRAWS = 1600
ONLINE_PREWARM_DRAWS = 700
FORMULA_REVISION = "fixed_epoch_evidence_v1"


def stable_rng(*parts):
    key = "|".join(map(str,(VERSION,)+parts)).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(key).digest()[:8],"big"))


def _probs(counts,pseudo):
    if len(counts)!=10 or pseudo<=0: raise ValueError("Bad predictive counts")
    total=sum(counts)+10*pseudo
    result=[(c+pseudo)/total for c in counts]
    if abs(sum(result)-1)>1e-10 or any(not (0<p<1) for p in result):
        raise AssertionError("Unnormalized probability forecast")
    return result


def expert_models(game,previous,stream):
    """Only earlier draws can enter the conditional features."""
    if game not in ("pick3","pick4","pick5"): raise ValueError(game)
    width=GAMES[game]["size"]
    if len(previous)<50:raise ValueError("At least 50 completed draws required")
    rows=previous[-LONG_WINDOW:]
    pos_counts=[[0]*10 for _ in range(width)]
    recent_counts=[[0]*10 for _ in range(width)]
    session_counts=[[0]*10 for _ in range(width)]
    transitions=[[[0]*10 for _ in range(10)] for _ in range(width)]
    chain_counts=[[[0]*10 for _ in range(10)] for _ in range(width)]
    last=None
    for idx,row in enumerate(rows):
        numbers=row["numbers"]
        if len(numbers)!=width or any(type(n)!=int or not 0<=n<=9 for n in numbers):
            raise ValueError("Invalid earlier digit draw")
        for pos,digit in enumerate(numbers):
            pos_counts[pos][digit]+=1
            if idx>=len(rows)-SHORT_WINDOW:
                recent_counts[pos][digit]+=1
            if row["stream"]==stream and idx>=len(rows)-SESSION_WINDOW:
                session_counts[pos][digit]+=1
            if last is not None:
                transitions[pos][last[pos]][digit]+=1
            if pos>0:
                chain_counts[pos][numbers[pos-1]][digit]+=1
        last=numbers
    modeled={}
    modeled["long_1500"]={
        "marginal":[_probs(x,20) for x in pos_counts],
        "within":None}
    modeled["recent_100"]={
        "marginal":[_probs(x,60) for x in recent_counts],
        "within":None}
    modeled["same_session"]={
        "marginal":[_probs(x,45) for x in session_counts],
        "within":None}
    modeled["markov"]={
        "marginal":[_probs(transitions[i][last[i]],55) for i in range(width)],
        "within":None}
    modeled["internal_chain"]={
        "marginal":[_probs(pos_counts[0],25)]+[[.1]*10 for _ in range(width-1)],
        "within":[None]+[[_probs(chain_counts[i][d],55)
                          for d in range(10)] for i in range(1,width)]}
    return modeled


def path_probability(model,numbers):
    product=1.
    for i,d in enumerate(numbers):
        matrix=model["within"]
        distribution=(matrix[i][numbers[i-1]] if matrix is not None and i>0
                      else model["marginal"][i])
        product*=distribution[d]
    return product


def prefix_probability(model,partial):
    return path_probability(model,partial)


def expert_log_gain(model,actual):
    chance=path_probability(model,actual)
    if chance<=0:raise AssertionError("Impossible outcome under smoothed expert")
    return math.log(chance)+len(actual)*math.log(10)


def calibration(game,history):
    """Chronologically evaluate historical *one-step-ahead* forecasts.

    Never compare an expert with a draw included in its own fit.
    Day clusters avoid treating two same-day results as independent.
    """
    if len(history)<600:
        return dict(observations=0,cluster_days=0,passed=[],
                    experts={name:{"mean_gain":0,"lower_bound":None} for name in EXPERT_NAMES})
    first=max(500,len(history)-VALIDATION_DRAWS)
    days={name:defaultdict(list) for name in EXPERT_NAMES}
    observations=0
    for i in range(first,len(history),VALIDATION_STRIDE):
        actual=history[i]
        models=expert_models(game,history[:i],actual["stream"])
        day=datetime.fromisoformat(actual["at"]).astimezone(ET).date().isoformat()
        for name in EXPERT_NAMES:
            days[name][day].append(expert_log_gain(models[name],actual["numbers"]))
        observations+=1
    stats={}
    passed=[]
    for name in EXPERT_NAMES:
        # Aggregate per day and use cluster-robust t approximation.
        daily=[sum(x)/len(x) for x in days[name].values()]
        n=len(daily)
        mean=sum(daily)/n if n else 0.
        if n>1:
            var=sum((x-mean)**2 for x in daily)/(n-1)
            stderr=math.sqrt(var/n)
        else:stderr=float("inf")
        lower=mean-EVIDENCE_Z*stderr
        half=n//2
        early=sum(daily[:half])/half if half else 0.
        late=sum(daily[half:])/(n-half) if n-half else 0.
        eligible=(observations>=MIN_VALIDATION and n>=MIN_VALIDATION//2 and
                  lower>MIN_LOG_GAIN and early>0 and late>0)
        stats[name]=dict(
            observations=observations,cluster_days=n,
            mean_gain=mean,lower_bound=lower if math.isfinite(lower) else None,
            earlier_mean=early,later_mean=late,passed=eligible)
        if eligible:passed.append(name)
    return dict(observations=observations,cluster_days=stats[EXPERT_NAMES[0]]["cluster_days"],
                experts=stats,passed=passed)


def _online_evidence(game, history, stream):
    """Fit a conditional digit formula and verify strictly past-only evidence.

    For each historical drawing, score experts BEFORE observing that draw.
    The fixed anytime threshold limits false positives under iid-fair draws;
    recent-half checks protect against an obsolete or reversed pattern.
    """
    # The old lifetime process could carry negative evidence from decades
    # earlier into a genuinely new drawing regime, preventing detection.
    # Count evidence only inside predeclared nonoverlapping epochs.
    eligible_rows = [
        row for row in history if
        datetime.fromisoformat(row["at"]).astimezone(ET).date().isoformat()
        >= ONLINE_EPOCH_ANCHOR
    ]
    epoch = len(eligible_rows) // ONLINE_EPOCH_DRAWS
    offset = epoch * ONLINE_EPOCH_DRAWS
    prewarm = eligible_rows[max(0,offset-ONLINE_PREWARM_DRAWS):offset]
    current = eligible_rows[offset:]
    # Bonferroni over four experts and three games, plus alpha spending
    # across infinitely many epochs: sum 1/((k+1)*(k+2)) = 1.
    threshold = ONLINE_LOG_GATE + math.log((epoch+1)*(epoch+2))
    machine = BoxEvidence(game)
    for row in prewarm:
        machine.observe(row)
    # Prewarming provides past-only model parameters, NEVER counted evidence.
    machine.log_e = {name:0. for name in ONLINE_EXPERT_NAMES}
    recent = {name: deque(maxlen=ONLINE_CONFIRM_DRAWS)
              for name in ONLINE_EXPERT_NAMES}
    for row in current:
        previous = dict(machine.log_e)
        scored = machine.seen >= machine.warmup
        machine.observe(row)
        if scored:
            for name in ONLINE_EXPERT_NAMES:
                recent[name].append(machine.log_e[name] - previous[name])
    candidates = [name for name in ONLINE_EXPERT_NAMES
                  if machine.log_e[name] >= threshold and
                  len(recent[name]) >= ONLINE_CONFIRM_MIN]
    active = max(candidates,key=lambda name: machine.log_e[name]) if candidates else None
    gains = list(recent[active]) if active else []
    n = len(gains)
    half = n // 2
    first = sum(gains[:half]) / half if half else 0.
    second = sum(gains[half:]) / (n - half) if n > half else 0.
    mean = sum(gains) / n if n else 0.
    confirmed = (active is not None and n >= ONLINE_CONFIRM_MIN and
                 first > 0. and second > 0. and mean > ONLINE_MIN_MEAN_GAIN)
    forecasts = machine.forecasts(stream)
    model = None
    if confirmed:
        marginals, conditional = forecasts[active]
        width = GAMES[game]["size"]
        model = {
            "marginal": ([list(row) for row in marginals] if conditional is None
                         else [list(marginals[0])] + [[.1]*10
                                                        for _ in range(width-1)]),
            "within": (None if conditional is None else
                       [None] + [[list(row) for row in conditional]
                                 for _ in range(width-1)]),
        }
    return dict(active=active, confirmed=confirmed, model=model,
                log_evidence={name:machine.log_e[name] for name in ONLINE_EXPERT_NAMES},
                threshold=threshold, epoch=epoch,
                epoch_draws=len(current), prewarm_draws=len(prewarm),
                anchor=ONLINE_EPOCH_ANCHOR, formula_revision=FORMULA_REVISION,
                recent_n=n,
                recent_mean=mean, recent_first_half=first,
                recent_second_half=second)


def forecast(game,history,stream):
    """Produce one joint probability model with an independent calibration gate."""
    e=expert_models(game,history,stream)
    check=calibration(game,history)
    online=_online_evidence(game,history,stream)
    qualified=list(check["passed"])
    if online["confirmed"]:
        # Change the ACTUAL production probability formula, not just a report.
        # A qualified normalized conditional distribution participates in the
        # joint model used for ranking complete Any Order combinations.
        key="online_"+online["active"]
        e[key]=online["model"]
        qualified=[key]
        check["passed"]=qualified
        check["experts"][key]=dict(
            mean_gain=online["recent_mean"],
            lower_bound=online["recent_mean"],
            passed=True,observations=online["recent_n"])
    if qualified:
        evidences=[max(0,check["experts"][name]["lower_bound"]) for name in qualified]
        total=sum(evidences)
        weights={name:evidence/total for name,evidence in zip(qualified,evidences)}
        # Most predictive weight remains at fair uniform: false positives are costly.
        strength=(min(.50,max(.10,.10+10*online["recent_mean"]))
                  if online["confirmed"] else
                  min(.50,max(.05,6*total)))
    else:
        weights={}
        strength=0.
    return dict(version=VERSION,formula_revision=FORMULA_REVISION,
                game=game,stream=stream,
                experts=e,weights=weights,signal_strength=strength,
                gate_passed=bool(qualified),calibration=check,
                online_evidence={name:value for name,value in online.items()
                                 if name!="model"})


def joint_probability(ready,numbers):
    width=GAMES[ready["game"]]["size"]
    if len(numbers)!=width:raise ValueError("Wrong number of positions")
    strength=ready["signal_strength"]
    p=(1-strength)*10.**(-width)
    for name,weight in ready["weights"].items():
        p+=strength*weight*path_probability(ready["experts"][name],numbers)
    return p


def log_gain(ready,actual):
    p=joint_probability(ready,actual)
    return math.log(p)+len(actual)*math.log(10)


def _top_candidates(ready,n):
    """Beam over exact joint-mixture PREFIX probabilities.

    Every expert is a normalized joint model, so prefix probabilities are
    valid marginal likelihoods, including the conditional chain expert.
    """
    width=GAMES[ready["game"]]["size"]
    beam=[()]
    for depth in range(1,width+1):
        next_items=[]
        for prefix in beam:
            for digit in range(10):
                candidate=prefix+(digit,)
                # All generative experts are normalized; prefix mass sums
                # over all completions, so ranking prefixes is coherent.
                p=(1-ready["signal_strength"])*10.**(-depth)
                for name,weight in ready["weights"].items():
                    p+=ready["signal_strength"]*weight*prefix_probability(
                        ready["experts"][name],candidate)
                next_items.append((p,candidate))
        beam=[candidate for _,candidate in heapq.nlargest(
            BEAM_WIDTH,next_items,key=lambda item:(item[0],item[1]))]
    ranked=sorted(beam,key=lambda numbers:(joint_probability(ready,numbers),numbers),
                  reverse=True)
    return ranked[:n]


def _top_box_candidates(ready,n):
    """Rank COMPLETE unordered digit multisets by total predictive mass.

    Each Box candidate's likelihood is the sum over its DISTINCT full
    permutations. That handles repeated digits correctly. Excludes
    single-way all-identical Straight-only patterns. Under a fair
    distribution, all-distinct sets naturally have the most coverage.
    """
    width=GAMES[ready["game"]]["size"]
    ranked=[]
    for numbers in combinations_with_replacement(range(10),width):
        if not any_order_prize(ready["game"],numbers):
            continue
        p=sum(joint_probability(ready,arrangement)
              for arrangement in distinct_permutations(numbers))
        ranked.append((p,numbers))
    ranked.sort(key=lambda item:(-item[0],item[1]))
    return [combo for _,combo in ranked[:n]]


def generate_picks(game,history,stream,count=3,rng=None,return_forecast=False):
    """Production-facing replacement for three arbitrarily weighted draws."""
    if game not in ("pick3","pick4","pick5"):raise ValueError(game)
    if not 1<=count<=5:raise ValueError("Only 1-5 independent ordered candidates")
    ready=forecast(game,history,stream)
    width=GAMES[game]["size"]
    rng=rng or random.SystemRandom()
    if ready["gate_passed"]:
        combos=_top_box_candidates(ready,count)
    else:
        # Maximize any-order outcome coverage under the fair null.
        # Three different digit sets cover nonoverlapping Box outcomes.
        combos=[tuple(p["numbers"]) for p in random_box_picks(game,count,rng)]
    picks=[]
    for rank,combo in enumerate(combos,1):
        box_probability=sum(joint_probability(ready,arrangement)
                            for arrangement in distinct_permutations(combo))
        picks.append(dict(numbers=list(combo),bonus=None,
                          rank=rank,
                          role="primary" if rank==1 else f"alternative_{rank-1}",
                          ranking_version=VERSION+"_"+FORMULA_REVISION,
                          formula_revision=FORMULA_REVISION,
                          model_weight_score=box_probability,
                          box_probability=box_probability,
                          box_ways=box_ways(combo),
                          box_payout_usd_1_dollar=any_order_prize(game,combo),
                          play_type="any_order",
                          signal_gate_passed=ready["gate_passed"],
                          formula_version=VERSION))
    meta=dict(formula_version=VERSION,formula_revision=FORMULA_REVISION,
              play_type="any_order",
              ticket_stake_usd=1,
              complete_multiset_match_required=True,
              signal_gate_passed=ready["gate_passed"],
              signal_strength=ready["signal_strength"],
              passed_experts=ready["calibration"]["passed"],
              calibration_observations=ready["calibration"]["observations"],
              calibration_cluster_days=ready["calibration"]["cluster_days"],
              online_evidence=ready["online_evidence"])
    return (picks,meta,ready) if return_forecast else (picks,meta)
