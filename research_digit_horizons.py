"""VAL digit-game long-history and future-horizon falsification laboratory.

Checks a specific user's hypothesis: does a ticket aimed at the immediate
next draw actually perform better when compared to later draws?

Official Pick 3, Pick 4, Pick 5 raw history is read at run time. Features
only inspect draws strictly before the forecast origin. Three old-ensemble
tickets and three independent uniform controls are frozen at each origin,
then scored against the 1st, 2nd, 3rd, 4th, 6th, and 8th subsequent draws.
(The offset is 0,1,2,3,5,7 below: 0 means the immediate next draw.)

A separate probabilistic comparison explores five non-ML predictive
architectures, selects on early origins, and scores a later fixed period.
All historical data have been available to earlier VAL researchers;
this is chronological internal testing, NOT an untouched prospective test.
Do not promote a model from this output into production.
"""
from __future__ import annotations
import hashlib
import json
import math
import random
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

from research_10k import load_official_history
from val import GAMES,generate,score_batch

GAMES_TO_TEST=("pick3","pick4","pick5")
HORIZONS=(0,1,2,3,5,7)
MODEL_NAMES=("uniform","legacy_ensemble","long500","same_session","multi_scale","lag_transition")
START_HISTORY=500
MAX_ORIGINS=2400
SPLIT_FRACTION=.45
SEED=20261118
JSON_OUT=Path("reports/research_digit_horizons.json")
MD_OUT=Path("reports/research_digit_horizons.md")


def stable_seed(*parts):
    payload="|".join(map(str,(SEED,)+parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8],"big")


def normalize(values):
    s=sum(values)
    if not s>0:raise ValueError("Nonpositive distribution")
    out=[float(x/s) for x in values]
    if any(not (0<x<1) for x in out) or abs(sum(out)-1)>1e-8:
        raise AssertionError("Invalid digit distribution")
    return out


def build_models(previous,target_stream,width):
    """Every feature uses only completed draws before the origin."""
    if len(previous)<50:raise ValueError("Need established historical observations")
    h=previous[-500:]
    totals=[[0]*10 for _ in range(width)]
    short=[[0]*10 for _ in range(width)]
    same=[[0]*10 for _ in range(width)]
    transitions=[[[0]*10 for _ in range(10)] for _ in range(width)]
    for idx,row in enumerate(h):
        nums=row["numbers"]
        is_recent=idx>=len(h)-50
        for pos,d in enumerate(nums):
            totals[pos][d]+=1
            if is_recent:short[pos][d]+=1
            if row["stream"]==target_stream:same[pos][d]+=1
        if idx>0:
            earlier=h[idx-1]["numbers"]
            for pos,d in enumerate(nums):
                transitions[pos][earlier[pos]][d]+=1

    model={name:[] for name in MODEL_NAMES}
    for pos in range(width):
        hot=[totals[pos][d]+2 for d in range(10)]
        fresh=[short[pos][d]+2 for d in range(10)]
        cold=[1/math.sqrt(x) for x in hot]
        legacy=normalize([.4*a/sum(hot)+.4*b/sum(fresh)+.2*c/sum(cold)
                          for a,b,c in zip(hot,fresh,cold)])
        long_p=normalize([totals[pos][d]+10 for d in range(10)])
        session_p=normalize([same[pos][d]+15 for d in range(10)])
        short_p=normalize([short[pos][d]+8 for d in range(10)])
        multiscale=normalize([.45*long_p[d]+.35*session_p[d]+.20*short_p[d]
                              for d in range(10)])
        prev_digit=h[-1]["numbers"][pos]
        lag_p=normalize([transitions[pos][prev_digit][d]+20 for d in range(10)])
        model["uniform"].append([.1]*10)
        model["legacy_ensemble"].append(legacy)
        model["long500"].append(long_p)
        model["same_session"].append(session_p)
        model["multi_scale"].append(multiscale)
        model["lag_transition"].append(lag_p)
    return model


def predictive_gain(position_distributions,numbers):
    return sum(math.log(position_distributions[i][d]/.1)
               for i,d in enumerate(numbers))


