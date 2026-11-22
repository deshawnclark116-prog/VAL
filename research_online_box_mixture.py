"""Prequential full-Box comparison. Research only; never edits frozen forecasts.

Run: python research_online_box_mixture.py --mode real
     python research_online_box_mixture.py --mode synthetic
Real 2025/26 drawings have been repeatedly inspected: exploratory, NOT holdout.
"""
import argparse
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from val_online_box_mixture import OnlineBoxMixture
from val_box import digits_key, box_ways
from research_decades import fetch_full

GAMES = ("pick3", "pick4", "pick5")
OUTPUT = Path("reports/research_online_box_mixture.json")
TICKETS = 3


def fair_mass(game, key):
    return box_ways(key) / 10 ** int(game[-1])


def synthetic(game, mechanism, seed, n=1800):
    rng = random.Random(seed)
    width = int(game[-1])
    favored = list(range(width))
    rows = []
    for i in range(n):
        draw = [rng.randrange(10) for _ in range(width)]
        if mechanism == "injected_box" and rng.random() < .06:
            draw = favored[:]
            rng.shuffle(draw)
        rows.append({"numbers": draw, "date": f"synthetic-{i//2:05d}",
                     "stream": "Day" if i % 2 == 0 else "Night"})
    return rows


def evaluate(game, rows, start):
    model = OnlineBoxMixture(game)
    stats = defaultdict(lambda: {"wins": 0, "fair_expected_wins": 0.,
                                  "log_gain": 0., "brier_delta": 0.})
    # Fair comparator is a fixed, deterministic, distinct all-unique Box
    # portfolio, whose chance is the same as any other three such tickets.
    fair_tickets = [tuple(range(i, i + int(game[-1])))
                    for i in range(TICKETS)]
    fair_keys = {digits_key(t) for t in fair_tickets}
    n = 0
    for i, row in enumerate(rows):
        if i >= start:
            forecast = model.predict(TICKETS)
            actual = digits_key(row["numbers"])
            q = fair_mass(game, actual)
            p = forecast["distribution"][actual]
            predicted = {digits_key(t) for t in forecast["picks"]}
            for name, keys in (("mixture", predicted), ("fair_portfolio", fair_keys)):
                s = stats[name]
                s["wins"] += int(actual in keys)
                s["fair_expected_wins"] += sum(fair_mass(game, k) for k in keys)
            stats["mixture"]["log_gain"] += math.log(p / q)
            # Multiclass Brier improvement vs fair distribution, using the
            # identity sum(p^2-q^2)-2(p_actual-q_actual).
            dist = forecast["distribution"]
            stats["mixture"]["brier_delta"] += (
                sum(v*v - fair_mass(game, k)**2 for k,v in dist.items())
                - 2*(p-q))
            n += 1
        model.observe(row)  # strictly after forecasting and scoring
    return {"targets": n, "methods": {
        name: {**s, "win_rate": s["wins"]/n,
               "fair_expected_win_rate": s["fair_expected_wins"]/n,
               "mean_log_gain": s["log_gain"]/n,
               "mean_brier_delta": s["brier_delta"]/n}
        for name,s in stats.items()}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("real", "synthetic"), required=True)
    args = parser.parse_args()
    output = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "research_only": True, "real_independent_holdout": False,
              "mode": args.mode, "results": {}}
    for game in GAMES:
        if args.mode == "real":
            rows, _ = fetch_full(game)
            rows = sorted(rows, key=lambda r: (r["date"], r["stream"] != "Day"))
            start = next((i for i,r in enumerate(rows)
                          if r["date"][:4] >= "2025" and i >= 500), len(rows))
            output["results"][game] = evaluate(game, rows, start)
        else:
            output["results"][game] = {
                mechanism: evaluate(game, synthetic(game, mechanism, 431),
                                    1000)
                for mechanism in ("fair", "injected_box")}
        print(game, json.dumps(output["results"][game]), flush=True)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print("SAVED", OUTPUT)


if __name__ == "__main__":
    main()
