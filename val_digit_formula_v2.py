"""VAL digit forecasting formula v2: conditional experts plus evidence-gated odds.

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
import heapq
import math
import random
from collections import defaultdict
from datetime import datetime
from val import GAMES

VERSION = "digit_conditional_v2"
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
        day=datetime.fromisoformat(actual["at"]).date().isoformat()
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


def forecast(game,history,stream):
    """Produce one joint probability model with an independent calibration gate."""
    e=expert_models(game,history,stream)
    check=calibration(game,history)
    qualified=check["passed"]
    if qualified:
        evidences=[max(0,check["experts"][name]["lower_bound"]) for name in qualified]
        total=sum(evidences)
        weights={name:evidence/total for name,evidence in zip(qualified,evidences)}
        # Most predictive weight remains at fair uniform: false positives are costly.
        strength=min(.50,max(.05,6*total))
    else:
        weights={}
        strength=0.
    return dict(version=VERSION,game=game,stream=stream,
                experts=e,weights=weights,signal_strength=strength,
                gate_passed=bool(qualified),calibration=check)


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


def generate_picks(game,history,stream,count=3,rng=None):
    """Production-facing replacement for three arbitrarily weighted draws."""
    if game not in ("pick3","pick4","pick5"):raise ValueError(game)
    if not 1<=count<=5:raise ValueError("Only 1-5 independent ordered candidates")
    ready=forecast(game,history,stream)
    width=GAMES[game]["size"]
    rng=rng or random.SystemRandom()
    if ready["gate_passed"]:
        combos=_top_candidates(ready,count)
    else:
        seen=set()
        while len(seen)<count:
            seen.add(tuple(rng.randrange(10) for _ in range(width)))
        combos=list(seen)
        # Arbitrary reproducible presentation order only, never a ranking
        # on supposed skill absent evidence of model advantage.
        combos.sort()
    picks=[]
    for rank,combo in enumerate(combos,1):
        picks.append(dict(numbers=list(combo),bonus=None,
                          rank=rank,
                          role="primary" if rank==1 else f"alternative_{rank-1}",
                          ranking_version=VERSION,
                          model_weight_score=joint_probability(ready,combo),
                          signal_gate_passed=ready["gate_passed"],
                          formula_version=VERSION))
    meta=dict(formula_version=VERSION,
              signal_gate_passed=ready["gate_passed"],
              signal_strength=ready["signal_strength"],
              passed_experts=ready["calibration"]["passed"],
              calibration_observations=ready["calibration"]["observations"],
              calibration_cluster_days=ready["calibration"]["cluster_days"])
    return picks,meta
