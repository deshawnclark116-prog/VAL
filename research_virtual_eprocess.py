"""Evidence-accumulating v3 challenger for VAL's virtual drawing laboratory.

A real change to candidate FORMULA selection: accumulate out-of-sample,
prequential likelihood-ratio evidence for three adaptive predictors, then
select one only when there is statistically meaningful historical evidence.

One-step next-draw predictive distributions P_t are constructed BEFORE
revealing draw X_t. Under the precommitted iid-fair null, each model's
E_t=product(P_i(X_i)/0.1**width) is a nonnegative martingale even when
the P_i were fitted adaptively to previous drawings. A threshold of
3*3/.05 controls a conceptual three-expert/three-game false-discovery
bound under the fair-null assumptions. This is a research simulation
that does NOT establish any signal in the real Virginia Lottery.

We explicitly compare to v2's short-window expert-significance gate and
do not promote the new challenger to production from synthetic data.
"""
from __future__ import annotations
import json
import math
from datetime import datetime,timezone
from pathlib import Path

from research_virtual_draw_lab import (GAMES_TEST,SCENARIOS,RollingCounts,
                                       simulate,_metric,score,finalize)

VERSION="val_virtual_eprocess_challenger_v1"
START_EVIDENCE=200
TRAIN_DRAWS=850
TEST_DRAWS=650
REPLICATES=8
EXPERTS=("pooled","position","day_night")
LOG_GATE=math.log(len(EXPERTS)*len(GAMES_TEST)/.05)
OUT=Path("reports/research_virtual_eprocess.json")
DOC=Path("reports/research_virtual_eprocess.md")


def evaluate(game,scenario,replicates=REPLICATES,train=TRAIN_DRAWS,test=TEST_DRAWS):
    aggregate={name:_metric() for name in
               ("fair","eprocess_challenger","pooled","position","day_night","oracle")}
    activations={name:0 for name in EXPERTS}
    experiments=[]
    for rep in range(replicates):
        rows=simulate(game,scenario,train+test,rep)
        rolling=RollingCounts(int(game[-1]))
        logs={name:0. for name in EXPERTS}
        first_activated=None
        active_targets=0
        for i,row in enumerate(rows):
            forecasts=rolling.models(row["stream"],row["machine"])
            # Decision is made before X_i is observed. No knowledge of machine
            # ID or current pretests is used by these three candidate experts.
            eligible=[name for name in EXPERTS if logs[name]>LOG_GATE]
            selected=max(eligible,key=lambda name:logs[name]) if eligible else None
            if i>=train:
                for name in ("fair",)+EXPERTS:
                    score(aggregate[name],forecasts[name],row["numbers"])
                score(aggregate["oracle"],row["truth_probs"],row["numbers"])
                model_name=selected if selected else "fair"
                score(aggregate["eprocess_challenger"],forecasts[model_name],
                      row["numbers"])
                if selected:
                    active_targets+=1
                    activations[selected]+=1
                    if first_activated is None:first_activated=i
            if i>=START_EVIDENCE:
                for name in EXPERTS:
                    # Multiply probability of actually drawn complete
                    # ordered number across all known positions.
                    log_gain=sum(math.log(forecasts[name][j][d]/.1)
                                 for j,d in enumerate(row["numbers"]))
                    logs[name]+=log_gain
            rolling.add(row)
        experiments.append({"replicate":rep,"active_test_draws":active_targets,
                            "first_test_activation_index":first_activated,
                            "final_log_e_by_expert":logs})
    return {
        "game":game,"scenario":scenario,
        "replicates":replicates,"training_draws":train,"test_draws":test,
        "test_active_draws":sum(x["active_test_draws"] for x in experiments),
        "replicates_with_evidence":sum(x["active_test_draws"]>0 for x in experiments),
        "activate_by_expert":activations,
        "models":{name:finalize(m) for name,m in aggregate.items()},
        "repetitions":experiments,
        "unverified_real_mechanism":True,
        "prospective_on_real_draws_required":True,
    }


def markdown(r):
    lines=["# VAL virtual drawing lab — cumulative-evidence formula challenger",
        "",
        "Tests a real algorithmic alternative to the deployed v2 gate.",
        "Three *predictive probability formulas* are evaluated before each",
        "virtual draw; their probabilities on actual future outcomes",
        "accumulate likelihood-ratio evidence. A formula becomes active",
        "only when accumulated evidence crosses a fixed, conservative",
        "multiple-model threshold. On fair, independent draws this",
        "procedure is designed not to invent persistent edges.",
        "",
        "**These are artificial drawings with known injected patterns,",
        "not historical Virginia Lottery outcomes.** Real-world",
        "predictive advantage has not been established.",
        "",
        "| Game | Synthetic scenario | Trials with signal | Signal-active test draws | New challenger top-1 | Fair top-1 | New log gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for game,cases in r["games"].items():
        for scenario,x in cases.items():
            a=x["models"]["eprocess_challenger"]
            b=x["models"]["fair"]
            lines.append("| "+game+" | "+scenario+" | "+
                str(x["replicates_with_evidence"])+"/"+str(x["replicates"])+
                " | "+str(x["test_active_draws"])+"/"+
                str(x["replicates"]*x["test_draws"])+
                " | "+f'{100*a["top1_rate"]:.2f}%'+
                " | "+f'{100*b["top1_rate"]:.2f}%'+
                " | "+f'{a["mean_log_gain_vs_uniform"]:+.5f}'+" |")
    lines+=["","## Interpretation","",
            "Strong injected biases should be recoverable; weak effects",
            "require much larger sample sizes. In the hidden-opposing",
            "machine scenario, the unconditional digit distribution is",
            "exactly uniform, making that mechanism unexploitable without",
            "pre-wager information about the machine. The simulator's",
            "perfect-information oracle is not a deployable model.",
            "",
            "Any effect found in this controlled simulation must be retested",
            "on fresh, real drawing outcomes before claiming accuracy gains.",
            "",
            "[Raw results](research_virtual_eprocess.json).",""]
    return "\n".join(lines)

def main():
    data={"version":VERSION,"created_utc":datetime.now(timezone.utc).isoformat(),
          "log_e_gate":LOG_GATE,"candidates":EXPERTS,"test_replicates":REPLICATES,
          "no_live_model_promotion":True,"games":{}}
    for game in GAMES_TEST:
        data["games"][game]={}
        for scenario in SCENARIOS:
            x=evaluate(game,scenario)
            data["games"][game][scenario]=x
            print(json.dumps({
                "game":game,"scenario":scenario,
                "activated_trials":x["replicates_with_evidence"],
                "activated_draws":x["test_active_draws"],
                "new_top1":x["models"]["eprocess_challenger"]["top1_rate"],
                "new_log_gain":x["models"]["eprocess_challenger"]["mean_log_gain_vs_uniform"]
            }),flush=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,indent=2)+"\n")
    DOC.write_text(markdown(data)+"\n")

if __name__=="__main__":main()
