"""Tune the ultimate generator on OLD real results, then test it on NEWER ones.

1. Training period (Pick 3/4: drawings before 2016; Pick 5, which only has
   history from 2023: its first 70%): try every weighting of the 7 vote
   sources (5 player methods, hot digits, due digits), each weight 0-3,
   16,383 combinations. Keep the one with the most Box hits.
2. Test period (the drawings after that): run ONLY that tuned weighting, and
   the untuned ultimate generator (all weights 1), on results never used to
   tune it. Compare with what luck gives.

All picks use only earlier drawings. Real official results only.
Research only: the live picks are unchanged.
"""
from __future__ import annotations

import argparse
import itertools
import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from research_player_methods import poisson_upper
from val import GAMES, Store, sync_game
from val_box import box_ways
from val_luck import one_in
from val_player_methods import METHODS, player_pick
from val_ultimate import HOT_WINDOW, LABEL

SOURCES = [*METHODS, "hot", "due"]
SOURCE_LABELS = {**METHODS, "hot": "Hot digits", "due": "Due digits"}
WEIGHTS = (0, 1, 2, 3)
SPLIT_DATE = "2016-01-01"
DIGIT_GAMES = ("pick3", "pick4", "pick5")


def features(history, width):
    """Per drawing: vote indicators (draws, sources, 10), tie-break counts, winning mask."""
    n = len(history) - HOT_WINDOW
    votes = np.zeros((n, len(SOURCES), 10))
    tiebreak = np.zeros((n, 10))
    target = np.full(n, -1, dtype=np.int64)
    for j, i in enumerate(range(HOT_WINDOW, len(history))):
        window = history[i - HOT_WINDOW:i]
        for s, method in enumerate(METHODS):
            for d in set(player_pick(method, window, width)["numbers"]):
                votes[j, s, d] = 1
        recent = Counter(d for r in window for d in r["numbers"])
        for d, _ in recent.most_common(width):
            votes[j, len(METHODS), d] = 1
        last_seen = {}
        for k, r in enumerate(window):
            for d in r["numbers"]:
                last_seen[d] = k
        for d in sorted(range(10), key=lambda d: last_seen.get(d, -1))[:width]:
            votes[j, len(METHODS) + 1, d] = 1
        # Same tie-break as val_ultimate: more recent appearances, then lower digit.
        tiebreak[j] = [recent[d] * 1e-3 - d * 1e-6 for d in range(10)]
        actual = history[i]["numbers"]
        if len(set(actual)) == width:
            target[j] = sum(1 << d for d in actual)
    return votes, tiebreak, target


def hits_for(weights, votes, tiebreak, target, width):
    """Box hits for each weighting (rows of `weights`)."""
    scores = np.einsum("ws,nsd->wnd", weights, votes) + tiebreak[None]
    top = np.argpartition(-scores, width - 1, axis=2)[:, :, :width]
    masks = (1 << top).sum(axis=2)
    return (masks == target[None]).sum(axis=1)


def all_weightings():
    grid = [w for w in itertools.product(WEIGHTS, repeat=len(SOURCES)) if any(w)]
    return np.array(grid, dtype=float)


def tune(votes, tiebreak, target, width, chunk=256):
    grid = all_weightings()
    best_hits, best = -1, None
    for start in range(0, len(grid), chunk):
        part = grid[start:start + chunk]
        hits = hits_for(part, votes, tiebreak, target, width)
        k = int(hits.argmax())
        if hits[k] > best_hits:
            best_hits, best = int(hits[k]), part[k]
    return best, best_hits, len(grid)


def split_index(history, width):
    dates = [r["at"][:10] for r in history[HOT_WINDOW:]]
    i = next((k for k, d in enumerate(dates) if d >= SPLIT_DATE), len(dates))
    if i < 1000 or len(dates) - i < 500:
        return int(len(dates) * 0.7), "first 70% of drawings"
    return i, f"drawings before {SPLIT_DATE[:4]}"


