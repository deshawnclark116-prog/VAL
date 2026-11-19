"""VAL v3 accuracy research: new pre-draw digit prediction hypotheses.

Research only, never silently overwrites the v2 live model. Predictive
features are measurable before the drawing and each forecast is scored on
the NEXT real observation in chronological order.

Unlike an ordinary p-value computed on a repeatedly inspected chart,
each candidate has a prequential e-process: log E = sum(log(p(actual)/p(fair))).
For any predictable normalized distribution and fair independent draws,
E is a nonnegative test martingale. With a frozen candidate registry,
a crossing of 1/alpha can be evaluated using a union bound over models
and games. This research archive was previously inspected and is NOT
an independently pristine confirmatory period. Future-only promotion
must start a new frozen e-process at publication.

Core metrics are exactly: actual next-digit top-1 hit rate, top-3 digit
coverage, full-ordered top combination wins, proper log-probability gain.
Partial-position matches are not prize wins.
"""
from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime,timezone
from pathlib import Path

from research_10k import load_official_history
from val import ET,GAMES

VERSION="val_digit_accuracy_experts_v3"
GAMES_TEST=("pick3","pick4","pick5")
CANDIDATES=(
    "historical_5000","weekday_session","month_session",
    "two_draw_lag","pooled_digit_bias","cold_60",
    "previous_sum","previous_set_presence")
TRAIN_MIN=1100
PREDICTIONS=1300
CALIBRATION=350
BUDGET_ALPHA=.05
JSON_OUT=Path("reports/research_digit_accuracy_v3.json")
MD_OUT=Path("reports/research_digit_accuracy_v3.md")


def _norm(x):
    total=sum(x)
    if total<=0:raise ValueError("Empty distribution")
    p=[v/total for v in x]
    if any(not 0<v<1 for v in p) or abs(sum(p)-1)>1e-10:
        raise AssertionError("Bad normalized probability")
    return p


def _smooth(counts,pseudocount):
    return _norm([v+pseudocount for v in counts])


def _context(row):
    dt=datetime.fromisoformat(row["at"]).astimezone(ET)
    return dt.weekday(),dt.month


def build(game,prior,target_stream,target_weekday,target_month):
    """Eight distinct distributions; only historical results are inspected."""
    width=GAMES[game]["size"]
    if len(prior)<100:raise ValueError("Need prior results")
    window=prior[-5000:]
    short=prior[-60:]
    ctx=window[-1600:]
    long=[[0]*10 for _ in range(width)]
    weekday=[[0]*10 for _ in range(width)]
    month=[[0]*10 for _ in range(width)]
    recent=[[0]*10 for _ in range(width)]
    lag2=[[[0]*10 for _ in range(10)] for _ in range(width)]
    smod=[[[0]*10 for _ in range(10)] for _ in range(width)]
    setmatch=[[0]*2 for _ in range(width)]
    pooled=[0]*10
    for row in window:
        for j,d in enumerate(row["numbers"]):
            long[j][d]+=1
            pooled[d]+=1
    for row in short:
        for j,d in enumerate(row["numbers"]):recent[j][d]+=1
    for k,row in enumerate(ctx):
        dow,m=_context(row)
        if row["stream"]==target_stream and dow==target_weekday:
            for j,d in enumerate(row["numbers"]):weekday[j][d]+=1
        if row["stream"]==target_stream and m==target_month:
            for j,d in enumerate(row["numbers"]):month[j][d]+=1
    # One-step-ahead conditional samples, with antecedent only at older time.
    for k in range(2,len(ctx)):
        before=ctx[k-2]["numbers"]
        prior_draw=ctx[k-1]["numbers"]
        now=ctx[k]["numbers"]
        s=sum(prior_draw)%10
        seen=set(prior_draw)
        for j,d in enumerate(now):
            lag2[j][before[j]][d]+=1
            smod[j][s][d]+=1
            setmatch[j][int(d in seen)]+=1
    latest=prior[-1]["numbers"]
    second=prior[-2]["numbers"]
    current_sum=sum(latest)%10
    current_seen=set(latest)
    experts={}
    # Long-run bias with 2,000 effective observations of prior evidence.
    experts["historical_5000"]=[_smooth(x,200.) for x in long]
    # Session × weekday and session × month patterns, heavily shrunk.
    experts["weekday_session"]=[_smooth(x,55.) for x in weekday]
    experts["month_session"]=[_smooth(x,55.) for x in month]
    # Two-draw delay: sparse contexts must avoid enormous odds.
    experts["two_draw_lag"]=[_smooth(lag2[j][second[j]],55.) for j in range(width)]
    # Pool evidence across different digit positions.
    experts["pooled_digit_bias"]=[_smooth([pooled[d]+width*200. for d in range(10)],1.) for _ in range(width)]
    # Deliberate inverse-frequency challenger, strongly regularized.
    experts["cold_60"]=[_norm([(recent[j][d]+60.)**(-.5)
                               for d in range(10)]) for j in range(width)]
    # Previous draw digit sum is known by the next draw.
    experts["previous_sum"]=[_smooth(smod[j][current_sum],55.) for j in range(width)]
    # Learn whether numbers present in last draw tend to carry forward,
    # correcting for the number of distinct digits present in that draw.
    # This is a contextual class prior, NOT assigning all ten equally
    # if only three digits occurred previously.
    membership=[]
    for j in range(width):
        inside=setmatch[j][1]+100.
        outside=setmatch[j][0]+100.
        fraction=inside/(inside+outside)
        n_inside=len(current_seen)
        n_outside=10-n_inside
        raw=[(fraction/n_inside if d in current_seen
              else (1-fraction)/n_outside) for d in range(10)]
        membership.append(_norm(raw))
    experts["previous_set_presence"]=membership
    return experts


