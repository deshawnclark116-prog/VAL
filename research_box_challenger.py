"""Precommitted research comparison: evidence-gated Box vs live v3 vs fair.

Run:
    python -u research_box_challenger.py --mode virtual
    python -u research_box_challenger.py --mode real

This never writes live tickets or changes production. Real archives and
the development period have been inspected previously: all such results
are exploratory, not untouched confirmation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from val_box import box_ways, random_box_picks
from val_box_challenger import (BoxEvidence, EXPERTS, GAMES, LOG_GATE,
                                VERSION, grade_box)
from research_virtual_draw_lab import SCENARIOS, simulate

VIRTUAL_REPLICATES = 2
VIRTUAL_TRAIN = 850
VIRTUAL_TEST = 650
VIRTUAL_STRIDE = 25
REAL_TRAIN = 800
REAL_TEST = 1200
REAL_STRIDE = 30
ROOT = Path("reports")


def rng_for(*parts):
    label = "|".join(map(str, (VERSION,) + parts))
    seed = int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], "big")
    return random.Random(seed)


def initial():
    return {"draws": 0, "active_draws": 0, "active_experts": Counter(),
            "mean_log_gain_sum": 0., "ticket_trials": 0,
            "candidate_box_wins": 0, "control_box_wins": 0,
            "v3_box_wins": 0, "fair_expected_box_wins": 0.,
            "v3_fair_expected_box_wins": 0.}


def evaluate_sequence(game, rows, train, stride, real=False,
                      archive=None, archive_offset=0):
    """All updates are next-draw: score/select first, observe outcome second."""
    machine = BoxEvidence(game)
    metrics = initial()
    for i, row in enumerate(rows):
        if i >= train:
            selected, model = machine.prediction(row["stream"])
            metrics["draws"] += 1
            metrics["active_draws"] += int(selected is not None)
            if selected:
                metrics["active_experts"][selected] += 1
            metrics["mean_log_gain_sum"] += machine.log_gain(row, selected)
            if (i - train) % stride == 0:
                label = (game, row["at"])
                selected_check, picks = machine.picks(
                    row["stream"], rng_for("challenger", *label))
                if selected_check != selected:
                    raise AssertionError("Pre-draw challenger state changed")
                control = random_box_picks(
                    game, 3, rng_for("independent_control", *label))
                metrics["ticket_trials"] += 1
                metrics["candidate_box_wins"] += grade_box(picks, row["numbers"])
                metrics["control_box_wins"] += grade_box(control, row["numbers"])
                metrics["fair_expected_box_wins"] += sum(
                    box_ways(p["numbers"]) / (10 ** int(game[-1]))
                    for p in picks)
                if real:
                    from val_digit_formula_v2 import generate_picks
                    # Use the exact existing production generator for a
                    # same-target comparison. Rows preceding target ONLY.
                    v3, meta = generate_picks(
                        game, archive[:archive_offset + i] if archive is not None else rows[:i],
                        row["stream"], 3,
                        rng=rng_for("live_v3", *label))
                    metrics["v3_box_wins"] += grade_box(v3, row["numbers"])
                    metrics["v3_fair_expected_box_wins"] += sum(
                        box_ways(p["numbers"]) / (10 ** int(game[-1]))
                        for p in v3)
        machine.observe(row)
    n = metrics["draws"]
    if n:
        metrics["mean_log_gain_vs_fair"] = metrics.pop("mean_log_gain_sum") / n
    metrics["active_experts"] = dict(metrics["active_experts"])
    metrics["final_log_evidence"] = {
        name: round(machine.log_e[name], 5) for name in EXPERTS}
    return metrics


def run_virtual():
    out = {"version": VERSION, "source": "injected synthetic virtual draws",
           "synthetic_only": True, "gate_log_threshold": LOG_GATE, "games": {}}
    for game in GAMES:
        out["games"][game] = {}
        for scenario in SCENARIOS:
            total = initial()
            for rep in range(VIRTUAL_REPLICATES):
                rows = simulate(
                    game, scenario, VIRTUAL_TRAIN + VIRTUAL_TEST, rep)
                m = evaluate_sequence(
                    game, rows, VIRTUAL_TRAIN, VIRTUAL_STRIDE)
                for key in ("draws", "active_draws", "ticket_trials",
                            "candidate_box_wins", "control_box_wins"):
                    total[key] += m[key]
                total["mean_log_gain_sum"] += m["mean_log_gain_vs_fair"] * m["draws"]
                total["fair_expected_box_wins"] += m["fair_expected_box_wins"]
                total["active_experts"].update(m["active_experts"])
            total["mean_log_gain_vs_fair"] = (
                total.pop("mean_log_gain_sum") / total["draws"])
            total["active_experts"] = dict(total["active_experts"])
            del total["v3_box_wins"], total["v3_fair_expected_box_wins"]
            out["games"][game][scenario] = total
            print("Virtual", game, scenario, "active", total["active_draws"],
                  "Box", total["candidate_box_wins"], "vs",
                  total["control_box_wins"], flush=True)
    return out


def run_real():
    from research_10k import load_official_history
    out = {"version": VERSION, "source": "Virginia Lottery official archive",
           "previously_inspected_historical_data": True,
           "pristine_future_validation": False, "games": {}}
    for game in GAMES:
        history = load_official_history(game)
        subset = history[-(REAL_TRAIN + REAL_TEST):]
        stats = evaluate_sequence(
            game, subset, REAL_TRAIN, REAL_STRIDE, real=True,
            archive=history, archive_offset=len(history) - len(subset))
        stats["first_evaluated"] = subset[REAL_TRAIN]["at"]
        stats["last_evaluated"] = subset[-1]["at"]
        stats["official_history_draws"] = len(history)
        stats["initial_training_draws"] = REAL_TRAIN
        stats["evaluation_stride"] = REAL_STRIDE
        out["games"][game] = stats
        print("Real", game, "active", stats["active_draws"],
              "Box", stats["candidate_box_wins"],
              "v3", stats["v3_box_wins"],
              "fair", stats["control_box_wins"], flush=True)
    return out


def render(result):
    real = result.get("previously_inspected_historical_data", False)
    lines = ["# VAL cumulative-evidence Box challenger: " +
             ("real-draw replay" if real else "virtual-draw check"),
             "", "All wins require the COMPLETE digit multiset including repeats.",
             "Three paper Box tickets per sampled target, no purchases.",
             "Candidate evidence uses strictly earlier draws. It must cross",
             "a conservative anytime threshold against the iid uniform null.",
             "No production forecast or previously saved pick was modified.",
             ""]
    if real:
        lines += ["**Exploratory only: these historical outcomes were already",
                  "available during development. No genuine future edge is proven.**",
                  "", "| Game | Evaluated draws | Signal-active | Sampled targets |",
                  "Challenger Box | Live v3 Box | Independent random Box |",
                  "Candidate fair-expected Box | Challenger mean log gain |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for game, m in result["games"].items():
            lines.append(f'| {game} | {m["draws"]} | {m["active_draws"]} | '
                         f'{m["ticket_trials"]} | {m["candidate_box_wins"]} | '
                         f'{m["v3_box_wins"]} | {m["control_box_wins"]} | '
                         f'{m["fair_expected_box_wins"]:.3f} | '
                         f'{m["mean_log_gain_vs_fair"]:+.6f} |')
    else:
        lines += ["**These are simulated devices with injected distributions,",
                  "not evidence of exploitable Virginia Lottery machinery.**",
                  "", "| Game | Scenario | Signal-active draws | Box trial draws |",
                  "Challenger Box | Random Box | Challenger fair-expected Box |",
                  "Mean log gain |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for game, cases in result["games"].items():
            for scenario, m in cases.items():
                lines.append(f'| {game} | {scenario} | {m["active_draws"]} | '
                             f'{m["ticket_trials"]} | {m["candidate_box_wins"]} | '
                             f'{m["control_box_wins"]} | '
                             f'{m["fair_expected_box_wins"]:.3f} | '
                             f'{m["mean_log_gain_vs_fair"]:+.6f} |')
    lines += ["", "## Decision", "",
              "Only future, immutable predictions that demonstrate an actual",
              "full-Box edge and pass a precommitted statistical rule can",
              "justify promotion to production. False positive and false negative",
              "behavior in simulations is diagnostic, never proof of a live edge.",
              ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("real", "virtual"), required=True)
    args = parser.parse_args()
    result = run_real() if args.mode == "real" else run_virtual()
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / ("research_box_challenger_" + args.mode)
    path.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
    path.with_suffix(".md").write_text(render(result) + "\n")
    print("Saved", path, flush=True)


if __name__ == "__main__":
    main()
