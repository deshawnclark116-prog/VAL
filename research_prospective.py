"""VAL frozen prospective one-pick method comparison.

Paper-only experiment. All predictions are timestamped and appended BEFORE
the targeted draw and wager close, then settled ONLY against their named game,
date, and Day/Night session after official results become available.

No live VAL picks or production model logic are touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, time, timezone
from pathlib import Path

from research_decades import GAMES, fetch_full
from research_one_pick import Rolling, choose_one, fair_box_probability_digits, stable_rng
from val import ET, next_draw

MODEL_VERSION = "val_prospective_one_pick_v1"
# Diagnostic look-ahead horizons for a FORECAST THAT WAS SAVED BEFORE THE
# ORIGINAL target. They never change the original target or its grading.
FROZEN_HORIZON_OFFSETS = (0,1,2,3,5,7)
METHOD_SPECS = (
    "random", "position_hot_top_500", "position_cold_top_30",
    "session_hier_sample_500", "position_cold_sample_1000",
)
LEDGER = Path("reports/prospective_one_pick.json")
SUMMARY = Path("reports/prospective_one_pick.md")
_CUTOFF = {"Day": time(13, 53), "Night": time(22, 45)}


def legal_target(game, now):
    """None if wager sales have already closed for the immediate next draw."""
    if now.tzinfo is None: raise ValueError("Aware UTC timestamp required")
    target = next_draw(game, now)
    dt = datetime.fromisoformat(target["at"])
    local_dt = dt.astimezone(ET)
    stream = target["stream"]
    last_sales = datetime.combine(local_dt.date(), _CUTOFF[stream], tzinfo=ET)
    if now >= last_sales.astimezone(timezone.utc):
        return None
    return {"game":game, "date":local_dt.date().isoformat(),"stream":stream,
            "draw_at_utc":dt.isoformat(),
            "wagers_close_utc":last_sales.astimezone(timezone.utc).isoformat()}


def earlier(a, target):
    if a["date"] < target["date"]:return True
    return a["date"]==target["date"] and a["stream"]=="Day" and target["stream"]=="Night"


def prepare_pick(game, target, earlier_history, method, version=MODEL_VERSION):
    """Returns immutable pre-draw number plus entire forecast distribution."""
    width=GAMES[game][1]
    generator=stable_rng(version,game,target["date"],target["stream"],method)
    if method=="random":
        digits=[generator.randrange(10) for _ in range(width)]
        probabilities=[[0.1]*10 for _ in range(width)]
    else:
        family, policy, window=method.rsplit("_",2)
        if policy not in ("top","sample"):raise ValueError(method)
        size=int(window)
        if len(earlier_history)<size:raise ValueError("Training sample too short")
        tracker=Rolling(earlier_history[-size:],width,size)
        probabilities=tracker.probabilities(family,target["stream"])
        digits=choose_one(probabilities,policy,generator)
    return {
        "numbers":digits,
        "forecast_by_position":probabilities,
        "fair_box_probability":fair_box_probability_digits(digits)
    }


def score_saved_pick(prediction, actual):
    numbers=prediction["numbers"]
    observed=actual["numbers"]
    straight=numbers==observed
    any_order=sorted(numbers)==sorted(observed)
    fireball_any_order=False
    fire=actual.get("fireball")
    if fire is not None:
        for i in range(len(observed)):
            hypothetical=observed[:]
            hypothetical[i]=fire
            fireball_any_order |= sorted(hypothetical)==sorted(numbers)
    probabilities=prediction["forecast_by_position"]
    likelihood=math.prod(probabilities[i][d] for i,d in enumerate(observed))
    if likelihood <= 0:raise AssertionError("Zero likelihood assigned to a real draw")
    return {
        "straight":straight,"any_order_including_straight":any_order,
        "fireball_any_order":fireball_any_order,
        "log_score_gain_vs_fair":round(math.log(likelihood*(10**len(numbers))),10)
    }


def update(game, history, entries, now):
    """Do not mutate entries; return new append-only+settlement representation."""
    entries=[dict(x) for x in entries]
    lookup={(r["date"],r["stream"]):r for r in history}
    changes={"created":0,"settled":0,"pending":0,"correction_warnings":0,
             "horizon_graded":0,
             "skipped_because_wager_window_closed":False}
    # Official history may be returned in descending order and may once have
    # been Night-only. Always use recorded chronological draw order.
    ordered=sorted(history,key=lambda x:(x["date"],
                  0 if x["stream"]=="Day" else 1))
    index_by_target={(r["date"],r["stream"]):i for i,r in enumerate(ordered)}
    if len(index_by_target)!=len(ordered):
        raise ValueError("Ambiguous official dates/sessions in prospective source")
    for entry in entries:
        actual=lookup.get((entry["target"]["date"],entry["target"]["stream"]))
        if actual is None:
            if entry.get("result") is None:changes["pending"]+=1
            continue
        if entry.get("result") is None:
            entry["result"]={
                "date":actual["date"],"stream":actual["stream"],
                "official_numbers":actual["numbers"],"official_fireball":actual["fireball"],
                "graded_at_utc":now.astimezone(timezone.utc).isoformat(),
                "methods":{name:score_saved_pick(pred,actual)
                           for name,pred in entry["predictions"].items()}
            }
            changes["settled"]+=1
        elif entry["result"]["official_numbers"] != actual["numbers"] or (
             entry["result"]["official_fireball"] != actual["fireball"]):
            entry["source_revision_warning"]=True
            changes["correction_warnings"]+=1

    # A fixed pre-target prediction is optionally evaluated at future horizons.
    # These are explicitly labeled DIAGNOSTICS, not retargeted official picks.
    # Every new horizon grade is immutable; corrections raise an audit warning.
    for entry in entries:
        key=(entry["target"]["date"],entry["target"]["stream"])
        ix=index_by_target.get(key)
        if ix is None:
            continue
        horizon_results=entry.setdefault("horizon_results",{})
        for offset in FROZEN_HORIZON_OFFSETS:
            if ix+offset>=len(ordered):
                continue
            future=ordered[ix+offset]
            hkey=str(offset)
            previous_grade=horizon_results.get(hkey)
            if previous_grade is None:
                horizon_results[hkey]={
                    "offset_draws":offset,
                    "actual_date":future["date"],
                    "actual_stream":future["stream"],
                    "actual_numbers":list(future["numbers"]),
                    "methods":{name:score_saved_pick(pred,future)
                               for name,pred in entry["predictions"].items()},
                }
                changes["horizon_graded"]+=1
            elif (previous_grade["actual_date"]!=future["date"] or
                  previous_grade["actual_stream"]!=future["stream"] or
                  previous_grade["actual_numbers"]!=future["numbers"]):
                entry["source_revision_warning"]=True
                changes["correction_warnings"]+=1

    target=legal_target(game,now)
    if target is None:
        changes["skipped_because_wager_window_closed"]=True
        return entries,changes

    if (target["date"],target["stream"]) in lookup:
        raise ValueError("Refusing to create a prediction for a published draw")
    if any(x["target"]["date"]==target["date"]
           and x["target"]["stream"]==target["stream"] for x in entries):
        return entries,changes

    past=[r for r in history if earlier(r,target)]
    if len(past)<1000:
        raise ValueError(f"Not enough verified history for {game}")
    if past and past[-1]["date"]>=target["date"] and target["stream"]=="Day":
        raise ValueError("Potential target data leakage")
    pickset={name:prepare_pick(game,target,past,name) for name in METHOD_SPECS}
    created_utc=now.astimezone(timezone.utc).isoformat()
    if datetime.fromisoformat(created_utc)>=datetime.fromisoformat(target["wagers_close_utc"]):
        raise AssertionError("Pre-draw betting cutoff was violated")
    entry={
        "id":hashlib.sha256(f"{game}:{target['date']}:{target['stream']}:{MODEL_VERSION}".encode()).hexdigest()[:16],
        "version":MODEL_VERSION,
        "created_at_utc":created_utc,
        "target":target,
        "training_draws_available":len(past),
        "training_latest_date":past[-1]["date"],
        "predictions":pickset,
        "result":None
    }
    entries.append(entry)
    changes["created"]+=1
    changes["pending"]+=1
    return entries,changes


def report_markdown(data, updates):
    lines=[
        "# VAL frozen future-draw one-number test",
        "",
        f"Latest run (UTC): {data['last_run_utc']}",
        "",
        "**Paper predictions only. No money wagered.**",
        "Each named method gets one number for the same exact future",
        "Day/Night draw. Entries are saved before wager close and can only",
        "be scored against the identified official result.",
        "Old predictions are not replaced or retargeted.",
        "",
        "All contenders are frozen as version "+MODEL_VERSION+".",
        "Method selection followed exploratory historical testing; only",
        "results **after this registry started** can independently test them.",
        "A few hits cannot prove a persistent lottery advantage.",
        "",
    ]
    for game, entries in data["games"].items():
        changes=updates[game]
        settled=[x for x in entries if x.get("result")]
        pending=[x for x in entries if not x.get("result")]
        lines += [f"## {game.title()}",
                  "",
                  f"Draws recorded: {len(entries)}. Graded: {len(settled)}. Pending: {len(pending)}.",
                  "",
                  "| Method | Paper picks graded | Straight | Any Order | Fair expected Any Order | Average log-score vs fair |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for method in METHOD_SPECS:
            n=len(settled)
            straight=sum(x["result"]["methods"][method]["straight"] for x in settled)
            box=sum(x["result"]["methods"][method]["any_order_including_straight"] for x in settled)
            expected=sum(x["predictions"][method]["fair_box_probability"] for x in settled)
            avg_log=sum(x["result"]["methods"][method]["log_score_gain_vs_fair"]
                        for x in settled)/n if n else 0.0
            lines.append(f"| {method} | {n} | {straight} | {box} | "
                         f"{expected:.3f} | {avg_log:+.5f} |")
        # Full comparisons are reported without selecting a winning horizon.
        # Observations across offsets reuse forecasts and overlapping draws.
        lines += ["", "### Frozen forecast checked against later draws (diagnostic)",
                  "",
                  "Offset 0 is the originally named draw; later offsets are",
                  "subsequent recorded draws. This does not retarget the ticket.",
                  "Position matches alone do not constitute prize wins.",
                  "",
                  "| Offset | Matured forecasts | "+ " | ".join(METHOD_SPECS)+" |",
                  "| ---: | ---: | "+" | ".join("---:" for _ in METHOD_SPECS)+" |"]
        for offset in FROZEN_HORIZON_OFFSETS:
            matured=[x for x in entries if str(offset) in x.get("horizon_results",{})]
            cells=[]
            for method in METHOD_SPECS:
                n=0
                for x in matured:
                    actual=x["horizon_results"][str(offset)]["actual_numbers"]
                    selected=x["predictions"][method]["numbers"]
                    n+=sum(a==b for a,b in zip(selected,actual))
                denominator=len(matured)*GAMES[game][1]
                cells.append(format(100*n/denominator,".2f")+"%" if denominator else "—")
            lines.append("| "+str(offset)+" | "+str(len(matured))+" | "+
                         " | ".join(cells)+" |")
        lines.append("")

        if pending:
            last=pending[-1]
            vals=", ".join(f"{name}: {''.join(map(str,pick['numbers']))}"
                           for name,pick in last["predictions"].items())
            lines += ["",
                      f"Most recent future target: {last['target']['date']} "
                      f"{last['target']['stream']}; created "
                      f"{last['created_at_utc']}.",
                      "",
                      f"Precommitted paper numbers: {vals}.",
                     ]
        lines += [""]
    lines += ["## Reliability",
              "",
              "- Only verified earlier public drawing results may train a method.",
              "- Day/Night target and sales-closing time are fixed and logged.",
              "- Any Order counts account for ticket digit multiplicity.",
              "- FIREBALL is only evaluated when the actual official result reports it.",
              "- Scores do not establish profitability or predictive advantage.",
              "- The independent random control is retained, including all losses.",
              "- Some official archives lag; pending picks are not assumed to lose.",
              "",
              "Full append-only prediction ledger: [prospective_one_pick.json](prospective_one_pick.json).",
              "",
              ]
    return "\n".join(lines)


def cycle(now, ledger=LEDGER, summary=SUMMARY):
    data=json.loads(ledger.read_text()) if ledger.exists() else {
        "created_utc":now.astimezone(timezone.utc).isoformat(),
        "version":MODEL_VERSION,"methods":list(METHOD_SPECS),
        "games":{game:[] for game in GAMES}
    }
    if data["version"] != MODEL_VERSION or data["methods"] != list(METHOD_SPECS):
        raise ValueError("Existing frozen registry differs; refusing to overwrite")
    updates={}
    for game in GAMES:
        official,meta=fetch_full(game)
        new,changes=update(game,official,data["games"].get(game,[]),now)
        data["games"][game]=new
        updates[game]=changes
        print(json.dumps({"game":game,"changes":changes,
                          "official_archive_latest":official[-1]["date"]}),flush=True)
    data["last_run_utc"]=now.astimezone(timezone.utc).isoformat()
    ledger.parent.mkdir(parents=True,exist_ok=True)
    ledger.write_text(json.dumps(data,indent=2)+"\n")
    summary.write_text(report_markdown(data,updates)+"\n")
    print(f"Saved {ledger} and {summary}")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ledger",default=str(LEDGER))
    parser.add_argument("--summary",default=str(SUMMARY))
    args=parser.parse_args()
    cycle(datetime.now(timezone.utc),Path(args.ledger),Path(args.summary))


if __name__=="__main__":main()
