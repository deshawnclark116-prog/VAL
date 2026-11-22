"""Historical test of popular player "adding" methods on REAL Pick 3/4/5 results.

Every method makes one pick before each real past drawing, using only the
drawings that came before it (all sessions, in time order). Each pick is scored
against the real winning number as:

* Straight: exact digits in exact order.
* Box (Any Order): all digits, any order (picks with no Box play don't count).

The yardstick is the fair math: how many hits any pick would get by luck,
plus an independent random pick for every drawing. A method only "beats luck"
if it hits clearly more often than both, after adjusting for the number of
methods tested at once.

Research only: it does not change the live picks or the ledger.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from val import GAMES, Store, sync_game
from val_box import fair_any_order_probability, is_any_order_win
from val_luck import one_in
from val_player_methods import METHODS, player_pick
from val_ultimate import HOT_WINDOW, LABEL as ULTIMATE_LABEL, VERSION as ULTIMATE_VERSION, ultimate_digit_pick

DIGIT_GAMES = ("pick3", "pick4", "pick5")
SEED = 20261122
SIGNIFICANCE = 0.05


def poisson_upper(expected, hits):
    """P(at least `hits`) for a count with this expected value (rare-event approximation)."""
    if hits <= 0:
        return 1.0
    if expected <= 0:
        return 0.0
    below = sum(math.exp(k * math.log(expected) - expected - math.lgamma(k + 1)) for k in range(hits))
    return min(1.0, max(0.0, 1.0 - below))


def evaluate(game, history, seed=SEED):
    """Walk forward through real history; return one summary row per method."""
    width = GAMES[game]["size"]
    rng = random.Random(f"{seed}:{game}")
    rows = {m: dict(game=game, method=m, label=label, draws=0, box_hits=0, box_expected=0.0,
                    straight_hits=0, straight_expected=0.0, random_box_hits=0)
            for m, label in {**METHODS, ULTIMATE_VERSION: ULTIMATE_LABEL}.items()}
    for i in range(width, len(history)):
        past, actual = history[i - width:i], history[i]["numbers"]  # methods only use the last few results
        control = [rng.randrange(10) for _ in range(width)]
        control_box_win = is_any_order_win(game, control, actual)
        for method, row in rows.items():
            if method == ULTIMATE_VERSION:
                pick = ultimate_digit_pick(history[max(0, i - HOT_WINDOW):i], width)["numbers"]
            else:
                pick = player_pick(method, past, width)["numbers"]
            row["draws"] += 1
            row["straight_hits"] += pick == list(actual)
            row["straight_expected"] += 10 ** -width
            row["box_hits"] += is_any_order_win(game, pick, actual)
            row["box_expected"] += fair_any_order_probability(game, pick)
            row["random_box_hits"] += control_box_win
    out = list(rows.values())
    for row in out:
        if history:
            row["first_draw"] = history[width]["at"] if len(history) > width else None
            row["last_draw"] = history[-1]["at"]
    return out


def judge(rows):
    """Add luck chances, adjusted for every method x game x bet type tested."""
    tests = max(1, 2 * len(rows))
    for row in rows:
        for kind in ("box", "straight"):
            hits, expected = row[f"{kind}_hits"], row[f"{kind}_expected"]
            chance = poisson_upper(expected, hits)
            row[f"{kind}_ratio"] = hits / expected if expected else None
            row[f"{kind}_luck_chance"] = chance
            row[f"{kind}_adjusted_chance"] = min(1.0, chance * tests)
        best = min(row["box_adjusted_chance"], row["straight_adjusted_chance"])
        if best < SIGNIFICANCE:
            row["verdict"] = "Hit more than luck would explain in the past. Needs future draws to confirm."
        elif max(row["box_ratio"] or 0, row["straight_ratio"] or 0) >= 1:
            row["verdict"] = "About the same as luck."
        else:
            row["verdict"] = "About the same as luck, or a bit worse."
    return rows


def ratio_text(ratio):
    return "—" if ratio is None else f"{ratio:.2f}×"


def markdown(rows, generated):
    tests = 2 * len(rows)
    lines = [
        "# Popular player methods — tested on real past results", "",
        f"Generated: {generated}", "",
        "Each method made one pick before every real Pick 3, Pick 4 and Pick 5 drawing in the official "
        "history, using only the drawings before it. **No fake or simulated numbers are used.** "
        "Each pick is checked against the real winning number.", "",
        "**How to read this:** \"Luck would give\" is how many hits ANY pick gets on average by pure chance. "
        "\"Hit rate vs luck\" of 1.00× means exactly as good as luck; 2.00× would mean twice as good. "
        "The random pick column is a second yardstick: a pick made with no system at all for every drawing. "
        f"Because {tests} things were checked at once, the luck chance is adjusted upward so a fluke "
        "doesn't look like a discovery.", "",
        "| Game | Method | Drawings tested | Box hits | Luck would give | Random-pick Box hits | Box hit rate vs luck | "
        "Straight hits | Luck would give | Straight hit rate vs luck | Verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {GAMES[r['game']]['name']} | {r['label']} | {r['draws']:,} | {r['box_hits']:,} | "
            f"{r['box_expected']:.1f} | {r['random_box_hits']:,} | {ratio_text(r['box_ratio'])} | "
            f"{r['straight_hits']:,} | {r['straight_expected']:.1f} | {ratio_text(r['straight_ratio'])} | "
            f"{r['verdict']} |")
    flagged = [r for r in rows if min(r["box_adjusted_chance"], r["straight_adjusted_chance"]) < SIGNIFICANCE]
    lines += ["", "## Bottom line", ""]
    if flagged:
        lines.append("Some methods hit more than luck would explain in the past. That still needs to hold up on "
                     "future drawings, which the live bot now tracks, before it means anything.")
        for r in flagged:
            chance = min(r["box_adjusted_chance"], r["straight_adjusted_chance"])
            lines.append(f"- {GAMES[r['game']]['name']}, {r['label']}: chance of this by luck {one_in(chance)}.")
    else:
        lines.append("None of the methods hit more often than luck. Their results look just like picking numbers "
                     "at random.")
    lines += ["", "Some methods often produce repeated digits (like 4 4 7). Those have fewer ways to win Box, so "
              "\"Luck would give\" is lower for them. That's already accounted for. Straight odds are the same for "
              "every pick.", "", "Research only. No tickets are bought and the live picks are unchanged.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="val-player-") as directory:
        store = Store(Path(directory) / "val.sqlite3")
        for game in DIGIT_GAMES:
            sync_game(store, game)
            history = [r for r in store.history(game)
                       if datetime.fromisoformat(r["at"]) <= datetime.now(timezone.utc)]
            if len(history) < 100:
                raise SystemExit(f"{game}: only {len(history)} real results downloaded")
            rows += evaluate(game, history)
    rows = judge(rows)
    generated = datetime.now(timezone.utc).isoformat()
    (out / "research_player_methods.json").write_text(
        json.dumps(dict(generated_at=generated, seed=SEED, rows=rows), indent=2) + "\n")
    (out / "research_player_methods.md").write_text(markdown(rows, generated))
    print(markdown(rows, generated))


if __name__ == "__main__":
    main()
