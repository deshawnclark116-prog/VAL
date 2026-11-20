"""Daily GitHub Actions runner. Reports and ledger survive in the repository."""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from val import ET, GAMES, Store, backtest, generate, rank_ensemble_picks, simulate, sync_game, draw_schedule, next_draw
from val_digit_formula_v2 import VERSION as DIGIT_FORMULA_VERSION, generate_picks as generate_digit_formula
from val_box import random_box_picks, box_score_batch


def restore(store, path):
    if not path.exists(): return
    records = json.loads(path.read_text())
    if records.get("version") != 1: raise ValueError("Unsupported ledger version")
    with store.connect() as db:
        for r in records["predictions"]:
            db.execute("INSERT INTO predictions(id,game,created,stream,method,data,result) VALUES(?,?,?,?,?,?,?)",
                       (r["id"],r["game"],r["created"],r["stream"],r["method"],json.dumps(r["data"]),
                        json.dumps(r["result"]) if r["result"] is not None else None))


def save_ledger(store, path):
    with store.connect() as db:
        rows = db.execute("SELECT id,game,created,stream,method,data,result FROM predictions ORDER BY id").fetchall()
    records = [dict(id=pid,game=game,created=created,stream=stream,method=method,
                    data=json.loads(data),result=json.loads(result) if result else None)
               for pid,game,created,stream,method,data,result in rows]
    path.write_text(json.dumps(dict(version=1,predictions=records),indent=2)+"\n")


def sessions(game):
    if GAMES[game].get("digits"): return ["Day","Night"]
    if game == "cashpop": return ["Coffee Break","Lunch Break","Rush Hour","Prime Time","After Hours"]
    return ["Main"]


def safe(value):
    return str(value).replace("|","/").replace("\n"," ").replace("\r", " ").replace("<","&lt;").replace(">","&gt;")


def selection(pick):
    return " ".join(str(n) for n in pick["numbers"]) + (" + " + str(pick["bonus"]) if pick["bonus"] is not None else "")


def ranked_selection(picks):
    """Never retroactively rank older saved combinations."""
    if all(p.get("rank") == i for i, p in enumerate(picks, 1)):
        if picks and picks[0].get("formula_version") == DIGIT_FORMULA_VERSION and not picks[0].get("signal_gate_passed"):
            roles = ("Paper 1", "Paper 2", "Paper 3")
        else:
            roles = ("Primary", "Alt 1", "Alt 2")
        return " / ".join(f"**{roles[i] if i < 3 else 'Alt'}:** `{selection(p)}`" for i, p in enumerate(picks))
    return " / ".join(f"`{selection(p)}`" for p in picks) + " (legacy: unranked)"