def cluster_ci(values_and_dates,repeats=600):
    """Bootstrap calendar days, not tickets, to handle shared draw outcomes."""
    buckets=defaultdict(list)
    for stamp,value in values_and_dates:buckets[stamp[:10]].append(value)
    groups=list(buckets.values())
    if len(groups)<3:return [None,None]
    group_sums=[sum(v) for v in groups]
    group_sizes=[len(v) for v in groups]
    rng=random.Random(stable_seed("day-ci",len(groups),round(sum(group_sums),8)))
    means=[]
    for _ in range(repeats):
        picks=[rng.randrange(len(groups)) for _ in groups]
        means.append(sum(group_sums[i] for i in picks)/sum(group_sizes[i] for i in picks))
    means.sort()
    return [means[int(.025*(repeats-1))],means[int(.975*(repeats-1))]]


def aggregate(values):
    if not values:return dict(n=0,mean=None,first_half=None,second_half=None,ci95=[None,None])
    mid=len(values)//2
    v=[x for _,x in values]
    return dict(n=len(v),mean=sum(v)/len(v),
                first_half=sum(v[:mid])/max(1,mid),
                second_half=sum(v[mid:])/max(1,len(v)-mid),
                ci95=cluster_ci(values))


def validate_rows(game,rows):
    if game not in GAMES_TO_TEST:raise ValueError("Unexpected game")
    if len(rows)<600:raise ValueError("Too few official draws")
    width=GAMES[game]["size"]
    prev=None
    for row in rows:
        if len(row["numbers"])!=width or any(type(n)!=int or not 0<=n<=9 for n in row["numbers"]):
            raise ValueError("Invalid digit record")
        if row["stream"] not in ("Day","Night"):
            raise ValueError("Invalid draw session")
        stamp=row["at"]
        if prev is not None and stamp<=prev:raise ValueError("Duplicate or unordered drawing timestamps in "+game+": previous "+str(prev)+" next "+str(stamp)+" row="+repr(row))
        prev=stamp


def provenance(rows):
    streams=Counter(r["stream"] for r in rows)
    return {
        "n":len(rows),
        "first":rows[0]["at"],
        "last":rows[-1]["at"],
        "sessions":dict(streams),
        "fingerprint_sha256":hashlib.sha256(
            json.dumps([(r["at"],r["stream"],r["numbers"]) for r in rows],
                       separators=(",",":")).encode("utf-8")).hexdigest()
    }