def evaluate(game,history,train_min=TRAIN_MIN,predictions=PREDICTIONS,calibration=CALIBRATION):
    width=GAMES[game]["size"]
    start=max(train_min,len(history)-predictions)
    if len(history)-start<=calibration+150:raise ValueError("Need evaluation period")
    train_rows=history[start:start+calibration]
    test_rows=history[start+calibration:]
    accum={name:{"train":defaultdict(list),"test":defaultdict(list)}
           for name in CANDIDATES}
    for i in range(start,len(history)):
        target=history[i]
        weekday,month=_context(target)
        model=build(game,history[:i],target["stream"],weekday,month)
        segment="train" if i<start+calibration else "test"
        day=datetime.fromisoformat(target["at"]).astimezone(ET).date().isoformat()
        for name,distributions in model.items():
            actual=target["numbers"]
            gain=sum(math.log(distributions[j][d]*10) for j,d in enumerate(actual))
            first=sum(actual[j]==max(range(10),key=lambda d:distributions[j][d])
                      for j in range(width))
            top3=sum(actual[j] in sorted(range(10),key=lambda d:
                                          (-distributions[j][d],d))[:3]
                     for j in range(width))
            predicted=[max(range(10),key=lambda d:distributions[j][d])
                       for j in range(width)]
            accum[name][segment][day].append((gain,first,top3,int(predicted==actual)))
        if (i-start+1)%500==0:
            print(f"{game}: scored {i-start+1}/{len(history)-start} chronological forecasts",flush=True)
    per_model={}
    threshold=math.log(len(CANDIDATES)*len(GAMES_TEST)/BUDGET_ALPHA)
    for name in CANDIDATES:
        segmented={}
        for segment in ("train","test"):
            days=accum[name][segment]
            observations=[item for d in days.values() for item in d]
            n=len(observations)
            daily=[sum(x[0] for x in records)/len(records) for records in days.values()]
            mean=sum(x[0] for x in observations)/n
            e=0.
            maximum=0.
            for row in observations:
                e+=row[0]
                maximum=max(maximum,e)
            segmented[segment]={
                "forecasts":n,
                "days":len(days),
                "mean_log_gain":mean,
                "total_log_e":e,
                "max_prefix_log_e":maximum,
                "significance_threshold":threshold,
                "would_cross_anytime_e_gate":maximum>=threshold,
                "top1_position_hits":sum(x[1] for x in observations),
                "top1_position_hit_rate":sum(x[1] for x in observations)/(n*width),
                "top3_position_hits":sum(x[2] for x in observations),
                "top3_position_hit_rate":sum(x[2] for x in observations)/(n*width),
                "top_combo_straight_hits":sum(x[3] for x in observations),
                "expected_top1_position_rate_if_fair":.1,
                "expected_top3_position_rate_if_fair":.3,
                "expected_top_combo_wins_if_fair":n/(10**width),
                "mean_day_log_gain":statistics.mean(daily)
            }
        per_model[name]=segmented
    return {
        "game":game,
        "official_draws":len(history),
        "calibration_targets":len(train_rows),
        "later_targets":len(test_rows),
        "later_first":test_rows[0]["at"],
        "later_last":test_rows[-1]["at"],
        "e_threshold_log":threshold,
        "models":per_model,
        "note":"All v3 hypotheses are historical exploratory; no live change or uncontaminated future promotion"
    }


