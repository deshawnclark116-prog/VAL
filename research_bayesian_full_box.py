"""Structural full-Box models vs pooled-digit and fair controls.

Every candidate is forecast on an earlier-only information set. Complete
Any Order multiset wins are the primary metric (never partial digit hits).
Real 2025/26 histories were previously inspected and are EXPLORATORY.
Synthetic mechanisms are explicit invented examples, not actual VA devices.
This script cannot promote a model to production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

from val_bayesian_full_box import BayesianBox,GAMES,METHODS,VERSION
from val_box import box_ways,digits_key,random_box_picks
from research_decades import fetch_full
from research_virtual_draw_lab import simulate

OUT=Path("reports/research_bayesian_full_box.json")
MD=Path("reports/research_bayesian_full_box.md")
REAL_PERIODS=("2025","2026")
VIRTUAL_SCENARIOS=("fair_independent","within_draw_echo","favored_exact_box")
VIRTUAL_SEEDS=(81,82)
VIRTUAL_TRAIN=1000
VIRTUAL_TEST=700
N_TICKETS=3


def stable_rng(*parts):
    raw="|".join(map(str,(VERSION,)+parts)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8],"big"))


def portfolio_probability(game,picks):
    unique={digits_key(p) for p in picks}
    return sum(box_ways(c) for c in unique)/10**int(game[-1])


def outcome(game,model,actual,random_control):
    winner=digits_key(actual["numbers"])
    fair=model["fair"]["distribution"][winner]
    if fair<=0:
        raise AssertionError("Fair outcome had zero mass")
    results={}
    for name in METHODS+("random",):
        if name=="random":
            picks=[p["numbers"] for p in random_control]
            log_gain=0.
        else:
            picks=model[name]["picks"]
            p=model[name]["distribution"][winner]
            log_gain=math.log(p/fair)
        results[name]=dict(
            win=int(winner in {digits_key(x) for x in picks}),
            coverage=portfolio_probability(game,picks),
            log_gain=log_gain,
            tickets=picks)
    return results


def summarize(game,events):
    report={}
    periods=("2025","2026","combined") if events and (
        events[0]["scenario"]=="official") else ("combined",)
    for period in periods:
        records=[r for r in events if period=="combined" or
                 r["period"]==period]
        if not records:
            continue
        score={}
        for method in METHODS+("random",):
            wins=sum(r["methods"][method]["win"] for r in records)
            chance=sum(r["methods"][method]["coverage"] for r in records)
            gain=sum(r["methods"][method]["log_gain"] for r in records)
            score[method]=dict(
                complete_box_wins=wins,
                fair_expected_box_wins=chance,
                full_box_rate=wins/len(records),
                mean_joint_log_gain=gain/len(records),
                fair_coverage_per_target=chance/len(records),
            )
        paired={}
        days=defaultdict(int)
        for r in records:
            for candidate in ("pooled","exact_bag","pair_shape"):
                days[(candidate,r["date"])]+=(r["methods"][candidate]["win"]-
                                               r["methods"]["random"]["win"])
        rng=stable_rng(game,period,"bootstrap")
        for candidate in ("pooled","exact_bag","pair_shape"):
            blocks=[score_ for (name,date),score_ in days.items()
                    if name==candidate]
            sims=sorted(sum(blocks[rng.randrange(len(blocks))]
                            for _ in blocks) for _ in range(1200))
            paired[candidate]=dict(
                wins_minus_random=(score[candidate]["complete_box_wins"]-
                                   score["random"]["complete_box_wins"]),
                paired_day_bootstrap_95pct_hit_difference=[
                    sims[30],sims[1170]])
        report[period]=dict(target_draws=len(records),metrics=score,
                            paired_uncertainty=paired)
    return report


def evaluate(game,rows,target_indices,scenario):
    machine=BayesianBox(game)
    interesting=set(target_indices)
    events=[]
    for idx,row in enumerate(rows):
        if idx in interesting:
            prediction=machine.predict(N_TICKETS)
            rng=stable_rng(game,scenario,row["at"],"control")
            control=random_box_picks(game,N_TICKETS,rng)
            scored=outcome(game,prediction,row,control)
            local_day=row.get("date") or datetime.fromisoformat(
                row["at"]).date().isoformat()
            events.append(dict(date=local_day,
                               stream=row["stream"],
                               target=row["at"],
                               period=local_day[:4],
                               scenario=scenario,
                               actual=list(row["numbers"]),
                               methods=scored))
            if len(events)%300==0:
                print("PROGRESS",game,scenario,len(events),
                      "/",len(target_indices),flush=True)
        # Never train on the drawing before its forecast is frozen.
        machine.observe(row)
    if len(events)!=len(interesting):
        raise AssertionError("Some target indices were not scored")
    return dict(targets=len(events),metrics=summarize(game,events),
                events=events)


def simulated(game,scenario,n,seed):
    if scenario!="favored_exact_box":
        return simulate(game,scenario,n,seed)
    rows=simulate(game,"fair_independent",n,seed)
    rng=stable_rng(game,"favored_exact_box",seed)
    favored=[0,2,5,7,9][:int(game[-1])]
    for row in rows:
        if rng.random()<.05:
            ticket=favored[:]
            rng.shuffle(ticket)
            row["numbers"]=ticket
        # The original simulator pretests/machine labels are deliberately
        # NOT made available to the Bayesian model.
    return rows


def render(report):
    lines=[
        "# VAL new Bayesian full Box formula vs previous pooled model",
        "",
        "**REAL TESTS: actual Virginia Lottery outcomes in 2025/2026.**",
        "Every target is scored chronologically with earlier drawings only.",
        "These years have been inspected during previous VAL experiments;",
        "therefore no positive retrospective result is independent proof.",
        "",
        "All methods choose three distinct complete digit MULTISETS,",
        "excluding all-identical Straight-only outcomes. Every hit must",
        "match the entire multiset including repeated digits. Joint log",
        "gain uses the target's full unordered Box probability, not the",
        "accuracy of individual positions.",
        "",
        "Exact bag: Dirichlet-smoothed empirical frequencies of each",
        "whole multiset. Pair shape: normalized probability adjustment",
        "using co-occurrence of *pairs* of digits (including duplicates).",
        "The pooled model and fair random baseline receive the same",
        "three-ticket budget.",
        "",
        "## Actual real drawings",
        "",
        "| Game | Period | Targets | Exact bag Box | Pair-shape Box | Pooled v2 Box | Random Box | Bag vs random 95% paired CI | Pair vs random 95% paired CI |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for game,section in report["real"].items():
        for period,data in section["metrics"].items():
            m=data["metrics"]
            u=data["paired_uncertainty"]
            lines.append(
                f'| {game} | {period} | {data["target_draws"]} | '
                f'{m["exact_bag"]["complete_box_wins"]} | '
                f'{m["pair_shape"]["complete_box_wins"]} | '
                f'{m["pooled"]["complete_box_wins"]} | '
                f'{m["random"]["complete_box_wins"]} | '
                f'{u["exact_bag"]["paired_day_bootstrap_95pct_hit_difference"]} | '
                f'{u["pair_shape"]["paired_day_bootstrap_95pct_hit_difference"]} |')
    lines.extend([
        "",
        "## Real full Box joint probability score",
        "",
        "| Game | Exact bag log gain | Pair shape log gain | Pooled log gain |",
        "| --- | ---: | ---: | ---: |",
    ])
    for game,section in report["real"].items():
        m=section["metrics"]["combined"]["metrics"]
        lines.append(
            f'| {game} | {m["exact_bag"]["mean_joint_log_gain"]:+.6f} | '
            f'{m["pair_shape"]["mean_joint_log_gain"]:+.6f} | '
            f'{m["pooled"]["mean_joint_log_gain"]:+.6f} |')
    lines.extend([
        "",
        "## Artificial-machine sanity tests",
        "",
        "| Game | Hypothetical mechanism | Targets | Exact bag | Pair shape | Pooled | Fair random | Bag log gain | Pair log gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for game,scenarios in report["virtual"].items():
        for scenario,part in scenarios.items():
            m=part["metrics"]["combined"]["metrics"]
            lines.append(
                f'| {game} | {scenario} | {part["targets"]} | '
                f'{m["exact_bag"]["complete_box_wins"]} | '
                f'{m["pair_shape"]["complete_box_wins"]} | '
                f'{m["pooled"]["complete_box_wins"]} | '
                f'{m["random"]["complete_box_wins"]} | '
                f'{m["exact_bag"]["mean_joint_log_gain"]:+.5f} | '
                f'{m["pair_shape"]["mean_joint_log_gain"]:+.5f} |')
    lines += [
        "",
        "## Promotion decision",
        "",
        "Do not replace the live VAL model merely because the challenger",
        "detects a pattern artificially injected into fake drawings.",
        "Look for positive, repeatable and uncertainty-adjusted complete",
        "Box performance AND proper probability-score improvement on",
        "future real draws that were unknown when models were chosen.",
        "",
        "The source used no official ball-set or machine IDs; there",
        "is no basis here to assume the real draws match the simulator.",
        "",
        "[Exact target-level picks, outcomes and metrics]",
        "(research_bayesian_full_box.json).",
        "",
    ]
    return "\n".join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("real","virtual","both"),default="both")
    args=ap.parse_args()
    result=dict(version=VERSION,generated_utc=datetime.now(timezone.utc).isoformat(),
                box_only=True,real_previously_inspected=True,
                research_only=True,real={},virtual={})
    if args.mode in ("real","both"):
        for game in GAMES:
            source,metadata=fetch_full(game)
            source=sorted(source,key=lambda r:(
                r["date"],0 if r["stream"]=="Day" else 1))
            targets=[i for i,r in enumerate(source)
                     if r["date"][:4] in REAL_PERIODS and i>=500]
            print("REAL START",game,len(source),len(targets),flush=True)
            result["real"][game]=evaluate(game,source,targets,"official")
            scores=result["real"][game]["metrics"]["combined"]["metrics"]
            print("REAL DONE",game,len(targets),
                  {x:[scores[x]["complete_box_wins"],
                      round(scores[x]["mean_joint_log_gain"],5)]
                   for x in METHODS+("random",)},flush=True)
    if args.mode in ("virtual","both"):
        for game in GAMES:
            result["virtual"][game]={}
            for scenario in VIRTUAL_SCENARIOS:
                all_events=[]
                for seed in VIRTUAL_SEEDS:
                    n=VIRTUAL_TRAIN+VIRTUAL_TEST
                    rows=simulated(game,scenario,n,seed)
                    part=evaluate(game,rows,list(range(VIRTUAL_TRAIN,n)),
                                  scenario)
                    all_events.extend(part["events"])
                result["virtual"][game][scenario]=dict(
                    targets=len(all_events),
                    metrics=summarize(game,all_events),
                    events=all_events)
                score=result["virtual"][game][scenario][
                    "metrics"]["combined"]["metrics"]
                print("VIRTUAL DONE",game,scenario,
                      {x:[score[x]["complete_box_wins"],
                          round(score[x]["mean_joint_log_gain"],5)]
                       for x in METHODS+("random",)},flush=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    MD.write_text(render(result)+"\n")
    print("SAVED",OUT,MD,flush=True)


if __name__=="__main__":
    main()