def analyze(game,rows,max_origins=MAX_ORIGINS):
    validate_rows(game,rows)
    width=GAMES[game]["size"]
    start=max(START_HISTORY,len(rows)-max(HORIZONS)-max_origins)
    end=len(rows)-max(HORIZONS)
    usable=end-start
    if usable<min(300,max_origins):raise ValueError("Insufficient test origins")
    mid=start+int(usable*SPLIT_FRACTION)
    # The candidate set and offsets are fixed before this test is run.
    scores={part:{(model,h):[] for model in MODEL_NAMES for h in HORIZONS}
            for part in ("calibration","final")}
    tickets={h:{"ensemble":{"position_matches":0,"exact":0,"tickets":0,"origins":0},
                "uniform_control":{"position_matches":0,"exact":0,"tickets":0,"origins":0}}
             for h in HORIZONS}
    first_ids={}
    for i in range(start,end):
        part="calibration" if i<mid else "final"
        previous=rows[max(0,i-500):i]
        relevant_streams={rows[i+h]["stream"] for h in HORIZONS}
        modeled={stream:build_models(previous,stream,width) for stream in relevant_streams}
        if part=="final":
            # A single forecast is generated once at the origin; the SAME
            # combinations are reused at later horizons rather than optimized
            # after seeing the later actual numbers.
            epicks=generate(game,previous,"ensemble",3,
                            random.Random(stable_seed(game,"ensemble",rows[i]["at"])))
            rpicks=generate(game,[],"random",3,
                            random.Random(stable_seed(game,"control",rows[i]["at"])))
            if len(epicks)!=3 or len(rpicks)!=3:raise AssertionError("Need 3 tickets")
            first_ids.setdefault(rows[i]["at"],epicks)
        for h in HORIZONS:
            target=rows[i+h]
            models=modeled[target["stream"]]
            for name,dist in models.items():
                gain=predictive_gain(dist,target["numbers"])
                scores[part][name,h].append((target["at"],gain))
            if part=="final":
                for key,picks in (("ensemble",epicks),("uniform_control",rpicks)):
                    s=score_batch(game,picks,target)
                    t=tickets[h][key]
                    t["position_matches"]+=s["total_matches"]
                    t["exact"]+=s["exact"]
                    t["tickets"]+=s["tickets"]
                    t["origins"]+=1
        if (i-start+1)%1000==0:
            print(game+" forecast origins "+str(i-start+1)+"/"+str(usable),flush=True)
    # Select a model/horizon using the CALIBRATION segment alone; later
    # final performance must never change model selection.
    scored_cal={(name,h):aggregate(samples)["mean"]
                for (name,h),samples in scores["calibration"].items()}
    immediate=("uniform",0)
    cross=("uniform",0)
    for name in MODEL_NAMES:
        if scored_cal[name,0]>scored_cal[immediate]:immediate=(name,0)
        for h in HORIZONS:
            if scored_cal[name,h]>scored_cal[cross]:cross=(name,h)

    final={str(h):{} for h in HORIZONS}
    for h in HORIZONS:
        for name in MODEL_NAMES:
            final[str(h)][name]=aggregate(scores["final"][name,h])
    selected={}
    for key,pair in (("immediate",immediate),("any_horizon",cross)):
        name,h=pair
        val=final[str(h)][name]
        selected[key]={
            "model":name,"horizon_offset":h,
            "calibration_mean_log_gain":scored_cal[pair],
            "final":val,
            "final_statistical_gate":name!="uniform" and val["ci95"][0]>0
                and val["first_half"]>0 and val["second_half"]>0,
            "eligible_for_live_promotion":False,
            "why_not":"Historical results already inspected in previous research; independent future validation and relevant payout analysis still required"
        }
    for h in HORIZONS:
        for label,t in tickets[h].items():
            t["position_hit_rate"]=t["position_matches"]/(t["tickets"]*width)
            t["fair_expected_hit_rate"]=.1
            t["fair_expected_position_matches"]=t["tickets"]*width*.1
    return {
        "game":game,
        "history":provenance(rows),
        "origin_calibration":dict(count=mid-start,first=rows[start]["at"],last=rows[mid-1]["at"]),
        "origin_final":dict(count=end-mid,first=rows[mid]["at"],last=rows[end-1]["at"]),
        "model_specifications":{
            "uniform":"10% per digit in each position",
            "legacy_ensemble":"Original hot50+hot500+cold500 mixture, position-specific",
            "long500":"500-draw position frequency with symmetric 100-observation prior",
            "same_session":"Same target session frequency with symmetric 150-observation prior",
            "multi_scale":"45% long500, 35% same_session, 20% short50 with symmetric 80-observation prior",
            "lag_transition":"Previous position digit transition over 500 drawings with 200-observation prior"
        },
        "horizons":list(HORIZONS),
        "selected_by_calibration_only":selected,
        "final_model_log_gains":final,
        "final_frozen_ticket_horizon_comparison":{str(h):v for h,v in tickets.items()},
        "meta":{
            "horizon_offsets":"0=immediate next recorded draw, 1=one draw later, etc; may span multiple calendar days in old history",
            "train_history":"Previous 500 recorded draws, never target or later",
            "time_split":"First 45% of eligible modern origin draws for selection; later 55% for final chronological evaluation",
            "model_promotion":"No automatic promotion; prospective records required"
        }
    }


