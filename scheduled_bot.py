"""Daily GitHub Actions runner. Reports and ledger survive in the repository."""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from val import ET, GAMES, Store, backtest, generate, rank_ensemble_picks, simulate, sync_game, draw_schedule, next_draw


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
              "Three unique combinations per target, with three saved random controls. New batches label Primary, Alt 1, and Alt 2 using experimental model sampling weights, not calibrated winning chances. Previously saved batches remain unranked and unchanged. If the latest completed result is missing, the game waits rather than generating from outdated input.", "",
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
            existing=next((r for r in ledger if r.get("target")==target),None)
            if existing is None:
                picks=rank_ensemble_picks(game,history,generate(game,history,"ensemble",count))
                baseline=generate(game,[],"random",len(picks))
                pid=store.record(game,stream,"ensemble",picks,baseline,target=target,training_latest=history[-1],created=now)
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
    report += ["", "## Prospective results", "",
               "Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.", "",
               "| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |",
               "| --- | --- | --- | --- | --- | --- |"]
    for game,g in GAMES.items():
        settled=[r["result"] for r in all_records if r["game"]==game and r["result"] is not None]
        if "id" not in g: continue
        total=lambda group,key:sum(r[group][key] for r in settled)
        report.append(f"| {g['name']} | {len(settled)} | {total('model','tickets')} | {total('model','exact')} | {total('random','tickets')} | {total('random','exact')} |")
    pending=sum(r["result"] is None for r in all_records)
    report += ["",f"Pending batches: {pending}. This report retains the original saved picks and controls; no retrospective replacement.","",
               "## Historical checks", "",
               "100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.", "",
               "| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |",
               "| --- | --- | --- | --- |"]
    for row in summaries:
        result={r["method"]:r for r in row["backtest"]["results"]}
        e,r=result["ensemble"],result["random"]
        report.append(f"| {GAMES[row['game']]['name']} | {e['exact']} / {e['tickets']} | {r['exact']} / {r['tickets']} | {row['frequency_check']['p_value']:.4f} |")
    report += ["", "Full five-method statistics and simulation details: [analysis.json](analysis.json).", "",
               "## Coverage and update status", "",
               "Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.", "",
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
