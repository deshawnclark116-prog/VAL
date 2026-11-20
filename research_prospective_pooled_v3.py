"""VAL pooled-digit v3: immutable, truly FUTURE prediction accuracy trial.

This is a strictly pre-draw frozen prediction-formula challenger. It does not
modify the live v2 formula or retroactively rewrite incumbent predictions.
All methods and the random control are committed before the sales deadline;
no skipped losses. A fair e-value process begins with the first recorded
future target and can only advance when a named official draw is available.

Uncalibrated top-1/3 historical accuracy was noticed only in retrospective
data, so future-only validation is mandatory before considering promotion.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime,timezone
from pathlib import Path

from research_decades import GAMES,fetch_full
from research_prospective import legal_target,earlier
from research_pooled_digit_followup import probabilities,WINDOW
from val import ET
from val_box import box_score_batch

VERSION="val_pooled_digit_future_accuracy_v1"
GAMES_TEST=("pick3","pick4","pick5")
LEDGER=Path("reports/prospective_pooled_digit_v3.json")
REPORT=Path("reports/prospective_pooled_digit_v3.md")
ALPHA=.05/len(GAMES_TEST)
LOG_E_GATE=math.log(1/ALPHA)


def secure_seed(*pieces):
    raw="|".join(map(str,(VERSION,)+pieces)).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8],"big")


def prepare(game,target,history):
    """Freeze actual candidate digit forecasts from strictly earlier results."""
    width=GAMES[game][1]
    prior=[r for r in history if earlier(r,target)]
    if len(prior)<500:raise ValueError("Insufficient verified history")
    counts=[0]*10
    for r in prior[-WINDOW:]:
        for d in r["numbers"]:counts[d]+=1
    probs=probabilities(counts,width)
    ranked=sorted(range(10),key=lambda d:(-probs[d],d))
    # Model A tests its per-position top-1 accuracy. B tests three
    # combination coverage with distinct choices at each digit position.
    # Rotation deliberately makes the three ordered tickets different.
    best=[ranked[0]]*width
    model_tickets=[[ranked[(k+j)%3] for j in range(width)]
                   for k in range(3)]
    rng=random.Random(secure_seed(game,target["date"],target["stream"]))
    sample=[rng.sample(range(10),3) for _ in range(width)]
    controls=[[sample[j][k] for j in range(width)] for k in range(3)]
    if len({tuple(x) for x in model_tickets})!=3:
        raise AssertionError("Repeated v3 ticket")
    return {
        "training_size":len(prior),
        "training_latest_date":prior[-1]["date"],
        "probability_by_digit":probs,
        "best_position_digit":ranked[0],
        "top_three_digits":ranked[:3],
        "model_tickets":model_tickets,
        "uniform_coverage_controls":controls,
    }


def grade(pick,actual):
    digits=actual["numbers"]
    n=len(digits)
    p=pick["probability_by_digit"]
    likelihood=math.prod(p[d] for d in digits)
    if likelihood<=0:raise AssertionError("Invalid probability")
    best=pick["best_position_digit"]
    top3=set(pick["top_three_digits"])
    model=pick["model_tickets"]
    baseline=pick["uniform_coverage_controls"]
    def matched(ticket):return sum(a==b for a,b in zip(ticket,digits))
    game="pick"+str(n)
    model_box=box_score_batch(game,[{"numbers":ticket} for ticket in model],actual)
    control_box=box_score_batch(game,[{"numbers":ticket} for ticket in baseline],actual)
    return {
        "model_box_wins":model_box["box_wins"],
        "control_box_wins":control_box["box_wins"],
        "model_box_paper_net_usd":model_box["box_net_usd"],
        "control_box_paper_net_usd":control_box["box_net_usd"],
        "model_box_fair_expected_wins":model_box["box_fair_expected_wins"],
        "control_box_fair_expected_wins":control_box["box_fair_expected_wins"],
        "top1_position_matches":sum(d==best for d in digits),
        "top3_position_matches":sum(d in top3 for d in digits),
        "total_positions":n,
        "mean_log_gain_vs_fair":math.log(likelihood)+n*math.log(10),
        "model_ticket_max_position_matches":max(matched(ticket) for ticket in model),
        "control_ticket_max_position_matches":max(matched(ticket) for ticket in baseline),
        "model_at_least_one_position":any(matched(t)>0 for t in model),
        "control_at_least_one_position":any(matched(t)>0 for t in baseline),
        "model_at_least_two_on_single_ticket":any(matched(t)>=2 for t in model),
        "control_at_least_two_on_single_ticket":any(matched(t)>=2 for t in baseline),
        "model_exact":sum(t==digits for t in model),
        "control_exact":sum(t==digits for t in baseline),
    }


def update(game,history,entries,now):
    if now.tzinfo is None:raise ValueError("Timezone-aware timestamp required")
    rows={(r["date"],r["stream"]):r for r in history}
    if len(rows)!=len(history):raise ValueError("Ambiguous official results")
    records=[dict(r) for r in entries]
    changes={"created":0,"settled":0,"pending":0,"source_revisions":0,
             "too_late":False}
    for row in records:
        key=(row["target"]["date"],row["target"]["stream"])
        actual=rows.get(key)
        if actual is None:
            if row["result"] is None:changes["pending"]+=1
            continue
        if row["result"] is None:
            row["result"]={
                "official_numbers":actual["numbers"],
                "official_fireball":actual.get("fireball"),
                "graded_utc":now.astimezone(timezone.utc).isoformat(),
                "accuracy":grade(row["forecast"],actual),
            }
            changes["settled"]+=1
        elif (row["result"]["official_numbers"]!=actual["numbers"] or
              row["result"]["official_fireball"]!=actual.get("fireball")):
            row["source_revision_warning"]=True
            changes["source_revisions"]+=1

    target=legal_target(game,now)
    if target is None:
        changes["too_late"]=True
        return records,changes
    if (target["date"],target["stream"]) in rows:
        raise ValueError("Target already published, refusing retrospective forecast")
    if any(r["target"]["date"]==target["date"] and
           r["target"]["stream"]==target["stream"] for r in records):
        return records,changes
    prediction=prepare(game,target,history)
    created=now.astimezone(timezone.utc).isoformat()
    if created>=target["wagers_close_utc"]:
        raise AssertionError("Attempted after-close prediction")
    records.append({
        "id":hashlib.sha256((game+target["date"]+target["stream"]+VERSION).encode()).hexdigest()[:16],
        "created_utc":created,
        "version":VERSION,
        "target":target,
        "forecast":prediction,
        "result":None
    })
    changes["created"]+=1
    changes["pending"]+=1
    return records,changes


def summary(registry,updates):
    lines=[
        "# VAL v3 pooled-digit future accuracy trial",
        "",
        "New forecast specification frozen BEFORE each individual drawing.",
        "Never retargets or replaces saved forecasts and controls.",
        "**This candidate was selected after historical exploration.**",
        "Its credibility depends entirely on subsequent real-world draws.",
        "",
        "PRIMARY METRIC: full Any Order (Box) digit-multiset wins, not",
        "partial digit matches. Repeated digits must match exactly.",
        "Box payout/net are hypothetical $1 per eligible ticket using",
        "published Virginia non-FIREBALL prizes. No wagers were purchased.",
        "The prospective frozen model/control ticket structures are",
        "unchanged; they can have different Box permutation counts.",
        "Exact-order overlaps are diagnostic, not Straight wagers.",
        "",
        "| Game | Settled draws | Model BOX wins | Control BOX wins | Model $1 paper net | Control $1 paper net | Exact model | Exact control | Anytime evidence gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for game,records in registry["games"].items():
        settled=[r for r in records if r["result"] is not None]
        n=len(settled)
        # Recompute derived Box results from frozen selections so that
        # older settled records remain immutable; no retroactive picks.
        model_box=[box_score_batch(game,
                     [{"numbers":x} for x in r["forecast"]["model_tickets"]],
                     {"numbers":r["result"]["official_numbers"]})
                   for r in settled]
        control_box=[box_score_batch(game,
                     [{"numbers":x} for x in r["forecast"]["uniform_coverage_controls"]],
                     {"numbers":r["result"]["official_numbers"]})
                   for r in settled]
        wins=sum(r["result"]["accuracy"]["model_exact"] for r in settled)
        random_wins=sum(r["result"]["accuracy"]["control_exact"] for r in settled)
        vals=[r["result"]["accuracy"]["mean_log_gain_vs_fair"] for r in settled]
        running=max_running=0.
        for val in vals:
            running+=val
            max_running=max(max_running,running)
        lines.append("| "+game+" | "+str(n)+" | "+
             str(sum(x["box_wins"] for x in model_box))+" | "+
             str(sum(x["box_wins"] for x in control_box))+" | $"+
             str(sum(x["box_net_usd"] for x in model_box))+" | $"+
             str(sum(x["box_net_usd"] for x in control_box))+" | "+
             str(wins)+" | "+str(random_wins)+" | "+
             ("TRIGGER" if max_running>=LOG_E_GATE else "No")+" |")
        if records:
            last=records[-1]
            if last["result"] is None:
                lines.extend(["",f"Latest frozen target for {game}: "+
                    last["target"]["date"]+" "+last["target"]["stream"]+
                    " (saved "+last["created_utc"]+").",
                    "Model top digit: "+str(last["forecast"]["best_position_digit"])+
                    "; candidates: "+", ".join("".join(map(str,t))
                                      for t in last["forecast"]["model_tickets"])+
                    "; independently seeded controls: "+
                    ", ".join("".join(map(str,t))
                              for t in last["forecast"]["uniform_coverage_controls"])+"."])
    lines+=["","Fair e-value evidence threshold is log(60) with a",
            "three-game union-bound allocation; it begins at the first",
            "future saved prediction and is not a historical backtest p-value.",
            "A threshold crossing alone warrants source and regime auditing,",
            "not claims of profitable lottery prediction.",
            "",
            "[Immutable prediction records](prospective_pooled_digit_v3.json).",""]
    return "\n".join(lines)


def cycle(now,ledger=LEDGER,report=REPORT):
    data=json.loads(ledger.read_text()) if ledger.exists() else {
        "created_utc":now.astimezone(timezone.utc).isoformat(),
        "version":VERSION,
        "signal_model":"pooled_5000_pr200_per_position_v1",
        "games":{game:[] for game in GAMES_TEST},
    }
    if data["version"]!=VERSION or data["signal_model"]!="pooled_5000_pr200_per_position_v1":
        raise ValueError("Frozen candidate registry mismatch")
    updates={}
    for game in GAMES_TEST:
        source,metadata=fetch_full(game)
        old=data["games"][game]
        new,change=update(game,source,old,now)
        data["games"][game]=new
        updates[game]=change
        print(json.dumps({"game":game,"source_rows":len(source),
                          "latest_date":source[-1]["date"],"changes":change}),flush=True)
    data["last_run_utc"]=now.astimezone(timezone.utc).isoformat()
    ledger.parent.mkdir(parents=True,exist_ok=True)
    ledger.write_text(json.dumps(data,indent=2)+"\n")
    report.write_text(summary(data,updates)+"\n")


def main():
    cycle(datetime.now(timezone.utc))


if __name__=="__main__":main()