def render(result):
    lines=[
        "# VAL Pick 3/4/5 — restored history and cross-draw forecast challenge",
        "",
        "Source: official Virginia Lottery full-history download. Models are",
        "constructed using only results strictly before the forecast origin.",
        "The same ensemble and independently drawn random-control tickets",
        "are compared against the next recorded drawing and later drawings.",
        "A model is frozen using the earlier calendar segment before checking",
        "a later segment. Historical source was previously inspected, so",
        "these are NOT untouched prospective results.",
        "",
        "One correct-position digit is worth no prize on a Straight-only wager;",
        "position-hit rates are diagnostic, not financial returns.",
        ""
    ]
    for game,r in result["games"].items():
        h=r["history"]
        lines += [
            "## "+game.upper(),
            "",
            "Official source: **"+format(h["n"],",")+" recorded draws** ("+
                h["first"]+" to "+h["last"]+").",
            "Fingerprint SHA-256: "+h["fingerprint_sha256"],
            "Calibration origins: "+str(r["origin_calibration"]["count"])+
                "; later evaluation origins: **"+str(r["origin_final"]["count"])+"**.",
            "",
            "| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |",
            "| --- | ---: | --- |"
        ]
        for model in MODEL_NAMES:
            v=r["final_model_log_gains"]["0"][model]
            lines.append("| "+model+" | "+format(v["mean"],"+.6f")+" | ["+
                         format(v["ci95"][0],"+.6f")+", "+
                         format(v["ci95"][1],"+.6f")+"] |")
        lines += [
            "",
            "Calibration-only selection for immediate next draw: **"+
                r["selected_by_calibration_only"]["immediate"]["model"]+"**.",
            "Calibration-only selection across forecast offsets: **"+
                r["selected_by_calibration_only"]["any_horizon"]["model"]+
                "** at offset "+
                str(r["selected_by_calibration_only"]["any_horizon"]["horizon_offset"])+".",
            "",
            "| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |",
            "| --- | ---: | ---: | ---: | ---: |"
        ]
        for offset in HORIZONS:
            row=r["final_frozen_ticket_horizon_comparison"][str(offset)]
            a=row["ensemble"]; b=row["uniform_control"]
            lines.append("| "+str(offset)+" | "+
                         str(a["position_matches"])+"/"+str(a["tickets"]*GAMES[game]["size"])+
                         " ("+format(100*a["position_hit_rate"],".2f")+"%) | "+
                         str(b["position_matches"])+"/"+str(b["tickets"]*GAMES[game]["size"])+
                         " ("+format(100*b["position_hit_rate"],".2f")+"%) | "+
                         str(a["exact"])+" | "+str(b["exact"])+" |")
        lines+=[""]
    lines += [
        "## Decision rule",
        "",
        "Do not change production tickets merely because an earlier forecast",
        "looked good against another date. An exploitable horizon must survive",
        "independent future forecasts with model parameters and horizons",
        "committed ahead of those results, outperform fair probabilities",
        "with positive lower confidence bound, and demonstrate meaningful",
        "payout improvement. Multiple horizons and games mean multiple",
        "hypotheses, requiring correction for selection.",
        "",
        "**This report does not assert that any prediction edge exists.**",
        "Original prospective ledger and live pick scheduling are unchanged",
        "apart from the separately committed history-retention fix.",
        "",
        "Machine-readable detail: [research_digit_horizons.json](research_digit_horizons.json).",
        ""
    ]
    return "\n".join(lines)


def main():
    result={
        "version":"VAL_digit_horizon_falsification_v1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "max_test_origins_per_game":MAX_ORIGINS,
        "horizon_offsets":list(HORIZONS),
        "research_only":True,
        "history_overfit_warning":True,
        "games":{}
    }
    for game in GAMES_TO_TEST:
        rows=load_official_history(game)
        result["games"][game]=analyze(game,rows)
        x=result["games"][game]
        print(json.dumps({
            "game":game,"all_history_draws":x["history"]["n"],
            "final_origins":x["origin_final"]["count"],
            "frozen_calibration_decisions":x["selected_by_calibration_only"]
        }),flush=True)
    JSON_OUT.parent.mkdir(parents=True,exist_ok=True)
    JSON_OUT.write_text(json.dumps(result,indent=2)+"\n")
    MD_OUT.write_text(render(result)+"\n")
    print("Report saved",JSON_OUT,MD_OUT,flush=True)


if __name__=="__main__":
    main()
