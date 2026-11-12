"""Daily GitHub Actions runner. Reports and ledger survive in the repository."""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from val import ET, GAMES, Store, backtest, generate, simulate, sync_game


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


def run(store, output, count=3, trials=1000, now=None, syncer=sync_game):
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ET).date()
    restore(store,output/"ledger.json")
    report = ["# VAL daily report", "", f"Generated: {now.isoformat()} · Eastern date: {day}", "",
              "Paper picks for research. These weights are not proven winning probabilities.", "",
              "## Picks", "",
              "Each batch targets the first draw in its selected session on an Eastern date **after its creation date**. Same-day draws are excluded. Picks for games without a draw tomorrow wait for their next eligible draw.", "",
              "Three unique combinations per game/session, with three saved random control combinations. Re-running on the same Eastern date reuses saved batches.", "",
              "| Game | Session | Batch | Combinations | Latest loaded draw (ET) |", "| --- | --- | --- | --- | --- |"]
    failures=[]; batches=[]; summaries=[]; all_records=[]
    for game,g in GAMES.items():
        if "id" not in g: continue
        try:
            syncer(store,game)
            history=store.history(game)
            if not history: raise ValueError("No history received")
            age=(day-datetime.fromisoformat(history[-1]["at"]).astimezone(ET).date()).days
            if age>7: raise ValueError(f"Latest draw is {age} days old; new picks skipped")
            # Settle previous saved batches using newly downloaded results.
            ledger=store.ledger(game)
            for stream in sessions(game):
                selected=store.history(game,stream)
                existing=next((r for r in ledger if r["stream"]==stream and datetime.fromisoformat(r["created"]).astimezone(ET).date()==day),None)
                if existing is None:
                    picks=generate(game,selected,"ensemble",count)
                    baseline=generate(game,[],"random",len(picks))
                    pid=store.record(game,stream,"ensemble",picks,baseline)
                    existing=next(r for r in store.ledger(game) if r["id"]==pid)
                batches.append(dict(game=game,name=g["name"],**existing))
                latest=datetime.fromisoformat(selected[-1]["at"]).astimezone(ET).isoformat()
                report.append(f"| {g['name']} | {stream} | #{existing['id']} | "+" / ".join(f"`{selection(p)}`" for p in existing["picks"])+f" | {latest} |")
            # Analysis uses All sessions, clearly separate from prospective session picks.
            test=backtest(game,history,count=count,tests=100)
            mc=simulate(game,history,trials=trials)
            summaries.append(dict(game=game,backtest=test,frequency_check=mc))
        except Exception as exc:
            failures.append(dict(game=game,error=safe(exc)))
        all_records.extend(dict(game=game,**r) for r in store.ledger(game))
    report += ["", "## Prospective results", "",
               "Every saved batch is retained in [ledger.json](ledger.json), including losses. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.", "",
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
               "Nine recurring games update from Virginia Lottery official downloads. Pick 3/4/5 have separate Day and Night picks; Cash Pop has five separate sessions. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.", "",
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
