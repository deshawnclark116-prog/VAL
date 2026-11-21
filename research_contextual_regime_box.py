"""Real and synthetic head-to-head of a new contextual-regime Box engine.

Every individual forecast is frozen BEFORE the corresponding drawing result.
Real dataset: official archive, 2025-2026 previously inspected — EXPLORATORY.
True real input features are only date/session and past observed results:
the official archive does NOT prove equipment IDs were public pre-cutoff.

Controlled simulations additionally separate an entirely hidden machine from
a machine whose identity/pretests are explicitly published before a mock
wager cutoff. Never treat the latter as a real-world data source.

Primary outcome: complete unordered Box multiset hit from 3 separate tickets.
Secondary: properly normalized whole-ordered-outcome prequential log gain.
No retuning on historical performance and NO promotion based on this test.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter,deque
from datetime import datetime,date,timedelta,timezone,time
from pathlib import Path

from research_decades import fetch_full
from research_pooled_digit_followup import probabilities as pooled_digits
from research_virtual_draw_lab import truth_distribution, choose
from val import ET
from val_box import box_ways,digits_key,random_box_picks
from val_pooled_box_formula import top_box_portfolio
from val_contextual_regime_box import ContextualBox,VERSION
from val_digit_formula_v2 import generate_picks as live_v4_picks

GAMES=("pick3","pick4","pick5")
REPORT=Path("reports/contextual_regime_box_v1.md")
JSON_REPORT=Path("reports/contextual_regime_box_v1.json")
START_YEAR=2025
REAL_PRIOR_DRAWS=2400
LIVE_SPARSE_PROBES=3
SYNTHETIC_CASES=("fair_independent","day_only_bias",
                 "halfway_replacement","hidden_opposing_machines")
SYNTHETIC_TRAIN=950
SYNTHETIC_TEST=450
SYNTHETIC_REPLICATES=(41,42)
MAX_TICKETS=3
POOLED_WINDOW=5000
POOLED_PSEUDO=200.


def stable_rng(*things):
    raw="|".join(map(str,(VERSION,)+things)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8],"big"))


def local_day(row):
    if row.get("date"):
        return row["date"]
    return datetime.fromisoformat(row["at"]).astimezone(
        ET).date().isoformat()


def prior_target(row,public_equipment=False):
    target=dict(date=local_day(row),stream=row["stream"])
    # Only simulated rows supply equipment. The real archive's 'source'
    # and timestamp never authenticate the machine ID for pre-wager use.
    if public_equipment:
        if "machine" not in row or "pretests" not in row:
            raise ValueError("Synthetic public feature missing")
        original=datetime.fromisoformat(row["at"])
        deadline=original-timedelta(minutes=15)
        published=original-timedelta(hours=3)
        observed=original-timedelta(hours=2,minutes=50)
        target["wagers_close_utc"]=deadline.isoformat()
        def wrapper(value,tag):
            return dict(value=value,
                        source_url="synthetic-test://"+tag,
                        published_at_utc=published.isoformat(),
                        observed_at_utc=observed.isoformat())
        target["observables"]=dict(
            equipment_id=wrapper(row["machine"],"equipment"),
            pretests=wrapper(row["pretests"],"pretests"))
    return target


def equivalent_at(row):
    if row.get("at"):
        return dict(at=row["at"],stream=row["stream"],
                    numbers=list(row["numbers"]))
    d=date.fromisoformat(row["date"])
    hour,minute=(13,59) if row["stream"]=="Day" else (23,0)
    dt=datetime.combine(d,time(hour,minute),tzinfo=ET)
    return dict(at=dt.astimezone(timezone.utc).isoformat(),
                stream=row["stream"],numbers=list(row["numbers"]))


def box_hit(picks,winner):
    expected=digits_key(winner)
    return int(expected in {digits_key(t) for t in picks})


def fair_coverage(game,picks):
    width=int(game[-1])
    return sum(box_ways(t) for t in
               {digits_key(t) for t in picks})/10**width


def _aggregate(events):
    if not events:
        return {}
    methods=("context","pooled","fair_random")
    n=len(events)
    stats={}
    for method in methods:
        wins=sum(e[method]["full_box_win"] for e in events)
        mass=sum(e[method]["fair_coverage"] for e in events)
        stats[method]=dict(complete_box_wins=wins,
                           fair_expected_wins=mass,
                           complete_box_rate=wins/n,
                           excess_vs_fair_expectation=wins-mass,
                           avg_prequential_joint_log_gain=sum(
                               e[method]["joint_log_gain"] for e in events)/n)
    by_day={}
    for row in events:
        day=row["date"]
        by_day[day]=by_day.get(day,0)+(
            row["context"]["full_box_win"]-
            row["fair_random"]["full_box_win"])
    blocks=list(by_day.values())
    rng=stable_rng("bootstrap",events[0]["game"],events[0]["scenario"],n)
    sims=sorted(sum(blocks[rng.randrange(len(blocks))]
                    for _ in blocks) for _ in range(1200))
    return dict(draws=n,metrics=stats,
                context_minus_random_full_box_wins=(
                    stats["context"]["complete_box_wins"]-
                    stats["fair_random"]["complete_box_wins"]),
                paired_day_bootstrap_ci_95pct=[
                    sims[30],sims[1170]],
                metadata_feature_rows=sum(
                    bool(row["eligible_features"]) for row in events),
                mean_fair_weight=sum(e["fair_weight"] for e in events)/n)


def evaluate(game,rows,start_idx,scenario,public_equipment=False,
             run_live_probe=False):
    width=int(game[-1])
    engine=ContextualBox(game)
    counts=Counter()
    rolling=deque()
    events=[]
    targets=len(rows)-start_idx
    probes=set()
    if run_live_probe and targets>0:
        probes={start_idx + min(targets-1,
                               int((k+.5)*targets/LIVE_SPARSE_PROBES))
                for k in range(LIVE_SPARSE_PROBES)}
    sampled_live=[]
    prev_raw=[]
    for idx,row in enumerate(rows):
        context=prior_target(row,public_equipment)
        frozen=engine.forecast(context)
        if idx>=start_idx:
            model=engine.choose(frozen,MAX_TICKETS)["picks"]
            if len({digits_key(x) for x in model})!=MAX_TICKETS:
                raise AssertionError("Duplicate entire Box prediction")
            pool=pooled_digits([counts[d] for d in range(10)],width)
            pooled=[p["numbers"] for p in
                    top_box_portfolio(game,pool,MAX_TICKETS)]
            fair=[x["numbers"] for x in random_box_picks(
                game,MAX_TICKETS,
                stable_rng(game,scenario,local_day(row),row["stream"],
                           idx,"control"))]
            outcome=list(row["numbers"])
            measured=engine.score(frozen,outcome)
            scored=dict(game=game,scenario=scenario,
                        date=local_day(row),stream=row["stream"],
                        winning_numbers=outcome,
                        fair_weight=frozen["weights"]["fair"],
                        eligible_features=list(frozen["eligible_features"]))
            for name,picks in (
                ("context",model),("pooled",pooled),("fair_random",fair)):
                scored[name]=dict(
                    picks=picks,
                    full_box_win=box_hit(picks,outcome),
                    fair_coverage=fair_coverage(game,picks),
                    joint_log_gain=(
                        measured["log_gain"] if name=="context"
                        else sum(math.log(pool[d]/.1)
                                 for d in outcome) if name=="pooled"
                        else 0.)
                )
            events.append(scored)
            if idx in probes:
                # This is the deployed v4 function, on the exact same
                # historical TARGET, passing only all completed earlier
                # rows. These are predeclared sparse diagnostic probes,
                # not a like-for-like full-period v4 comparison.
                picks,meta=live_v4_picks(
                    game,prev_raw,row["stream"],3,
                    rng=stable_rng(game,"live_v4",local_day(row),
                                   row["stream"]))
                sampled_live.append(dict(
                    date=local_day(row),stream=row["stream"],
                    full_box_win=box_hit(
                        [p["numbers"] for p in picks],outcome),
                    signal_gate_passed=meta["signal_gate_passed"],
                    frozen_picks=[p["numbers"] for p in picks]))
            if len(events)%450==0:
                print("PROGRESS",game,scenario,len(events),
                      "/",targets,flush=True)
        # Scoring has finished. Only now can the result train the model.
        engine.observe(context,row["numbers"],frozen)
        draw=list(row["numbers"])
        rolling.append(draw)
        counts.update(draw)
        if len(rolling)>POOLED_WINDOW:
            old=rolling.popleft()
            counts.subtract(old)
        if run_live_probe:
            prev_raw.append(equivalent_at(row))
    result=_aggregate(events)
    result["v4_sparse_probe"]=dict(draws=len(sampled_live),
                                   full_box_wins=sum(
                                       x["full_box_win"] for x in
                                       sampled_live),
                                   details=sampled_live)
    return dict(summary=result,events=events)


def real_study(game):
    rows,_=fetch_full(game)
    rows=sorted(rows,key=lambda row:(
        row["date"],0 if row["stream"]=="Day" else 1))
    first=next(i for i,row in enumerate(rows)
               if row["date"][:4]>=str(START_YEAR))
    start=max(0,first-REAL_PRIOR_DRAWS)
    subset=rows[start:]
    report=evaluate(game,subset,first-start,"real_official",
                    public_equipment=False,run_live_probe=True)
    report["data_not_untouched"]=True
    return report


def simulate_temporally_valid(game,scenario,n,seed):
    """Invented physical drawing: equipment chosen, pretests, THEN result.

    Using the same immutable seed gives exactly the same simulated outcomes
    whether equipment observations are withheld or published in advance.
    This avoids any post-target pretest or accidental oracle leakage.
    """
    if game not in GAMES or n%2:
        raise ValueError("Simulated game/draws must be valid Day/Night pairs")
    width=int(game[-1])
    rng=stable_rng("chronological_machine",game,scenario,seed)
    start=date(2026,1,1)
    rows=[]
    machine=None
    for idx in range(n):
        day=start+timedelta(days=idx//2)
        stream="Day" if idx%2==0 else "Night"
        if idx%2==0:
            machine=rng.randrange(2)
        def draw_numbers():
            outcome=[]
            for position in range(width):
                p=truth_distribution(
                    scenario,width,stream,machine,idx/n,
                    position,outcome)
                outcome.append(choose(rng,p))
            return outcome
        # Pretest observations are generated before the target official draw
        # in the *actual synthetic event sequence*, not just relabeled.
        pretests=[draw_numbers() for _ in range(2)]
        result=draw_numbers()
        hour,minute=(13,59) if stream=="Day" else (23,0)
        timestamp=datetime.combine(
            day,time(hour,minute),tzinfo=ET).astimezone(
                timezone.utc).isoformat()
        rows.append(dict(
            game=game,at=timestamp,stream=stream,numbers=result,
            machine=machine,pretests=pretests,
            simulation_pretests_before_official=True))
    return rows


def synthetic_study(game,scenario,public):
    events=[]
    for seed in SYNTHETIC_REPLICATES:
        n=SYNTHETIC_TRAIN+SYNTHETIC_TEST
        rows=simulate_temporally_valid(game,scenario,n,seed)
        part=evaluate(game,rows,SYNTHETIC_TRAIN,
                      scenario+("_public_equipment" if public
                               else "_hidden_equipment"),
                      public_equipment=public)
        events.extend(part["events"])
    return dict(summary=_aggregate(events))


def markdown(data):
    lines=[
        "# VAL adaptive contextual Box forecast — actual predictions",
        "",
        "The candidate is a NEW prediction engine, not an auditing layer.",
        "Experts: recent-regime positional model; weekday+session",
        "posterior; independently timestamp-verified equipment and",
        "pretest data when available; and a fair baseline. Expert",
        "weights adapt using only earlier complete-draw likelihood.",
        "Picks maximize predicted probability of a whole unordered",
        "digit combination (all digits including repeats), never",
        "partial matches or ordered-position hits.",
        "",
        "## Real Virginia Lottery 2025–2026 predictions",
        "",
        "The entire real history has been explored before. Results below",
        "are exploratory chronological backtests, not an untouched",
        "validation set. No real machine/pretest metadata is silently",
        "inferred or injected from the simulator.",
        "",
        "| Game | Actual target draws | New contextual Box wins | Pooled Box wins | Random Box wins | New mean joint log gain | New - random 95% paired hit CI |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for game,body in data["real"].items():
        r=body["summary"];m=r["metrics"]
        lines.append(
            f'| {game} | {r["draws"]} | '
            f'{m["context"]["complete_box_wins"]} | '
            f'{m["pooled"]["complete_box_wins"]} | '
            f'{m["fair_random"]["complete_box_wins"]} | '
            f'{m["context"]["avg_prequential_joint_log_gain"]:+.6f} | '
            f'{r["paired_day_bootstrap_ci_95pct"]} |')
    lines.extend([
        "",
        "## Equipment genuinely unavailable vs available in invented scenarios",
        "",
        "Public equipment here means **hypothetical** machine/pretest",
        "observations, generated before the simulated winning draw and",
        "explicitly timestamped BEFORE its synthetic cutoff.",
        "Hidden scenarios do not allow the predictor to read the simulator",
        "machine field or private pretests. This does NOT demonstrate",
        "that this information is public before real Virginia wagers.",
        "",
        "| Game | Artificial scenario | Test draws | Contextual Box wins | Random Box wins | Context joint log gain | Eligible metadata draws |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for game,part in data["simulated"].items():
        for key,p in part.items():
            r=p["summary"];m=r["metrics"]
            lines.append(
                f'| {game} | {key} | {r["draws"]} | '
                f'{m["context"]["complete_box_wins"]} | '
                f'{m["fair_random"]["complete_box_wins"]} | '
                f'{m["context"]["avg_prequential_joint_log_gain"]:+.6f} | '
                f'{r["metadata_feature_rows"]} |')
    lines.extend([
        "",
        "## Production decision",
        "",
        "No production changes from this exploratory study.",
        "A real model promotion requires pre-frozen predictions",
        "with stronger full Box and proper probability performance",
        "on genuinely new outcomes and independent evidence that",
        "external features were publicly available before wagering",
        "closed. Synthetic machine IDs are never evidence of this.",
        "",
        "The deployed digit_box_v4 formula is probed on a small,",
        "predeclared set of actual targets per game; those probe",
        "results are in the JSON, not a full-window head-to-head.",
        "",
        "[Target-by-target research JSON](contextual_regime_box_v1.json).","",
    ])
    return "\n".join(lines)


def main():
    data=dict(version=VERSION,
              timestamp_utc=datetime.now(timezone.utc).isoformat(),
              external_equipment_usable_in_real_lottery=False,
              real_already_inspected=True,live_champion_unchanged=True,
              real={},simulated={})
    for game in GAMES:
        print("START real",game,flush=True)
        data["real"][game]=real_study(game)
        s=data["real"][game]["summary"]
        print("REAL",game,s["draws"],{
            name:[m["complete_box_wins"],
                  round(m["avg_prequential_joint_log_gain"],5)]
            for name,m in s["metrics"].items()},
            "live probe",s["v4_sparse_probe"]["full_box_wins"],
            flush=True)
    for game in GAMES:
        data["simulated"][game]={}
        for scenario in SYNTHETIC_CASES:
            variants=(False,True) if scenario=="hidden_opposing_machines" else (False,)
            for public in variants:
                key=scenario+("_public_equipment" if public
                               else "_hidden_equipment")
                print("START virtual",game,key,flush=True)
                s=synthetic_study(game,scenario,public)
                data["simulated"][game][key]=s
                print("VIRTUAL",game,key,s["summary"]["draws"],{
                    name:[m["complete_box_wins"],
                          round(m["avg_prequential_joint_log_gain"],5)]
                    for name,m in s["summary"]["metrics"].items()},
                    flush=True)
    JSON_REPORT.parent.mkdir(parents=True,exist_ok=True)
    JSON_REPORT.write_text(json.dumps(data,indent=2)+"\n")
    REPORT.write_text(markdown(data)+"\n")
    print("SAVED",JSON_REPORT,REPORT,flush=True)


if __name__=="__main__":
    main()
