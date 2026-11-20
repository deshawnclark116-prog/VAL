"""Challenge a Day->Night CONDITIONAL prediction formula on full Box results.

Predeclared eight simulator mechanisms x three games, multiple independent
seeds. Every Night's three tickets selected before its result is revealed.
Hidden machine ID is never a feature. Offline oracle uses synthetic truth
only AFTER selection to estimate expected complete-Box wins. This is a
hypothesis test and cannot establish physical Virginia equipment behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from datetime import datetime,timezone
from pathlib import Path

from research_virtual_draw_lab import SCENARIOS, simulate, truth_distribution
from val_day_night_formula import (
    NightConditionalEvidence,optimal_boxes,GAMES, VERSION,
)
from val_box import distinct_permutations, random_box_picks, box_ways
from val_box_challenger import grade_box

TRAIN_PAIRS=650
TEST_PAIRS=750
REPLICATES=3
OUTPUT=Path("reports/research_day_night_conditional.json")
MARKDOWN=Path("reports/research_day_night_conditional.md")


def seeded(*parts):
    data="|".join(map(str,(VERSION,)+parts)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(data).digest()[:8],"big"))


def true_box_mass(game,scenario,night,progress,picks):
    """Unavailable to live predictor; offline synthetic expectation only."""
    width=int(game[-1])
    total=0.
    for pick in picks:
        for permutation in distinct_permutations(pick["numbers"]):
            q=1.
            for j,d in enumerate(permutation):
                dist=truth_distribution(scenario,width,"Night",
                                        night["machine"],progress,j,
                                        permutation[:j])
                q*=dist[d]
            total+=q
    return total


def evaluate(game,scenario,rep,train=TRAIN_PAIRS,test=TEST_PAIRS):
    n=train+test
    rows=simulate(game,scenario,2*n,rep+170)
    machine=NightConditionalEvidence(game)
    counts={"targets":0,"active":0,"candidate_wins":0,
            "fair_wins":0,"candidate_fair_expected":0.,
            "fair_fair_expected":0.,"candidate_true_expected":0.,
            "fair_true_expected":0.,"gated_log_gain":0.,
            "ungated_presence_gain":0.,"ungated_tokens_gain":0.,
            "pooled_gain":0.,"active_presence":0,"active_tokens":0}
    width=int(game[-1])
    for pair_idx in range(n):
        day=rows[2*pair_idx]
        night=rows[2*pair_idx+1]
        assert day["stream"]=="Day" and night["stream"]=="Night"
        d=day["numbers"]
        y=night["numbers"]
        selected,prob,diag=machine.predict(d)
        if pair_idx>=train:
            key=(game,scenario,rep,pair_idx)
            picks=(optimal_boxes(game,prob,3) if selected else
                   random_box_picks(game,3,seeded("candidate",*key)))
            controls=random_box_picks(game,3,seeded("control",*key))
            counts["targets"]+=1
            counts["active"]+=int(selected is not None)
            if selected:
                counts["active_"+selected]+=1
            counts["candidate_wins"]+=grade_box(picks,y)
            counts["fair_wins"]+=grade_box(controls,y)
            for field,portfolio in (
                ("candidate_fair_expected",picks),
                ("fair_fair_expected",controls)):
                counts[field]+=sum(box_ways(t["numbers"])/10**width
                                   for t in portfolio)
            # Simulated mechanism known only after candidate/control
            # selection; no model feature can access it.
            progress=(2*pair_idx+1)/len(rows)
            counts["candidate_true_expected"]+=true_box_mass(
                game,scenario,night,progress,picks)
            counts["fair_true_expected"]+=true_box_mass(
                game,scenario,night,progress,controls)
            raw=machine.accumulator.distributions(d)
            fair=width*math.log(.1)
            for name in ("presence","tokens"):
                counts["ungated_"+name+"_gain"]+=sum(
                    math.log(raw[name][t]) for t in y)-fair
            pooled=machine.accumulator.base()
            counts["pooled_gain"]+=sum(math.log(pooled[t]) for t in y)-fair
            if selected:
                counts["gated_log_gain"]+=sum(math.log(prob[t]) for t in y)-fair
        # Only NOW does the model observe this Night.
        machine.observe(d,y)
    return counts


def aggregate(items):
    keys=items[0]
    out={k:sum(x[k] for x in items) for k in keys}
    targets=out["targets"]
    for k in ("gated_log_gain","ungated_presence_gain",
              "ungated_tokens_gain","pooled_gain"):
        out["mean_"+k]=out[k]/targets
    out["active_fraction"]=out["active"]/targets
    out["candidate_box_rate"]=out["candidate_wins"]/targets
    out["fair_box_rate"]=out["fair_wins"]/targets
    out["expected_box_lift"]= (
        out["candidate_true_expected"]-out["fair_true_expected"])
    return out


def format_report(result):
    lines=[
        "# Day-to-Night conditional prediction formula — full Any Order audit",
        "",
        "Research-only mathematical challenger. The model learns statistical",
        "relationships between completed Day drawings and later Night results.",
        "It is NEVER supplied the simulator's hidden machine identity,",
        "private pretest outcomes, or the target's future Night result.",
        "",
        "Each target uses exactly three complete Box candidates and three",
        "independent random Box controls. A hit requires every digit,",
        "including multiplicity, in any order. The offline *true expected*",
        "Box wins use known synthetic probabilities strictly for evaluation.",
        "These experiments do NOT demonstrate how Virginia's actual drawing",
        "equipment operates or that historical lottery numbers are predictable.",
        "",
        "| Game | Artificial mechanism | Future Night draws | Candidate Box wins | Random Box wins | Candidate oracle expected | Random oracle expected | Signal-on draws | Gated mean Box log gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for game,cases in result["games"].items():
        for scenario,x in cases.items():
            lines.append(
                f'| {game} | {scenario} | {x["targets"]} | '
                f'{x["candidate_wins"]} | {x["fair_wins"]} | '
                f'{x["candidate_true_expected"]:.2f} | '
                f'{x["fair_true_expected"]:.2f} | '
                f'{x["active"]} | {x["mean_gated_log_gain"]:+.5f} |'
            )
    lines += [
        "",
        "## Promotion discipline",
        "",
        "The deployed VAL Box v4 generator remains unchanged by this challenge.",
        "A synthetic win is useful evidence about the challenger's ability",
        "to learn that hypothetical mechanism, NOT evidence of a Virginia",
        "Lottery weakness. Real-time adoption requires a clean, prospective",
        "improvement on actual future full Box outcomes and calibrated",
        "probabilities compared with an equal-cost control.",
        "", "[All results and paired counts](research_day_night_conditional.json).","",
    ]
    return "\n".join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replicates",type=int,default=REPLICATES)
    ap.add_argument("--train",type=int,default=TRAIN_PAIRS)
    ap.add_argument("--test",type=int,default=TEST_PAIRS)
    args=ap.parse_args()
    if not 1<=args.replicates<=20 or args.train<200 or args.test<10:
        raise ValueError("Invalid experiment size")
    result={"version":VERSION,"created_utc":datetime.now(timezone.utc).isoformat(),
            "train_completed_pairs":args.train,"future_night_pairs":args.test,
            "replicates":args.replicates,"synthetic_only":True,
            "deployment_unchanged":True,"games":{}}
    for game in GAMES:
        result["games"][game]={}
        for scenario in SCENARIOS:
            observations=[]
            for rep in range(args.replicates):
                observations.append(evaluate(
                    game,scenario,rep,args.train,args.test))
            summary=aggregate(observations)
            result["games"][game][scenario]=summary
            print("RESULT",game,scenario,
                  "box",summary["candidate_wins"],summary["fair_wins"],
                  "true",round(summary["candidate_true_expected"],3),
                  round(summary["fair_true_expected"],3),
                  "active",summary["active"],
                  "log",round(summary["mean_gated_log_gain"],5),flush=True)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
    MARKDOWN.write_text(format_report(result)+"\n")
    print("SAVED",OUTPUT,MARKDOWN,flush=True)


if __name__=="__main__":
    main()
