"""Retest the tuned ultimate generator two tougher ways, on real Pick 3/4 results.

1. Rolling rounds: for each test period, re-tune using ONLY drawings before
   it, then score the new tuned weights on that period it never saw.
2. Steadiness: the weights tuned on pre-2016 drawings (the original test),
   scored separately on each stretch of 2016-now. A real pattern should beat
   luck in most stretches, not in one lucky one.

Research only: the live picks are unchanged.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from research_player_methods import poisson_upper
from research_tuned_ultimate import SOURCES, SOURCE_LABELS, features, hits_for, tune
from val import GAMES, Store, sync_game
from val_box import box_ways
from val_ultimate import HOT_WINDOW

GAMES_TESTED = ("pick3", "pick4")
ROUNDS = (("2001", "2005"), ("2006", "2010"), ("2011", "2015"), ("2016", "2020"), ("2021", "2026"))
STRETCHES = (("2016", "2018"), ("2019", "2021"), ("2022", "2024"), ("2025", "2026"))


def span(dates, first, last):
    idx = [k for k, d in enumerate(dates) if first <= d[:4] <= last]
    return (idx[0], idx[-1] + 1) if idx else (None, None)


def evaluate(game, history):
    width = GAMES[game]["size"]
    votes, tiebreak, target = features(history, width)
    dates = [r["at"][:10] for r in history[HOT_WINDOW:]]
    p = box_ways(list(range(width))) / 10 ** width
    rounds = []
    for first, last in ROUNDS:
        a, b = span(dates, first, last)
        if a is None or a < 1000:
            continue
        best, _, _ = tune(votes[:a], tiebreak[:a], target[:a], width)
        hits = int(hits_for(best[None], votes[a:b], tiebreak[a:b], target[a:b], width)[0])
        rounds.append(dict(tuned_before=first, test=f"{first}–{last}", draws=b - a, hits=hits, luck=(b - a) * p,
                           weights={SOURCE_LABELS[s]: int(w) for s, w in zip(SOURCES, best)}))
    a0, _ = span(dates, "2016", "2026")
    original, _, _ = tune(votes[:a0], tiebreak[:a0], target[:a0], width)
    stretches = []
    for first, last in STRETCHES:
        a, b = span(dates, first, last)
        if a is None:
            continue
        hits = int(hits_for(original[None], votes[a:b], tiebreak[a:b], target[a:b], width)[0])
        stretches.append(dict(test=f"{first}–{last}", draws=b - a, hits=hits, luck=(b - a) * p))
    total_hits = sum(r["hits"] for r in rounds)
    total_luck = sum(r["luck"] for r in rounds)
    return dict(game=game, rounds=rounds, stretches=stretches, total_hits=total_hits, total_luck=total_luck,
                luck_chance=min(1.0, poisson_upper(total_luck, total_hits) * len(GAMES_TESTED)),
                rounds_beating_luck=sum(r["hits"] > r["luck"] for r in rounds),
                stretches_beating_luck=sum(s["hits"] > s["luck"] for s in stretches))


def markdown(rows, generated):
    lines = ["# Tuned ultimate generator — retest", "", f"Generated: {generated}", "",
             "**Part 1, rolling rounds:** each round re-tunes using only drawings before the test years, then "
             "scores the tuned version on those years. **Part 2, steadiness:** the version tuned before 2016 "
             "(the one that looked a little good on Pick 4) is checked on each stretch of 2016–now separately. "
             "\"Luck would give\" is what any all-different-digit pick gets by chance. Real results only.", ""]
    for r in rows:
        name = GAMES[r["game"]]["name"]
        lines += [f"## {name}", "", "| Round: tested on | Drawings | Tuned hits | Luck would give | Beat luck? |",
                  "| --- | ---: | ---: | ---: | --- |"]
        for x in r["rounds"]:
            lines.append(f"| {x['test']} | {x['draws']:,} | {x['hits']} | {x['luck']:.1f} | "
                         f"{'Yes' if x['hits'] > x['luck'] else 'No'} |")
        lines += [f"| **All rounds** | | **{r['total_hits']}** | **{r['total_luck']:.1f}** | "
                  f"{r['rounds_beating_luck']} of {len(r['rounds'])} rounds |", "",
                  "| Pre-2016 version, stretch | Drawings | Hits | Luck would give | Beat luck? |",
                  "| --- | ---: | ---: | ---: | --- |"]
        for x in r["stretches"]:
            lines.append(f"| {x['test']} | {x['draws']:,} | {x['hits']} | {x['luck']:.1f} | "
                         f"{'Yes' if x['hits'] > x['luck'] else 'No'} |")
        lines.append("")
    lines += ["## Bottom line", ""]
    for r in rows:
        name = GAMES[r["game"]]["name"]
        if r["luck_chance"] < 0.05:
            lines.append(f"- {name}: beat luck across the rounds. Worth tracking live.")
        else:
            lines.append(f"- {name}: {r['total_hits']} hits vs {r['total_luck']:.1f} from luck across all rounds. "
                         f"Same as luck.")
    lines += ["", "Research only. No tickets are bought and the live picks are unchanged.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="val-retest-") as directory:
        store = Store(Path(directory) / "val.sqlite3")
        for game in GAMES_TESTED:
            sync_game(store, game)
            history = [r for r in store.history(game)
                       if datetime.fromisoformat(r["at"]) <= datetime.now(timezone.utc)]
            rows.append(evaluate(game, history))
            print(game, "done", flush=True)
    generated = datetime.now(timezone.utc).isoformat()
    (out / "research_tuned_retest.json").write_text(json.dumps(dict(generated_at=generated, rows=rows), indent=2) + "\n")
    (out / "research_tuned_retest.md").write_text(markdown(rows, generated))
    print(markdown(rows, generated))


if __name__ == "__main__":
    main()
