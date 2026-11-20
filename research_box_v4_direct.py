"""Direct formula audit: actual production v4 vs frozen production v3.

Identical three-ticket Box budgets and RNG streams. All formulas receive
only earlier drawings. The simulator's scenario and equipment identities
are never used to choose tickets. Real archive has previously been
inspected, so historical results are exploratory, not fresh confirmation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from datetime import datetime,timezone
from pathlib import Path

from research_virtual_draw_lab import simulate, SCENARIOS
from research_10k import load_official_history
from research.val_box_v3_frozen import generate_picks as v3_generate
from research.val_box_v3_frozen import forecast as v3_forecast
from research.val_box_v3_frozen import log_gain as v3_gain
from val_digit_formula_v2 import generate_picks as v4_generate
from val_digit_formula_v2 import log_gain as v4_gain
from val_box import random_box_picks
from val_box_challenger import grade_box, GAMES

VERSION="box_v4_direct_formula_challenge"
OUT=Path("reports/research_box_v4_direct.json")
MD=Path("reports/research_box_v4_direct.md")
TRAIN=850
VIRTUAL_ORIGINS=16
VIRTUAL_STEP=50
REAL_ORIGINS=70
REAL_STEP=18
MODELS=("v4","v3","random")


def seeded(*parts):
    data="|".join(map(str,(VERSION,)+parts)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(data).digest()[:8],"big"))


def evaluate(game, rows, indices, scenario):
    metrics={name:{"box_wins":0,"draws":0,"model_active":0,
                   "mean_log_gain_sum":0.,"fair_expected_box_wins":0.}
             for name in MODELS}
    from val_box import box_ways
    events=[]
    for k,i in enumerate(indices):
        target=rows[i]
        prior=rows[:i]
        token=(game,scenario,target["at"])
        a,metadata,ready=v4_generate(
            game,prior,target["stream"],3,seeded("matched",*token),True)
        b,metadata_v3,ready_v3=v3_generate(
            game,prior,target["stream"],3,seeded("matched",*token),True)
        fair=random_box_picks(game,3,seeded("independent",*token))
        selected={"v4":a,"v3":b,"random":fair}
        gain={"v4":v4_gain(ready,target["numbers"]),
              "v3":v3_gain(ready_v3,target["numbers"]),
              "random":0.}
        for name,picks in selected.items():
            m=metrics[name]
            m["box_wins"]+=grade_box(picks,target["numbers"])
            m["draws"]+=1
            m["fair_expected_box_wins"]+=sum(
                box_ways(p["numbers"]) / 10 ** int(game[-1])
                for p in picks)
            m["mean_log_gain_sum"]+=gain[name]
        metrics["v4"]["model_active"]+=int(metadata["signal_gate_passed"])
        metrics["v3"]["model_active"]+=int(metadata_v3["signal_gate_passed"])
        if not (metadata["signal_gate_passed"] or metadata_v3["signal_gate_passed"]):
            # Critical anti-luck control: if neither model sees signal, the
            # fair-null tickets must be EXACTLY identical, not just similar.
            if [p["numbers"] for p in a]!=[p["numbers"] for p in b]:
                raise AssertionError("Unjustified change in fair control tickets")
        events.append({
            "target":target["at"],"stream":target["stream"],
            "v4_active":metadata["signal_gate_passed"],
            "v4_experts":metadata["passed_experts"],
            "v3_active":metadata_v3["signal_gate_passed"],
            "v4_box_won":grade_box(a,target["numbers"]),
            "v3_box_won":grade_box(b,target["numbers"]),
            "random_box_won":grade_box(fair,target["numbers"]),
            "v4_log_gain":gain["v4"],
            "v3_log_gain":gain["v3"],
        })
        if (k+1)%20==0:
            print(scenario,game,k+1,"/",len(indices),flush=True)
    for name,m in metrics.items():
        m["mean_log_gain_vs_fair"]=m.pop("mean_log_gain_sum")/m["draws"]
    return {"game":game,"scenario":scenario,"targets":len(indices),
            "metrics":metrics,"events":events}


def run():
    result={"version":VERSION,"created_utc":datetime.now(timezone.utc).isoformat(),
            "all_complete_box":True,"real_archive_already_inspected":True,
            "no_live_wagers":True,"virtual":{},"real":{}}
    for game in GAMES:
        result["virtual"][game]={}
        for scenario in SCENARIOS:
            rows=simulate(game,scenario,TRAIN+VIRTUAL_ORIGINS*VIRTUAL_STEP,replicate=307)
            indices=list(range(TRAIN,len(rows),VIRTUAL_STEP))
            result["virtual"][game][scenario]=evaluate(
                game,rows,indices,scenario)
            m=result["virtual"][game][scenario]["metrics"]
            print("VIRTUAL",game,scenario,
                  {x:[m[x]["box_wins"],m[x]["model_active"],
                      round(m[x]["mean_log_gain_vs_fair"],5)]
                   for x in MODELS},flush=True)
        history=load_official_history(game)
        n=min(REAL_ORIGINS,(len(history)-1800)//REAL_STEP)
        indices=list(range(len(history)-n*REAL_STEP,len(history),REAL_STEP))
        result["real"][game]=evaluate(game,history,indices,"official_history")
        m=result["real"][game]["metrics"]
        print("REAL",game,{x:[m[x]["box_wins"],m[x]["model_active"],
                            round(m[x]["mean_log_gain_vs_fair"],5)]
                             for x in MODELS},flush=True)
    return result


def render(report):
    lines=[
        "# VAL actual prediction formula v4 vs frozen v3",
        "",
        "This tests the production number-generation functions on identical",
        "prior histories, fixed target draws, and the same three-ticket budget.",
        "If neither detects evidence, v3 and v4 use IDENTICAL random controls.",
        "Every credited winner is a complete Any Order multiset match.",
        "Results on artificial draws cannot establish a real lottery edge.",
        "Real archive results are retrospective and previously inspected.",
        "",
        "## Simulated machines",
        "",
        "| Game | Machine condition | Target draws | v4 Box | v3 Box | Random Box | v4 gated | v3 gated | v4 log gain | v3 log gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    ]
    for game, scenarios in report["virtual"].items():
        for scenario,x in scenarios.items():
            m=x["metrics"]
            lines.append(
                f'| {game} | {scenario} | {x["targets"]} | '
                f'{m["v4"]["box_wins"]} | {m["v3"]["box_wins"]} | '
                f'{m["random"]["box_wins"]} | {m["v4"]["model_active"]} | '
                f'{m["v3"]["model_active"]} | '
                f'{m["v4"]["mean_log_gain_vs_fair"]:+.5f} | '
                f'{m["v3"]["mean_log_gain_vs_fair"]:+.5f} |')
    lines.extend([
        "", "## Actual historical drawings (exploratory)", "",
        "| Game | Targets | v4 full Box | v3 full Box | Random full Box | v4 gated | v3 gated | v4 mean log gain | v3 mean log gain |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for game,x in report["real"].items():
        m=x["metrics"]
        lines.append(
            f'| {game} | {x["targets"]} | '
            f'{m["v4"]["box_wins"]} | {m["v3"]["box_wins"]} | '
            f'{m["random"]["box_wins"]} | {m["v4"]["model_active"]} | '
            f'{m["v3"]["model_active"]} | '
            f'{m["v4"]["mean_log_gain_vs_fair"]:+.5f} | '
            f'{m["v3"]["mean_log_gain_vs_fair"]:+.5f} |')
    lines.extend([
        "", "A newly activated signal is not proof of genuine winning ability.",
        "Live promotion requires correct probability calibration and",
        "future full-Box confirmation against independent fair controls.",
        "", "[Auditable target-level outcomes](research_box_v4_direct.json).", "",
    ])
    return "\n".join(lines)


def main():
    data=run()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,indent=2)+"\n")
    MD.write_text(render(data)+"\n")
    print("Saved",OUT,MD,flush=True)


if __name__=="__main__":
    main()