def evaluate(game, history):
    width = GAMES[game]["size"]
    votes, tiebreak, target = features(history, width)
    cut, rule = split_index(history, width)
    p = box_ways(list(range(width))) / 10 ** width      # every pick here has all-different digits
    train = (votes[:cut], tiebreak[:cut], target[:cut])
    test = (votes[cut:], tiebreak[cut:], target[cut:])
    best, train_hits, tried = tune(*train, width)
    test_tuned = int(hits_for(best[None], *test, width)[0])
    test_plain = int(hits_for(np.ones((1, len(SOURCES))), *test, width)[0])
    dated = history[HOT_WINDOW:]
    row = dict(
        game=game, rule=rule, weightings_tried=tried,
        best_weights={SOURCE_LABELS[s]: int(w) for s, w in zip(SOURCES, best)},
        train_draws=cut, train_from=dated[0]["at"][:10], train_to=dated[cut - 1]["at"][:10],
        train_hits=train_hits, train_luck=cut * p,
        test_draws=len(dated) - cut, test_from=dated[cut]["at"][:10], test_to=dated[-1]["at"][:10],
        test_tuned_hits=test_tuned, test_plain_hits=test_plain, test_luck=(len(dated) - cut) * p)
    row["test_luck_chance"] = min(1.0, poisson_upper(row["test_luck"], test_tuned) * len(DIGIT_GAMES))
    return row


def verdict(r):
    if r["test_luck_chance"] < 0.05:
        return "Kept hitting more than luck on new drawings. Worth watching live."
    if r["test_tuned_hits"] >= r["test_luck"]:
        return "Looked great on old drawings, then about the same as luck on new ones."
    return "Looked great on old drawings, then the same as luck or worse on new ones."


def markdown(rows, generated):
    lines = ["# Tuned ultimate generator — tuned on old results, tested on new ones", "",
             f"Generated: {generated}", "",
             "The computer tried every way of weighting the ultimate generator's 7 vote sources "
             "(5 methods, hot digits, due digits; each weight 0 to 3) on OLD real drawings and kept the one "
             "with the most Box hits. Then that tuned version was tested on NEWER real drawings it never saw. "
             "\"Luck would give\" is what any all-different-digit pick gets by pure chance.", "",
             "| Game | Tuned on | Ways tried | Old drawings: tuned hits | Old drawings: luck would give | "
             "New drawings tested | New: tuned hits | New: untuned ultimate hits | New: luck would give | Verdict |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for r in rows:
        lines.append(
            f"| {GAMES[r['game']]['name']} | {r['train_from'][:4]}–{r['train_to'][:4]} | {r['weightings_tried']:,} | "
            f"{r['train_hits']} | {r['train_luck']:.1f} | {r['test_draws']:,} ({r['test_from'][:4]}–{r['test_to'][:4]}) | "
            f"{r['test_tuned_hits']} | {r['test_plain_hits']} | {r['test_luck']:.1f} | {verdict(r)} |")
    lines += ["", "## Best weights found on old drawings", ""]
    for r in rows:
        w = ", ".join(f"{k} {v}" for k, v in r["best_weights"].items())
        lines.append(f"- {GAMES[r['game']]['name']}: {w}")
    lines += ["", "## Bottom line", ""]
    good = [r for r in rows if r["test_luck_chance"] < 0.05]
    if good:
        for r in good:
            lines.append(f"- {GAMES[r['game']]['name']}: kept beating luck on new drawings "
                         f"(chance by luck {one_in(r['test_luck_chance'])}). Next step: track it live.")
    else:
        lines.append("Tuning made the generator look better on the old drawings it was tuned on, but on new "
                     "drawings it went back to luck. The extra hits were the computer fitting the past, not "
                     "finding a pattern.")
    lines += ["", f"Untuned ultimate = the live \"{LABEL}\" with every source weighted 1.",
              "Research only. No tickets are bought and the live picks are unchanged.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="val-tuned-") as directory:
        store = Store(Path(directory) / "val.sqlite3")
        for game in DIGIT_GAMES:
            sync_game(store, game)
            history = [r for r in store.history(game)
                       if datetime.fromisoformat(r["at"]) <= datetime.now(timezone.utc)]
            if len(history) < 2000:
                raise SystemExit(f"{game}: only {len(history)} real results downloaded")
            rows.append(evaluate(game, history))
            print(game, "done", flush=True)
    generated = datetime.now(timezone.utc).isoformat()
    (out / "research_tuned_ultimate.json").write_text(
        json.dumps(dict(generated_at=generated, rows=rows), indent=2) + "\n")
    (out / "research_tuned_ultimate.md").write_text(markdown(rows, generated))
    print(markdown(rows, generated))


if __name__ == "__main__":
    main()
