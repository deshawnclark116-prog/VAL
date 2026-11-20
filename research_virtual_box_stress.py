"""High-volume complete-Box validation on VAL's virtual drawing machines.

Unlike the old sparse lab, this scores EVERY mock drawing in the test window.
At the start of each block, generate genuine live Box v3 predictions,
evidence-challenger picks and equal-cost fair controls. Freeze all three
portfolios, grade on the *later* block, and update training only after each
simulated result has been graded. No outcomes enter their own forecasts.

Research only. The simulator uses synthetic hypothetical biases; its device
identifiers and pretests are NOT supplied to predictors. Passing these tests
cannot establish an exploitable bias in Virginia's actual drawings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

from research_virtual_draw_lab import SCENARIOS, simulate
from val_box import box_ways, random_box_picks
from val_box_challenger import BoxEvidence, GAMES, grade_box
from val_digit_formula_v2 import generate_picks

VERSION = "virtual_box_stress_v1"
TRAIN = 850
TEST = 650
BLOCK = 260
TRIALS = 8
FIRST_REPLICATE = 100
OUTPUT = Path("reports/research_virtual_box_stress.json")
MARKDOWN = Path("reports/research_virtual_box_stress.md")
METHODS = ("challenger", "production_v3", "random")


def seeded(*parts):
    raw = "|".join(map(str, [VERSION] + list(parts))).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8], "big"))


def fair_coverage(picks, width):
    unique = {tuple(sorted(p["numbers"])): box_ways(p["numbers"])
              for p in picks}
    return sum(unique.values()) / (10 ** width)


def run_single(game, scenario, replicate, train=TRAIN, test=TEST, block=BLOCK):
    rows = simulate(game, scenario, train + test, replicate)
    machine = BoxEvidence(game)
    width = int(game[-1])
    chosen = None
    coverages = None
    signal = None
    wins = {key: 0 for key in METHODS}
    expected = {key: 0. for key in METHODS}
    active_draws = active_blocks = 0
    blocks = 0
    for i, draw in enumerate(rows):
        if i >= train:
            if (i - train) % block == 0:
                selected_by_stream = {}
                cover_by_stream = {}
                active_by_stream = {}
                for stream in ("Day", "Night"):
                    rng_token = (game, scenario, replicate, i, stream)
                    signal, contender = machine.picks(
                        stream, seeded("challenger", *rng_token), 3)
                    incumbent, _ = generate_picks(
                        game, rows[:i], stream, 3,
                        rng=seeded("production", *rng_token))
                    controls = random_box_picks(
                        game, 3, seeded("fair", *rng_token))
                    selected_by_stream[stream] = {
                        "challenger": contender,
                        "production_v3": incumbent,
                        "random": controls}
                    cover_by_stream[stream] = {
                        name: fair_coverage(picks, width)
                        for name, picks in selected_by_stream[stream].items()}
                    active_by_stream[stream] = signal is not None
                    assert len({tuple(sorted(p["numbers"]))
                                for p in controls}) == 3
                    assert all(len(x) == 3
                               for x in selected_by_stream[stream].values())
                active_blocks += int(any(active_by_stream.values()))
                blocks += 1

            # Same three frozen tickets for every same-stream draw in a
            # block; both session portfolios were fixed BEFORE the block.
            chosen = selected_by_stream[draw["stream"]]
            coverages = cover_by_stream[draw["stream"]]
            for name, picks in chosen.items():
                wins[name] += grade_box(picks, draw["numbers"])
                expected[name] += coverages[name]
            active_draws += active_by_stream[draw["stream"]]
        machine.observe(draw)

    return {"replicate": replicate, "draws": test, "blocks": blocks,
            "active_blocks": active_blocks, "active_draws": active_draws,
            "box_wins": wins,
            "fair_expected_box_wins": expected}


def aggregate(samples):
    draws = sum(s["draws"] for s in samples)
    box = {name: sum(s["box_wins"][name] for s in samples)
           for name in METHODS}
    expected = {name: sum(s["fair_expected_box_wins"][name] for s in samples)
                for name in METHODS}
    # Paired comparison: same simulated drawings, same 3 tickets per draw.
    differences = [s["box_wins"]["challenger"] - s["box_wins"]["random"]
                   for s in samples]
    n = len(differences)
    dmean = sum(differences) / n
    sem = (math.sqrt(sum((x - dmean) ** 2 for x in differences)
                     / (n - 1) / n) if n > 1 else float("inf"))
    return {"draws": draws, "trials": n,
            "ticket_budget_each_method": draws * 3,
            "box_wins": box,
            "box_rate_per_draw": {name: box[name] / draws for name in METHODS},
            "fair_expected_box_wins": expected,
            "active_blocks": sum(s["active_blocks"] for s in samples),
            "total_blocks": sum(s["blocks"] for s in samples),
            "active_draws": sum(s["active_draws"] for s in samples),
            "paired_win_difference_challenger_minus_random": (
                box["challenger"] - box["random"]),
            "paired_replication_95pct_approx_interval_for_total_difference": [
                (dmean - 1.96 * sem) * n,
                (dmean + 1.96 * sem) * n,
            ],
            "per_replicate": samples}


def report(data):
    lines = [
        "# VAL high-volume virtual-draw COMPLETE Box test", "",
        f'{data["trials"]} independent synthetic trials per game/scenario,',
        f'{data["train_draws"]} historical virtual training results,',
        f'{data["test_draws"]} scored future virtual results per trial.',
        f'Tickets are frozen every {data["block_draws"]} results, then',
        "graded against each subsequent drawing in the block.",
        "Each model has three distinct Box tickets for each drawing.",
        "The random, incumbent Box v3 and challenger portfolios are",
        "selected before the block and compared on identical outcomes.",
        "",
        "**Primary metric: full Any Order digits, including repeated digits.**",
        "Correct-position or partial-digit matches are never credited.",
        "No actual Virginia Lottery edge is established by this synthetic test.",
        "",
        "| Game | Simulated mechanism | Target draws | Challenger Box wins | Live v3 Box wins | Random Box wins | Fair expected (candidate) | Challenger active blocks |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for game, scenarios in data["games"].items():
        for name, x in scenarios.items():
            lines.append(
                f'| {game} | {name} | {x["draws"]} | '
                f'{x["box_wins"]["challenger"]} | '
                f'{x["box_wins"]["production_v3"]} | '
                f'{x["box_wins"]["random"]} | '
                f'{x["fair_expected_box_wins"]["challenger"]:.1f} | '
                f'{x["active_blocks"]}/{x["total_blocks"]} |'
            )
    lines += [
        "", "## Interpretation", "",
        "A fair iid drawing gives no predictor a dependable edge.",
        "Synthetic biases test detection capability, not real-world advantage.",
        "The frozen deployment blocks differ from refresh-on-every-draw;",
        "forecasts for both Day and Night are frozen before each block.",
        "Real-world validation requires prospectively saved real outcomes.",
        "", "[Raw results](research_virtual_box_stress.json).", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--train", type=int, default=TRAIN)
    parser.add_argument("--test", type=int, default=TEST)
    parser.add_argument("--block", type=int, default=BLOCK)
    args = parser.parse_args()
    if not (1 <= args.trials <= 64 and 200 <= args.train and
            1 <= args.block <= args.test):
        raise ValueError("Invalid stress experiment dimensions")
    out = {"version": VERSION, "generated_utc": datetime.now(timezone.utc).isoformat(),
           "trials": args.trials, "train_draws": args.train,
           "test_draws": args.test, "block_draws": args.block,
           "reference_simulation": "research_virtual_draw_lab.simulate",
           "trials_preselected": list(range(FIRST_REPLICATE,
                                             FIRST_REPLICATE + args.trials)),
           "synthetic_only": True, "production_changes": False, "games": {}}
    for game in GAMES:
        out["games"][game] = {}
        for scenario in SCENARIOS:
            samples = []
            for rep in range(FIRST_REPLICATE,
                             FIRST_REPLICATE + args.trials):
                samples.append(run_single(
                    game, scenario, rep, args.train, args.test, args.block))
                if len(samples) % 4 == 0:
                    print(game, scenario, "trials", len(samples), "of",
                          args.trials, flush=True)
            out["games"][game][scenario] = aggregate(samples)
            x = out["games"][game][scenario]
            print("RESULT", game, scenario, x["box_wins"],
                  "expected", x["fair_expected_box_wins"]["challenger"],
                  "signal", x["active_blocks"], "/", x["total_blocks"],
                  flush=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n")
    MARKDOWN.write_text(report(out) + "\n")
    print("Saved", OUTPUT, MARKDOWN, flush=True)


if __name__ == "__main__":
    main()
