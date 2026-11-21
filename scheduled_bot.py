"""Daily GitHub Actions runner. Reports and ledger survive in the repository."""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from val import ET, GAMES, Store, backtest, generate, rank_ensemble_picks, score, simulate, sync_game, draw_schedule, next_draw
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
    """Show only the original first prediction, including archived multi-pick batches."""
    if not picks:
        return "—"
    pick = picks[0]
    if pick.get("rank") == 1:
        label = ("Paper" if pick.get("formula_version") == DIGIT_FORMULA_VERSION
                 and not pick.get("signal_gate_passed") else "Primary")
        return f"**{label}:** `{selection(pick)}`"
    return f"`{selection(pick)}` (legacy first saved pick)"


def fallback_scorecard(records):
    """Audit the original first ticket and first control for settled fallback batches.

    Rows are grouped by frozen formula version rather than conflating old and
    current fallbacks. Each row is a paper-only, complete Any Order comparison.
    """
    grouped = {}
    for entry in records:
        game = entry.get("game")
        if game not in ("pick3", "pick4", "pick5") or entry.get("result") is None:
            continue
        meta = entry.get("model_meta") or {}
        if meta.get("signal_gate_passed") is not False:
            continue
        if not entry.get("picks") or not entry.get("baseline"):
            continue
        key = (game, meta.get("formula_version") or entry.get("method") or "unknown")
        item = grouped.setdefault(key, dict(game=game, version=key[1], settled=0,
                                            wins=0, controls=0, fair_expected=0.0))
        actual = entry["result"]["draw"]
        model = box_score_batch(game, entry["picks"][:1], actual)
        control = box_score_batch(game, entry["baseline"][:1], actual)
        item["settled"] += 1
        item["wins"] += model["box_wins"]
        item["controls"] += control["box_wins"]
        item["fair_expected"] += model["box_fair_expected_wins"]
    return [grouped[k] for k in sorted(grouped)]


def run(store, output, count=1, trials=1000, now=None, syncer=sync_game):
    if count != 1:
        raise ValueError("Live VAL supports exactly one prediction and one random control per draw")
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ET).date()
    restore(store,output/"ledger.json")
    report = ["# VAL next-draw report", "", f"Updated: {now.astimezone(ET).isoformat()} · Eastern time", "",
              "Paper picks for research. These weights are not proven winning probabilities.", "",
              "## Picks", "",
              "Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.", "",
              "Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.", "",
              "**Exactly one prediction and one independent random control per upcoming game draw.** Pick 3/4/5 target complete Any Order (Box) digit sets, not partial-position matches. Box v4 evaluates cumulative and recent evidence; without a proven signal it returns one clearly labeled random paper Box selection, not an asserted edge. All tickets are hypothetical; none are purchased. Older multi-ticket batches are preserved unchanged in the ledger, but only each original first ticket is shown and counted in the one-pick comparison. Missing latest results withhold new picks.", "",
              "| Game | Target draw (ET) | Session | Batch | One prediction | Latest result used (ET) | Latest winning numbers used |", "| --- | --- | --- | --- | --- | --- | --- |"]
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
            # Preserve the original ledger unchanged; publish the primary ticket only.
            public_batch = dict(existing, picks=existing["picks"][:1], baseline=existing["baseline"][:1])
            batches.append(dict(game=game,name=g["name"],**public_batch))
            used=existing["training_latest"]
            latest=datetime.fromisoformat(used["at"]).astimezone(ET).isoformat()
            target_label=datetime.fromisoformat(target["at"]).astimezone(ET).isoformat()
            report.append(f"| {g['name']} | {target_label} | {stream} | #{existing['id']} | "+ranked_selection(public_batch["picks"])+f" | {latest} | `{selection(used)}` ({used['stream']}) |")
            # Analysis uses All sessions, clearly separate from prospective session picks.
            test=backtest(game,history,count=count,tests=100)
            mc=simulate(game,history,trials=trials)
            summaries.append(dict(game=game,backtest=test,frequency_check=mc))
        except Exception as exc:
            failures.append(dict(game=game,error=safe(exc)))
        all_records.extend(dict(game=game,**r) for r in store.ledger(game))
    report += ["", "## Complete Any Order (Box) results — PRIMARY METRIC", "",
               "A Box match requires ALL selected digits, including repeated digits, regardless of their order. A one-way all-identical pattern is Straight-only. Every settled batch is rescored using only its FIRST originally saved ticket and the FIRST original random control. Old three-ticket ledgers stay immutable, but their alternatives do not count toward this one-pick score. Historical picks were not necessarily purchased as Box tickets.", "",
               "Payout and net are **hypothetical** $1 Any Order paper-wagers using published no-FIREBALL prize tables, one ticket per side per settled batch. No tickets were bought. Historical first-choice tickets may have different digit multiplicities.", "",
               "| Digit game | Settled batches | Model Box wins | Control Box wins | Model Straight | Control Straight | Model paper net | Control paper net |",
               "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for game in ("pick3","pick4","pick5"):
        entries=[r for r in all_records if r["game"]==game and r["result"] is not None]
        model=[box_score_batch(game,r["picks"][:1],r["result"]["draw"]) for r in entries]
        control=[box_score_batch(game,r["baseline"][:1],r["result"]["draw"]) for r in entries]
        exact=lambda side:sum(score(game, r["picks"][0] if side=="model" else r["baseline"][0], r["result"]["draw"])["exact"] for r in entries)
        report.append(f"| {GAMES[game]['name']} | {len(entries)} | "
                      f"{sum(z['box_wins'] for z in model)} | {sum(z['box_wins'] for z in control)} | "
                      f"{exact('model')} | {exact('random')} | "
                      f"${sum(z['box_net_usd'] for z in model):,} | "
                      f"${sum(z['box_net_usd'] for z in control):,} |")
    report += ["", "## Fallback watch — one original ticket per drawing", "",
               "Only settled Pick 3/4/5 batches explicitly tagged as a no-signal fallback are included. Each row uses the first saved ticket and its original first random control; alternatives are never counted. Grouping by formula version avoids combining distinct experiments. Fair-expected wins come from the exact digit-multiplicity odds of those tickets, not estimated predictive probabilities. **These results do not demonstrate an edge**, especially when examining a version after its early wins.", "",
               "| Game | Fallback formula | Settled picks | Box wins | Random-control wins | Fair expected Box wins |",
               "| --- | --- | ---: | ---: | ---: | ---: |"]
    for row in fallback_scorecard(all_records):
        report.append(f"| {GAMES[row['game']]['name']} | `{safe(row['version'])}` | {row['settled']} | {row['wins']} | {row['controls']} | {row['fair_expected']:.4f} |")
    report += ["", "## Other game results", "",
               "| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |",
               "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for game,g in GAMES.items():
        if g.get("digits") or "id" not in g: continue
        settled=[r for r in all_records if r["game"]==game and r["result"] is not None]
        hits=lambda side:sum(score(game, r["picks"][0] if side=="model" else r["baseline"][0],r["result"]["draw"])["exact"] for r in settled)
        report.append(f"| {g['name']} | {len(settled)} | {len(settled)} | {hits('model')} | {len(settled)} | {hits('random')} |")
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