def run(store, output, count=3, trials=1000, now=None, syncer=sync_game):
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ET).date()
    restore(store,output/"ledger.json")
    report = ["# VAL next-draw report", "", f"Updated: {now.astimezone(ET).isoformat()} · Eastern time", "",
              "Paper picks for research. These weights are not proven winning probabilities.", "",
              "## Picks", "",
              "Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.", "",
              "Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.", "",
              "**Pick 3/4/5 target complete Any Order (Box) digit sets.** Box v4 uses cumulative evidence plus recent confirmation to rank complete unordered digit-multisets by summed probabilities of all permutations, not partial-position matches. Without a proven signal it uses three nonoverlapping, all-distinct random Box candidates and three independent same-type Box controls (Paper 1/2/3, not purported ranked predictions). Each Box ticket represents a hypothetical $1 Any Order play; no purchases are made. Other games retain their existing methods. Old saved predictions remain unchanged. Missing latest results withhold new picks.", "",
              "| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |", "| --- | --- | --- | --- | --- | --- | --- |"]
    failures=[]; batches=[]; summaries=[]; all_records=[]
    for game,g in GAMES.items():
        if "id" not in g: continue
        try:
            syncer(store,game)
            history=[r for r in store.history(game) if datetime.fromisoformat(r["at"])<=now]
            if not history: raise ValueError("No history received")
            age=(day-datetime.fromisoformat(history[-1]["at"]).astimezone(ET).date()).days
            if age>7: raise ValueError(f"Latest draw is {age} days old; new picks skipped")
            # Settle previous saved batches using newly downloaded results.
            ledger=store.ledger(game)
            expected=max((d for d in draw_schedule(game,now) if datetime.fromisoformat(d["at"])<=now),key=lambda d:d["at"])
            if not any(r["at"]==expected["at"] and r["stream"]==expected["stream"] for r in history):
                stamp=datetime.fromisoformat(expected["at"]).astimezone(ET).isoformat()
                raise ValueError(f"Waiting for latest completed {expected['stream']} result ({stamp}); new picks withheld")
            target=next_draw(game,now)
            if (datetime.fromisoformat(target["at"])-now).total_seconds()<15*60:
                raise ValueError("Next draw is less than 15 minutes away; waiting for its result before preparing the following draw")
            stream=target["stream"]
            # Preserve old predictions and add one immutable versioned Box prediction for
            # the identical future target, enabling real A/B comparison.
            existing=next((r for r in ledger if r.get("target")==target and
                           (not g.get("digits") or r["method"]==DIGIT_FORMULA_VERSION)),None)
            if existing is None:
                if g.get("digits"):
                    # Actual replacement of the digit prediction formula;
                    # do not just rerank arbitrary sampled old candidates.
                    picks,model_meta=generate_digit_formula(game,history,stream,count)
                    method=DIGIT_FORMULA_VERSION
                else:
                    picks=rank_ensemble_picks(game,history,generate(game,history,"ensemble",count))
                    model_meta=None
                    method="ensemble"
                baseline=(random_box_picks(game,len(picks))
                          if g.get("digits") else
                          generate(game,[],"random",len(picks)))
                pid=store.record(game,stream,method,picks,baseline,target=target,
                                 training_latest=history[-1],created=now,
                                 model_meta=model_meta)
                existing=next(r for r in store.ledger(game) if r["id"]==pid)
            batches.append(dict(game=game,name=g["name"],**existing))
            used=existing["training_latest"]
            latest=datetime.fromisoformat(used["at"]).astimezone(ET).isoformat()
            target_label=datetime.fromisoformat(target["at"]).astimezone(ET).isoformat()
            report.append(f"| {g['name']} | {target_label} | {stream} | #{existing['id']} | "+ranked_selection(existing["picks"])+f" | {latest} | `{selection(used)}` ({used['stream']}) |")
            # Analysis uses All sessions, clearly separate from prospective session picks.
            test=backtest(game,history,count=count,tests=100)
            mc=simulate(game,history,trials=trials)
            summaries.append(dict(game=game,backtest=test,frequency_check=mc))
        except Exception as exc:
            failures.append(dict(game=game,error=safe(exc)))
        all_records.extend(dict(game=game,**r) for r in store.ledger(game))
    report += ["", "## Complete Any Order (Box) results — PRIMARY METRIC", "",
               "A Box match requires ALL selected digits, including repeated digits, regardless of their order. A one-way all-identical pattern is Straight-only. Every settled batch is rescored from its original immutable picks and actual drawing; historical picks were not necessarily purchased as Box tickets.", "",
               "Payout and net are **hypothetical** $1 Any Order paper-wagers using published no-FIREBALL prize tables. No tickets were bought. Equal-cost random controls are compared where possible; historical legacy picks may have different digit multiplicities.", "",
               "| Digit game | Settled batches | Model Box wins | Control Box wins | Model Straight | Control Straight | Model paper net | Control paper net |",
               "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for game in ("pick3","pick4","pick5"):
        entries=[r for r in all_records if r["game"]==game and r["result"] is not None]
        model=[box_score_batch(game,r["picks"],r["result"]["draw"]) for r in entries]
        control=[box_score_batch(game,r["baseline"],r["result"]["draw"]) for r in entries]
        exact=lambda side:sum(r["result"][side]["exact"] for r in entries)
        report.append(f"| {GAMES[game]['name']} | {len(entries)} | "
                      f"{sum(z['box_wins'] for z in model)} | {sum(z['box_wins'] for z in control)} | "
                      f"{exact('model')} | {exact('random')} | "
                      f"${sum(z['box_net_usd'] for z in model):,} | "
                      f"${sum(z['box_net_usd'] for z in control):,} |")
    report += ["", "## Other game results", "",
               "| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |",
               "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for game,g in GAMES.items():
        if g.get("digits") or "id" not in g: continue
        settled=[r["result"] for r in all_records if r["game"]==game and r["result"] is not None]
        total=lambda group,key:sum(r[group][key] for r in settled)
        report.append(f"| {g['name']} | {len(settled)} | {total('model','tickets')} | {total('model','exact')} | {total('random','tickets')} | {total('random','exact')} |")
    pending=sum(r["result"] is None for r in all_records)
    report += ["",f"Pending batches: {pending}. This report retains the original saved picks and controls; no retrospective replacement.","",
               "## Historical checks", "",
               "100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.", "",
               "| Game (all sessions) | Ensemble full Box wins | Random full Box wins | Ensemble exact wins | Random exact wins | Frequency p-value |",
               "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in summaries:
        result={r["method"]:r for r in row["backtest"]["results"]}
        e,r=result["ensemble"],result["random"]
        box_e=e.get("box_wins","—")
        box_r=r.get("box_wins","—")
        report.append(f"| {GAMES[row['game']]['name']} | {box_e} | {box_r} | {e['exact']} | {r['exact']} | {row['frequency_check']['p_value']:.4f} |")
    report += ["", "Full five-method statistics and simulation details: [analysis.json](analysis.json).", "",
               "## Coverage and update status", "",
               "Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Box scoring uses published no-FIREBALL $1 Any Order prize tables for paper-only payout and net estimates; no actual wagering occurs. Fireball, 50/50, and Combo are excluded. Other games have no payout/ROI calculation. Keno needs a CSV import, and seasonal raffle ticket numbers are assigned.", "",
               "[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)", ""]
    if failures:
        report += ["### Update / analysis failures", ""]
        report += [f"- {GAMES[f['game']]['name']}: {f['error']}" for f in failures]
    else: report += ["All nine automatic history updates and analyses completed."]
    # Keep the complete ledger; only the latest report/picks/analysis are replaced.
    save_ledger(store,output/"ledger.json")
    (output/"latest.md").write_text("\n".join(report)+"\n")
    (output/"picks.json").write_text(json.dumps(dict(generated_at=now.isoformat(),batches=batches,failures=failures),indent=2)+"\n")
    (output/"analysis.json").write_text(json.dumps(dict(generated_at=now.isoformat(),games=summaries),indent=2)+"\n")
    return dict(batches=len(batches),failures=failures)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default="reports")
    parser.add_argument("--trials",type=int,default=1000)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="val-daily-") as directory:
        result=run(Store(Path(directory)/"val.sqlite3"),args.output,trials=args.trials)
    print(json.dumps(result,indent=2))
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a") as f: f.write((Path(args.output)/"latest.md").read_text())
    # Report failures visibly without discarding successful games or the ledger.
    if result["failures"]:
        for failure in result["failures"]: print(f"::warning::{failure['game']}: {failure['error']}")
    if not result["batches"]: raise SystemExit("No games produced picks; inspect reports/latest.md")


if __name__=="__main__": main()