def render(data):
    lines=[
        "# VAL v3: test new prediction FORMULAS on real later drawings",
        "",
        "This evaluates eight **previously unimplemented contextual",
        "prediction hypotheses** against fair uniform probability, using",
        "only strictly earlier official results. Every method is checked",
        "for ordered next-draw likelihood, its top digit in each position,",
        "three most likely digits in each position, and a complete",
        "highest-scoring Straight number. All models are fixed before",
        "the later test segment, with no holdout-based parameter tuning.",
        "",
        "The archive itself has been inspected in prior VAL experiments,",
        "so this remains historical exploratory research rather than",
        "untouched future proof.",
        "",
        "Top-1 fair expectation = **10%**, top-3 = **30%** of positions.",
        "E-value log threshold controls a hypothetical frozen study over",
        "eight methods × three games at family-wise 5% under iid fair",
        "draws; a historical threshold crossing would still need future",
        "replication. The running maximum checks every past prefix.",
        "",
        "| Game | Method | Later draws | Top-digit accuracy | Top-3 coverage | Complete Straight hits | Fair-relative log gain | Anytime gate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"
    ]
    for game,report in data["games"].items():
        for method,row in report["models"].items():
            s=row["test"]
            lines.append("| "+game+" | "+method+" | "+str(s["forecasts"])+" | "+
                         f'{s["top1_position_hit_rate"]*100:.2f}%'+
                         " | "+f'{s["top3_position_hit_rate"]*100:.2f}%'+
                         " | "+str(s["top_combo_straight_hits"])+
                         " | "+f'{s["mean_log_gain"]:+.6f}'+
                         " | "+("TRIGGER" if s["would_cross_anytime_e_gate"] else "No")+" |")
    lines+=["",
            "## Promotion protocol",
            "",
            "A challenger must beat uniform on strict next-draw probability",
            "accuracy, and independently demonstrate predictive value on",
            "future time-stamped draws, with its complete model specification",
            "and e-value gate frozen beforehand. A few high partial-hit",
            "numbers or fortunate exact wins do not establish a repeatable edge.",
            "No production prediction formula is automatically switched.",
            "",
            "[Complete results](research_digit_accuracy_v3.json).",""]
    return "\n".join(lines)


def main():
    result={
        "version":VERSION,"created_at":datetime.now(timezone.utc).isoformat(),
        "games":{},"candidate_names":list(CANDIDATES),
        "alpha_budget":BUDGET_ALPHA,"research_only":True
    }
    for game in GAMES_TEST:
        rows=load_official_history(game)
        result["games"][game]=evaluate(game,rows)
        s=result["games"][game]
        print(json.dumps({"game":game,"later_targets":s["later_targets"],
            "models":{name:{"top1":res["test"]["top1_position_hit_rate"],
                             "log_gain":res["test"]["mean_log_gain"],
                             "gate":res["test"]["would_cross_anytime_e_gate"]}
                      for name,res in s["models"].items()}}),flush=True)
    JSON_OUT.parent.mkdir(parents=True,exist_ok=True)
    JSON_OUT.write_text(json.dumps(result,indent=2)+"\n")
    MD_OUT.write_text(render(result)+"\n")


if __name__=="__main__":main()
