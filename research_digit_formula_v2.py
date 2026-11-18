"""Historical head-to-head for the actual proposed digit prediction formula.

For each fixed chronological test origin, generate three tickets from the
new conditional formula, three old-ensemble picks, and three fair controls.
Evaluate EXACT hits, exact-position digits, and fair-relative log score on
the same subsequent official draw. No later outcome can enter any formula.
Not an untouched future holdout; do not claim lottery advantage.
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

from research_10k import load_official_history
from val import generate,score_batch,model_selection_weights
from val_digit_formula_v2 import (VERSION,forecast,generate_picks,joint_probability,
                                  log_gain,stable_rng)
from val import GAMES

OUTPUT=Path("reports/research_digit_formula_v2.json")
MARKDOWN=Path("reports/research_digit_formula_v2.md")
GAMES_TEST=("pick3","pick4","pick5")
STEP=6
MAX_TARGETS=220
MIN_TRAIN=1800


def old_joint_likelihood(game,previous,actual):
    width=GAMES[game]["size"]
    p=1.
    for i in range(width):
        weights=model_selection_weights(game,previous,"ensemble",position=i)
        p*=weights[actual[i]]
    return p


def seeded(old,new,game,target):
    return stable_rng(game,old,new,target["at"])


def evaluate(game,rows,step=STEP,max_targets=MAX_TARGETS):
    width=GAMES[game]["size"]
    end=len(rows)
    # Same fixed last-range, every Nth actual drawing. The chronological
    # prequential calculations still only see results BEFORE each target.
    available=max(0,end-MIN_TRAIN)
    n=min(max_targets,available//step)
    if n<20:raise ValueError("Not enough eligible held-out observations")
    indices=list(range(end-n*step,end,step))
    if len(indices)!=n:raise AssertionError("Range changed")
    output={name:{"digits":0,"exact":0,"tickets":0,"log_gains":[]}
            for name in ("new_v2","original_ensemble","uniform_control")}
    signal_count=0
    experts=defaultdict(int)
    chronological=[]
    for k,i in enumerate(indices):
        target=rows[i]
        previous=rows[:i]
        # Calling the production generator itself, not reconstructing picks
        # from approximate research-only probability code.
        current,meta,ready=generate_picks(game,previous,target["stream"],3,
                                    rng=seeded("nextgen","uniform",game,target),
                                    return_forecast=True)
        if meta["signal_gate_passed"]!=ready["gate_passed"]:
            raise AssertionError("Production/research gate mismatch")
        original=generate(game,previous[-500:],"ensemble",3,
                          seeded("original","draws",game,target))
        fair=generate(game,[],"random",3,
                      seeded("independent","control",game,target))
        candidate_sets={"new_v2":current,"original_ensemble":original,
                        "uniform_control":fair}
        log_probs={
            "new_v2":log_gain(ready,target["numbers"]),
            "original_ensemble":math.log(old_joint_likelihood(
                game,previous,target["numbers"]))+width*math.log(10),
            "uniform_control":0.
        }
        signal_count+=int(meta["signal_gate_passed"])
        for name in meta["passed_experts"]:experts[name]+=1
        event={"at":target["at"],"stream":target["stream"],
               "signal_gate_passed":meta["signal_gate_passed"],
               "passed_experts":meta["passed_experts"]}
        for name,picks in candidate_sets.items():
            grade=score_batch(game,picks,target)
            record=output[name]
            record["digits"]+=grade["total_matches"]
            record["exact"]+=grade["exact"]
            record["tickets"]+=grade["tickets"]
            record["log_gains"].append((target["at"],log_probs[name]))
            event[name]={
                "tickets":["".join(map(str,x["numbers"])) for x in picks],
                "position_matches":grade["total_matches"],
                "exact":grade["exact"],
                "log_gain":log_probs[name]
            }
        chronological.append(event)
        if (k+1)%50==0:
            print(game+" head-to-head "+str(k+1)+"/"+str(n),flush=True)
    out={}
    for method,record in output.items():
        gains=record["log_gains"]
        v=[score for _,score in gains]
        out[method]={
            "tickets":record["tickets"],
            "exact":record["exact"],
            "position_matches":record["digits"],
            "position_hit_rate":record["digits"]/(record["tickets"]*width),
            "mean_log_gain_vs_fair":sum(v)/n,
            "first_half_mean_log_gain":sum(v[:n//2])/(n//2),
            "second_half_mean_log_gain":sum(v[n//2:])/(n-n//2)
        }
    pair=[event["new_v2"]["log_gain"]-
          event["original_ensemble"]["log_gain"] for event in chronological]
    # Day-cluster differences: single-day baselines can share outcome effects.
    grouped=defaultdict(list)
    for event,diff in zip(chronological,pair):
        grouped[event["at"][:10]].append(diff)
    clusters=[sum(vals)/len(vals) for vals in grouped.values()]
    delta=sum(clusters)/len(clusters)
    if len(clusters)>1:
        variance=sum((x-delta)**2 for x in clusters)/(len(clusters)-1)
        err=(variance/len(clusters))**.5
    else:err=float("inf")
    return {
        "game":game,"source_draws":len(rows),
        "draws_evaluated":n,"first_target":rows[indices[0]]["at"],
        "last_target":rows[indices[-1]]["at"],
        "chronological_stride":step,
        "signal_gate_active_targets":signal_count,
        "passed_expert_counts":dict(experts),
        "comparison":out,
        "new_v2_vs_original_log_gain_delta":delta,
        "new_v2_vs_original_log_gain_ci95":[delta-1.96*err,delta+1.96*err],
        "test_targets":chronological,
    }


def render(data):
    lines=[
        "# VAL v2 — actual formula vs original ensemble",
        "",
        "Precommitted challenger: **"+VERSION+"**.",
        "Direct live-generator replay on real subsequent drawing outcomes.",
        "Each candidate uses strictly earlier history. This is exploratory",
        "because the historical period has been previously inspected.",
        "All groups have three tickets per target. Exact = full Straight match.",
        "Position matches are diagnostics; a single position match on its own",
        "does NOT constitute a prize.",
        "",
        "| Game | Test draws | v2 matched positions | Old ensemble | Uniform controls | v2 exact | Old exact | Uniform exact |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    ]
    for game,g in data["games"].items():
        comp=g["comparison"]
        a,b,c=(comp[x] for x in ("new_v2","original_ensemble","uniform_control"))
        lines.append("| "+game+" | "+str(g["draws_evaluated"])+" | "+
                     format(a["position_hit_rate"]*100,".2f")+"% | "+
                     format(b["position_hit_rate"]*100,".2f")+"% | "+
                     format(c["position_hit_rate"]*100,".2f")+"% | "+
                     str(a["exact"])+" | "+str(b["exact"])+" | "+str(c["exact"])+" |")
    for game,g in data["games"].items():
        comp=g["comparison"]
        lines += [
            "",
            "## "+game.upper(),
            "",
            "Official history draws: "+format(g["source_draws"],",")+
              "; evaluated "+str(g["draws_evaluated"])+" independent target origins.",
            "Test dates: "+g["first_target"]+" through "+g["last_target"]+".",
            "Conditionally active signal gates: "+
              str(g["signal_gate_active_targets"])+"/"+str(g["draws_evaluated"])+".",
            "Active expert counts: "+json.dumps(g["passed_expert_counts"])+".",
            "",
            "| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |",
            "| --- | ---: | ---: | ---: |"
        ]
        for key in ("new_v2","original_ensemble","uniform_control"):
            r=comp[key]
            lines.append("| "+key+" | "+format(r["mean_log_gain_vs_fair"],"+.6f")+
                         " | "+format(r["first_half_mean_log_gain"],"+.6f")+
                         " | "+format(r["second_half_mean_log_gain"],"+.6f")+" |")
        lines += [
            "",
            "v2 minus old ensemble: "+format(g["new_v2_vs_original_log_gain_delta"],"+.6f")+
            " log units per drawing; day-cluster 95% interval: ["+
              format(g["new_v2_vs_original_log_gain_ci95"][0],"+.6f")+", "+
              format(g["new_v2_vs_original_log_gain_ci95"][1],"+.6f")+"].",
            "",
        ]
    lines += [
        "## Interpretation and promotion rule",
        "",
        "The v2 formula is a genuine conditional joint model. It only exposes",
        "a nonuniform advantage if a model passes the past-only statistical gate.",
        "Otherwise it uses fair 10%-per-position distributions and diverse",
        "independent random candidates. It is designed to reduce overconfidence,",
        "not to fake a winning edge. A lower log loss can be a valid improvement",
        "in forecasting honesty even when hit rates remain indistinguishable.",
        "",
        "Only strictly future, immutable paper predictions can validate a",
        "claim of a new predictive edge. No model is promoted merely by",
        "retrospectively finding a lucky ticket.",
        "",
        "Machine readable target-level comparison:",
        "[research_digit_formula_v2.json](research_digit_formula_v2.json).",
        ""
    ]
    return "\n".join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-targets",type=int,default=MAX_TARGETS)
    parser.add_argument("--step",type=int,default=STEP)
    args=parser.parse_args()
    data={"version":"val_digit_formula_challenge_v2",
          "generated_at":datetime.now(timezone.utc).isoformat(),
          "test_specs":{"step":args.step,"max_targets":args.max_targets,
              "min_training_draws":MIN_TRAIN,
              "primary_metric":"mean prequential log probability vs fair"},
          "historical_holdout_not_pristine":True,"games":{}}
    for game in GAMES_TEST:
        hist=load_official_history(game)
        data["games"][game]=evaluate(game,hist,args.step,args.max_targets)
        x=data["games"][game]
        print(json.dumps({"game":game,"targets":x["draws_evaluated"],
            "signal_gates":x["signal_gate_active_targets"],
            "v2_log_gain":x["comparison"]["new_v2"]["mean_log_gain_vs_fair"],
            "legacy_log_gain":x["comparison"]["original_ensemble"]["mean_log_gain_vs_fair"],
            "v2_match_rate":x["comparison"]["new_v2"]["position_hit_rate"],
            "legacy_match_rate":x["comparison"]["original_ensemble"]["position_hit_rate"]
            }),flush=True)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(data,indent=2)+"\n")
    MARKDOWN.write_text(render(data)+"\n")
    print("Saved",OUTPUT,MARKDOWN,flush=True)

if __name__=="__main__":main()
