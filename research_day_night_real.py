"""Chronological actual VA Day->Night conditional formula audit (exploratory).

Every Night ticket is selected AFTER its completed Day result, but BEFORE
that Night result is observed by the model. The official historical source
has been inspected before and is NOT a pristine forward holdout.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime,timezone
from pathlib import Path

from research_decades import fetch_full
from val_box_challenger import grade_box
from val_box import random_box_picks,box_ways
from val_day_night_formula import (
    NightConditionalEvidence,optimal_boxes,GAMES,VERSION,ANCHOR,
)
from val import ET

OUT=Path("reports/research_day_night_real.json")
MD=Path("reports/research_day_night_real.md")
EVAL_AFTER_PAIRS=250


def seeded(game,date,kind):
    key=f"{VERSION}|real|{game}|{date}|{kind}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest()[:8],"big"))


def evaluate(game,history):
    history=sorted(history,key=lambda r:(
        r["date"],0 if r["stream"]=="Day" else 1))
    bydate={}
    for row in history:
        if row["date"]<ANCHOR:
            continue
        bydate.setdefault(row["date"],{})[row["stream"]]=row
    pairs=[(day["Day"],day["Night"]) for _,day in sorted(bydate.items())
           if "Day" in day and "Night" in day]
    model=NightConditionalEvidence(game)
    width=int(game[-1])
    scores={"targets":0,"model_box_wins":0,"control_box_wins":0,
            "model_fair_expected":0.,"control_fair_expected":0.,
            "model_active":0,"presence_active":0,"tokens_active":0,
            "model_log_gain_vs_fair":0.,"pooled_log_gain":0.,
            "presence_raw_gain":0.,"tokens_raw_gain":0.}
    targets=[]
    for i,(day,night) in enumerate(pairs):
        x,y=day["numbers"],night["numbers"]
        expert,dist,diagnostics=model.predict(x)
        if i>=EVAL_AFTER_PAIRS:
            controls=random_box_picks(game,3,seeded(game,day["date"],"control"))
            picks=(optimal_boxes(game,dist,3) if expert else
                   random_box_picks(game,3,seeded(game,day["date"],"candidate")))
            raw=model.accumulator.distributions(x)
            pooled=model.accumulator.base()
            fair=width*math.log(.1)
            scores["targets"]+=1
            scores["model_active"]+=int(expert is not None)
            if expert:
                scores[expert+"_active"]+=1
            a=grade_box(picks,y)
            b=grade_box(controls,y)
            scores["model_box_wins"]+=a
            scores["control_box_wins"]+=b
            scores["model_fair_expected"]+=sum(
                box_ways(p["numbers"])/10**width for p in picks)
            scores["control_fair_expected"]+=sum(
                box_ways(p["numbers"])/10**width for p in controls)
            selected_gain=(sum(math.log(dist[d]) for d in y)-fair
                           if expert else 0.)
            scores["model_log_gain_vs_fair"]+=selected_gain
            scores["pooled_log_gain"]+=sum(math.log(pooled[d])
                                           for d in y)-fair
            scores["presence_raw_gain"]+=sum(
                math.log(raw["presence"][d]) for d in y)-fair
            scores["tokens_raw_gain"]+=sum(
                math.log(raw["tokens"][d]) for d in y)-fair
            targets.append(dict(
                date=day["date"],day=list(x),night=list(y),
                selected=expert,candidates=[p["numbers"] for p in picks],
                controls=[p["numbers"] for p in controls],
                candidate_box_win=a,random_box_win=b,
                log_gain=selected_gain))
        model.observe(x,y)
    n=scores["targets"]
    for key in ("model_log_gain_vs_fair","pooled_log_gain",
                "presence_raw_gain","tokens_raw_gain"):
        scores["mean_"+key]=scores[key]/n if n else 0.
    return dict(game=game,source_pairs=len(pairs),first_test=
                targets[0]["date"] if targets else None,
                last_test=targets[-1]["date"] if targets else None,
                metrics=scores,targets=targets)


def summary(data):
    lines=[
        "# Official historical Day-to-Night full Box formula audit",
        "",
        "This is a chronologically prequential analysis: all forecast inputs",
        "precede the target Night result. The full historical archive was",
        "previously inspected; it is NOT fresh or untouched validation.",
        "No machine IDs, drawing pretests or future Night results are features.",
        "",
        "| Game | Completed pairs | Test Nights | Conditional Box wins | Random Box wins | Active forecasts | Conditional mean log gain | Pooled baseline mean log gain |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for game,x in data["games"].items():
        m=x["metrics"]
        lines.append(
            f'| {game} | {x["source_pairs"]} | {m["targets"]} | '
            f'{m["model_box_wins"]} | {m["control_box_wins"]} | '
            f'{m["model_active"]} | '
            f'{m["mean_model_log_gain_vs_fair"]:+.6f} | '
            f'{m["mean_pooled_log_gain"]:+.6f} |')
    lines += [
        "",
        "A genuine predictive advantage requires better complete-Box",
        "performance and calibrated probabilities on newly frozen future",
        "draws, not merely favorable outcomes in this retrospective history.",
        "", "[Exact future-only target audit](research_day_night_real.json).", "",
    ]
    return "\n".join(lines)


def main():
    data={"version":VERSION,"created_utc":datetime.now(timezone.utc).isoformat(),
          "exploratory_previously_inspected_history":True,
          "train_complete_day_night_pairs":EVAL_AFTER_PAIRS,"games":{}}
    for game in GAMES:
        history,metadata=fetch_full(game)
        data["games"][game]=evaluate(game,history)
        m=data["games"][game]["metrics"]
        print("REAL",game,"nights",m["targets"],
              "box",m["model_box_wins"],m["control_box_wins"],
              "active",m["model_active"],
              "raw",round(m["mean_presence_raw_gain"],6),
              round(m["mean_tokens_raw_gain"],6),
              "pooled",round(m["mean_pooled_log_gain"],6),flush=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,indent=2)+"\n")
    MD.write_text(summary(data)+"\n")
    print("SAVED",OUT,MD,flush=True)


if __name__=="__main__":
    main()
