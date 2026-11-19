"""VAL virtual-draw lab: fair, biased, switched-equipment and dependent draws.

This is NOT a claim to reproduce Virginia's undisclosed machinery or RNG.
The Virginia Lottery describes random equipment selection and pretesting for
its televised drawing security, but those descriptions do not establish the
exact apparatus of each Pick 3/4/5 drawing or pre-bet availability of machine
IDs/pretests. This lab uses explicitly hypothetical digit-generating devices.

The lab asks whether prediction systems:
  1. stay near chance and do NOT claim an edge when the draw is fair,
  2. recover a persistent small or strong injected bias,
  3. handle day-only biases and changes in apparatus mid-experiment,
  4. understand that hidden equipment cannot be inferred per draw,
  5. distinguish within-ticket correlation from marginal digit bias.

All test seeds are fixed in source; simulated outcomes are generated
independently of predictor output. No live model promotion follows
from doing well on a simulator with invented biases.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import deque
from datetime import datetime,timedelta,timezone
from pathlib import Path

from val import ET,GAMES
from val_digit_formula_v2 import forecast as forecast_v2,joint_probability

SEED=20261118
SCENARIOS=(
    "fair_independent",
    "fixed_position_small",
    "fixed_position_strong",
    "pooled_device_bias",
    "day_only_bias",
    "halfway_replacement",
    "hidden_opposing_machines",
    "within_draw_echo",
)
GAMES_TEST=("pick3","pick4","pick5")
TRIALS=8
TRAIN_DRAWS=850
TEST_DRAWS=650
V2_PROBE_TARGETS=12
OUTPUT=Path("reports/research_virtual_draw_lab.json")
MD_OUT=Path("reports/research_virtual_draw_lab.md")


def seeded_rng(*parts):
    raw="|".join(map(str,(SEED,)+parts)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8],"big"))


def normalize(weights):
    if len(weights)!=10 or any(x<0 for x in weights) or sum(weights)<=0:
        raise ValueError("Invalid virtual device weights")
    total=sum(weights)
    return [v/total for v in weights]


def choose(rng,weights):
    x=rng.random()
    for digit,p in enumerate(weights):
        x-=p
        if x<0:return digit
    return 9


def truth_distribution(scenario,width,stream,machine,offset,position,prefix):
    """Known synthetic physical conditions. The predictors never get these."""
    p=[.1]*10
    if scenario=="fixed_position_small" and position==0:
        p[7]=.125
        p=[v if j==7 else .875/9 for j,v in enumerate(p)]
    elif scenario=="fixed_position_strong" and position==0:
        p[7]=.22
        p=[v if j==7 else .78/9 for j,v in enumerate(p)]
    elif scenario=="pooled_device_bias":
        p[7]=.145
        p=[v if j==7 else .855/9 for j,v in enumerate(p)]
    elif scenario=="day_only_bias" and stream=="Day":
        p[7]=.17
        p=[v if j==7 else .83/9 for j,v in enumerate(p)]
    elif scenario=="halfway_replacement":
        favorite=7 if offset<.5 else 2
        p[favorite]=.18
        p=[v if j==favorite else .82/9 for j,v in enumerate(p)]
    elif scenario=="hidden_opposing_machines":
        # Mixture over machine ID gives *exactly* uniform probabilities:
        # P(7 | machine A)=.17, P(7 | machine B)=.03.
        # Drawn machine is randomly selected and NOT supplied pre-wager.
        p[7]=.17 if machine==0 else .03
        p=[v if j==7 else (1-p[7])/9 for j,v in enumerate(p)]
    elif scenario=="within_draw_echo" and position>0:
        p=[.07]*10
        p[prefix[-1]]+=.30
    return normalize(p)


def simulate(game,scenario,n,replicate):
    if game not in GAMES_TEST or scenario not in SCENARIOS:raise ValueError("Invalid experiment")
    width=GAMES[game]["size"]
    rng=seeded_rng(game,scenario,replicate)
    start=datetime(2026,1,1,tzinfo=ET)
    rows=[]
    for index in range(n):
        day=index//2
        stream="Day" if index%2==0 else "Night"
        # One randomly selected device for each calendar day.
        # This value is hidden by default, even though simulation knows it.
        if index%2==0:
            machine=rng.randrange(2)
        dt=(start+timedelta(days=day)).replace(
            hour=13 if stream=="Day" else 23,minute=59 if stream=="Day" else 0)
        progress=index/n
        drawn=[]
        oracle=[]
        for j in range(width):
            dist=truth_distribution(scenario,width,stream,machine,progress,j,drawn)
            oracle.append(dist)
            drawn.append(choose(rng,dist))
        pretests=[]
        for trial in range(2):
            trial_numbers=[]
            for j in range(width):
                dist=truth_distribution(scenario,width,stream,machine,progress,j,trial_numbers)
                trial_numbers.append(choose(rng,dist))
            pretests.append(trial_numbers)
        rows.append({
            "game":game,"at":dt.astimezone(timezone.utc).isoformat(),
            "stream":stream,"numbers":drawn,"machine":machine,
            "pretests":pretests,"truth_probs":oracle
        })
    return rows


class RollingCounts:
    def __init__(self,width,window=600):
        self.width=width
        self.window=window
        self.queue=deque()
        self.positions=[[0]*10 for _ in range(width)]
        self.pooled=[0]*10
        self.by_stream={s:[[0]*10 for _ in range(width)] for s in ("Day","Night")}
        self.by_machine={m:[[0]*10 for _ in range(width)] for m in (0,1)}
        self.machine_sizes={0:0,1:0}

    def add(self,row):
        self.queue.append(row)
        self._apply(row,1)
        if len(self.queue)>self.window:
            self._apply(self.queue.popleft(),-1)

    def _apply(self,row,sign):
        self.machine_sizes[row["machine"]]+=sign
        for j,d in enumerate(row["numbers"]):
            self.positions[j][d]+=sign
            self.pooled[d]+=sign
            self.by_stream[row["stream"]][j][d]+=sign
            self.by_machine[row["machine"]][j][d]+=sign

    def models(self,stream,machine):
        width=self.width
        # Candidate formulations predeclared and symmetric.
        position=[normalize([v+80. for v in pos]) for pos in self.positions]
        pooled=normalize([v+200.*width for v in self.pooled])
        by_stream=[normalize([v+55. for v in pos]) for pos in self.by_stream[stream]]
        by_machine=[normalize([v+40. for v in pos]) for pos in self.by_machine[machine]]
        return {
            "fair": [[.1]*10 for _ in range(width)],
            "pooled": [pooled]*width,
            "position":position,
            "day_night":by_stream,
            # Deliberately unrealistic counterfactual if equipment is hidden.
            "equipment_id_visible":by_machine,
        }


def _metric():
    return {"forecasts":0,"correct_positions":0,"total_positions":0,
            "log_gain":0.,"best_full_ticket_hits":0,"top3_positions":0}


def score(metric,probs,numbers):
    width=len(numbers)
    picks=[max(range(10),key=lambda d:(probs[j][d],-d))
           for j in range(width)]
    metric["forecasts"]+=1
    metric["correct_positions"]+=sum(a==b for a,b in zip(picks,numbers))
    metric["top3_positions"]+=sum(numbers[j] in sorted(range(10),key=lambda d:
                              (-probs[j][d],d))[:3] for j in range(width))
    metric["best_full_ticket_hits"]+=int(picks==numbers)
    metric["total_positions"]+=width
    metric["log_gain"]+=sum(math.log(max(1e-12,probs[j][d])/.1)
                            for j,d in enumerate(numbers))


def finalize(metric):
    n=metric["forecasts"]
    return {
        "target_draws":n,
        "position_correct":metric["correct_positions"],
        "position_total":metric["total_positions"],
        "top1_rate":metric["correct_positions"]/metric["total_positions"],
        "top3_rate":metric["top3_positions"]/metric["total_positions"],
        "full_straight_hits":metric["best_full_ticket_hits"],
        "expected_fair_full_straight_hits":n/(10**(metric["total_positions"]//n)),
        "mean_log_gain_vs_uniform":metric["log_gain"]/n
    }


def evaluate(game,scenario,trials=TRIALS,train=TRAIN_DRAWS,test=TEST_DRAWS,probe_v2=True):
    width=GAMES[game]["size"]
    agg={name:_metric() for name in
         ("fair","pooled","position","day_night","equipment_id_visible","oracle","v2_live")}
    v2_passed=0
    v2_forecasts=0
    # Only test first replicate with live production v2, sampling evenly
    # across held-out segment to control computational expense.
    for replicate in range(trials):
        history=simulate(game,scenario,train+test,replicate)
        rolling=RollingCounts(width)
        for i,row in enumerate(history):
            if i>=train:
                predictions=rolling.models(row["stream"],row["machine"])
                predictions["oracle"]=row["truth_probs"]
                for name,dist in predictions.items():
                    score(agg[name],dist,row["numbers"])
                if probe_v2 and replicate==0 and (i-train)%(max(1,test//V2_PROBE_TARGETS))==0:
                    ready=forecast_v2(game,history[:i],row["stream"])
                    # Use genuine production mixture probability, but the
                    # top combination requires finding the global maximum.
                    # Per-position marginals of a mixture are obtained from
                    # the expert marginals (chain's later marginals need
                    # explicit summation over prior positions).
                    observed=joint_probability(ready,row["numbers"])
                    m=agg["v2_live"]
                    m["forecasts"]+=1
                    m["total_positions"]+=width
                    m["log_gain"]+=math.log(observed/(.1**width))
                    m["position_correct"] if False else None
                    v2_passed+=int(ready["gate_passed"])
                    v2_forecasts+=1
            rolling.add(row)
        if (replicate+1)%4==0:
            print(game,scenario,"replicate",replicate+1,"/",trials,flush=True)
    report={name:finalize(m) for name,m in agg.items() if name!="v2_live"}
    report["v2_production_probe"]={
        "targets_checked":v2_forecasts,
        "gate_triggered":v2_passed,
        "mean_joint_log_gain":agg["v2_live"]["log_gain"]/v2_forecasts
                 if v2_forecasts else None,
        "note":"Live v2 genuine joint probability evaluated on preselected sparse target origins; per-position tickets not approximated here."
    }
    # Flag machine-ID model as a counterfactual, not actionable.
    return {
        "game":game,"scenario":scenario,
        "test_draws_per_replicate":test,"replicates":trials,
        "synthetic_not_real":True,
        "device_id_not_known_before_real_wager":True,
        "methods":report,
    }


def markdown(result):
    lines=[
        "# VAL virtual drawing-machine laboratory",
        "",
        "**This is a statistical virtual apparatus, not an exact physical",
        "replica of the Virginia Lottery's equipment.** Ball-set IDs,",
        "pretest observations and equipment-selection availability are",
        "unknown for the individual real Pick 3/4/5 archived draws.",
        "",
        "Each virtual draw contains one independent digit selection per",
        "position, except for the explicitly declared echo experiment.",
        "Repetitions are allowed, as in the real digit games. The simulator",
        "selects one hypothetical equipment ID per day, and performs two",
        "pretests. Those private synthetic states do not automatically",
        "become legal pre-wager features.",
        "",
        "Eight scenarios: fair independent; weak fixed-position skew",
        "(12.5% instead of 10% for one digit); strong fixed-position skew",
        "(22% for one digit); pooled 14.5% digit bias; Day-only 17%",
        "pooled skew; halfway 18% favorite-digit reversal; randomly",
        "selected hidden opposing machines with *uniform unconditional*",
        "outcomes; and a 30% same-previous-position echo mechanism.",
        "",
        "Models are online rolling-frequency baselines with symmetric",
        "smoothing, plus the exact deployed v2 formula probed on a fixed",
        "sparse sample of target origins. The perfect-information oracle",
        "receives the simulator's secret probabilities and supplies the",
        "best possible log-score achievable under those assumptions.",
        "The equipment-aware model has hypothetical advance access to",
        "machine identity; real-world advance access is UNVERIFIED.",
        "",
        "| Game | Virtual scenario | Fair top-1 | Pooled top-1 | Position top-1 | Visible equipment top-1 | Oracle top-1 | Live v2 gate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    ]
    for game,cases in result["games"].items():
        for name,case in cases.items():
            x=case["methods"]
            lines.append("| "+game+" | "+name+" | "+
                f'{100*x["fair"]["top1_rate"]:.2f}%'+ " | "+
                f'{100*x["pooled"]["top1_rate"]:.2f}%'+ " | "+
                f'{100*x["position"]["top1_rate"]:.2f}%'+ " | "+
                f'{100*x["equipment_id_visible"]["top1_rate"]:.2f}%'+ " | "+
                f'{100*x["oracle"]["top1_rate"]:.2f}%'+ " | "+
                str(x["v2_production_probe"]["gate_triggered"])+"/"+
                str(x["v2_production_probe"]["targets_checked"])+" |")
    lines+=["",
        "## Decision",
        "",
        "A simulator with injected bias measures our *ability to recover that",
        "bias*. It does not demonstrate that Virginia's real drawings have",
        "the same bias. The fair scenario quantifies false positives; the",
        "hidden-machine scenario checks irreducible uncertainty.",
        "Model selection must come from observations available before the",
        "actual wager cut-off. A model that improves only with secret",
        "machine IDs is not a usable strategy.",
        "",
        "[Complete target-level aggregate metrics](research_virtual_draw_lab.json).",""]
    return "\n".join(lines)


def main():
    result={
        "version":"virtual_digit_draw_lab_v1",
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "scenarios":SCENARIOS,"train_draws":TRAIN_DRAWS,
        "test_draws":TEST_DRAWS,"replicates":TRIALS,
        "games":{},"research_only":True
    }
    for game in GAMES_TEST:
        result["games"][game]={}
        for scenario in SCENARIOS:
            case=evaluate(game,scenario)
            result["games"][game][scenario]=case
            methods=case["methods"]
            print(json.dumps({
                "game":game,"scenario":scenario,
                "pooled_top1":methods["pooled"]["top1_rate"],
                "oracle_top1":methods["oracle"]["top1_rate"],
                "live_v2_gate":methods["v2_production_probe"]["gate_triggered"],
                "v2_log_gain":methods["v2_production_probe"]["mean_joint_log_gain"]
            }),flush=True)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
    MD_OUT.write_text(markdown(result)+"\n")
    print("Saved",OUTPUT,MD_OUT,flush=True)

if __name__=="__main__":
    main()
