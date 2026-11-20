"""Stress-test VAL's full Any Order predictor against mock lottery machines.

The virtual apparatus generates digit draws from known mechanisms. Ball-set
identities and pretest results remain hidden from the prediction model.
The simulator is NOT an exact replica of Virginia Lottery hardware.

Main null: 40,000 never-seen fair draws per game, all scored; fair-null
probabilities are 3*(width!)/10**width for three unique all-distinct tickets.
Other scenarios: 6,000 never-seen targets per game, with full Box tickets
sampled every 100 draws to bound compute; the prequential likelihood
is evaluated on ALL held-out draws, with no future outcomes in the model.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_virtual_draw_lab import SCENARIOS, simulate
from research_box_challenger import virtual_truth_mass
from val_box import box_ways, random_box_picks
from val_box_challenger import BoxEvidence, GAMES, grade_box

VERSION = "val_mock_box_stress_v1"
TRAIN = 800
FAIR_TEST = 40000
CHALLENGE_TEST = 6000
BIAS_SAMPLE_STRIDE = 100
SEED = 272106
OUT = Path("reports/research_mock_box_stress.json")
MD = Path("reports/research_mock_box_stress.md")


def null_probability(game):
    return 3 * math.factorial(int(game[-1])) / (10 ** int(game[-1]))


def run_case(game, scenario, train=TRAIN, test=None, replicate=SEED, stride=None):
    if game not in GAMES or scenario not in SCENARIOS:
        raise ValueError("Invalid game/scenario")
    if train < 200:
        raise ValueError("Insufficient warmup")
    test = test if test is not None else (
        FAIR_TEST if scenario == "fair_independent" else CHALLENGE_TEST)
    stride = stride if stride is not None else (
        1 if scenario == "fair_independent" else BIAS_SAMPLE_STRIDE)
    if test < 1 or stride < 1:
        raise ValueError("Invalid experiment count")

    # The actual rows are generated FIRST, entirely independently of both
    # candidate and random-control generators. They are revealed one by one.
    rows = simulate(game, scenario, train + test, replicate)
    model = BoxEvidence(game)
    model_rng = random.Random((replicate ^ 0x89b198e3) + int(game[-1]) * 911)
    control_rng = random.Random((replicate ^ 0xc177047d) + int(game[-1]) * 997)
    counters = Counter()
    accuracy_log_gain = 0.
    first_active = None
    sample_pairs = []
    for i, draw in enumerate(rows):
        if i >= train:
            selected, forecast = model.prediction(draw["stream"])
            counters["draws_evaluated"] += 1
            accuracy_log_gain += model.log_gain(draw, selected)
            if selected is not None:
                counters["active_draws"] += 1
                counters["expert_" + selected] += 1
                if first_active is None:
                    first_active = i - train

            if (i - train) % stride == 0:
                # For a same-cost, same-draw comparison each gets 3 complete
                # legal Box tickets. Never optimize the control after outcome.
                asserted, picks = model.picks(draw["stream"], model_rng)
                if selected != asserted:
                    raise AssertionError("Prediction state changed")
                controls = random_box_picks(game, 3, control_rng)
                candidate = grade_box(picks, draw["numbers"])
                baseline = grade_box(controls, draw["numbers"])
                counters["evaluated_box_draws"] += 1
                counters["candidate_box_wins"] += candidate
                counters["control_box_wins"] += baseline
                counters["model_only"] += int(candidate and not baseline)
                counters["control_only"] += int(baseline and not candidate)
                counters["both"] += int(candidate and baseline)
                counters["candidate_fair_expected"] += sum(
                    box_ways(t["numbers"]) / (10 ** int(game[-1]))
                    for t in picks)
                counters["control_fair_expected"] += sum(
                    box_ways(t["numbers"]) / (10 ** int(game[-1]))
                    for t in controls)
                # Oracle is used for evaluation only. It never enters the
                # deployed predictor or mock-ticket selection.
                counters["candidate_true_expected"] += virtual_truth_mass(
                    game, scenario, draw, i / len(rows), picks)
                counters["control_true_expected"] += virtual_truth_mass(
                    game, scenario, draw, i / len(rows), controls)
                sample_pairs.append(candidate - baseline)
        model.observe(draw)
    n = counters["evaluated_box_draws"]
    discordant = counters["model_only"] + counters["control_only"]
    observed_diff = (counters["candidate_box_wins"] -
                     counters["control_box_wins"]) / n
    # Independent-draw normal approximation: informative for large n; the
    # other simulated scenarios may share a hidden machine within a day.
    se = math.sqrt(max(0., (discordant / n - observed_diff ** 2) / n))
    return {
        "game": game, "scenario": scenario,
        "total_simulated_draws": len(rows),
        "training_draws": train,
        "held_out_draws": test,
        "sample_stride": stride,
        "box_target_draws": n,
        "paper_tickets_per_method_per_target": 3,
        "null_full_box_rate_for_3_distinct_sets": null_probability(game),
        "candidate_full_box_wins": counters["candidate_box_wins"],
        "random_full_box_wins": counters["control_box_wins"],
        "candidate_full_box_rate": counters["candidate_box_wins"] / n,
        "random_full_box_rate": counters["control_box_wins"] / n,
        "candidate_minus_random_rate": observed_diff,
        "paired_rate_interval_95_approx": [
            observed_diff - 1.96 * se, observed_diff + 1.96 * se],
        "model_only": counters["model_only"],
        "control_only": counters["control_only"],
        "both": counters["both"],
        "candidate_fair_expected_wins": counters["candidate_fair_expected"],
        "random_fair_expected_wins": counters["control_fair_expected"],
        "candidate_true_expected_wins": counters["candidate_true_expected"],
        "random_true_expected_wins": counters["control_true_expected"],
        "gate_active_targets": counters["active_draws"],
        "first_gate_activation_heldout_index": first_active,
        "active_expert_counts": {
            name.removeprefix("expert_"): value
            for name, value in counters.items() if name.startswith("expert_")},
        "mean_prequential_log_gain_vs_fair": accuracy_log_gain / test,
        "final_log_e": dict(model.log_e),
        "simulator_not_physical_replica": True,
    }


def table(data):
    lines = [
        "# VAL mock-lottery full Box stress test",
        "",
        "Simulates hidden-machine digit drawing conditions using the repository's",
        "existing virtual drawing machine. This is **not** a faithful",
        "physical replica or evidence of machine bias in Virginia.",
        "",
        "Only complete Any Order multisets count as wins, preserving repeats.",
        "Three independent $1 paper Box combinations for each method and target.",
        "No purchases. No future draw is available when its selection is made.",
        "",
        "Fair scenario evaluates every held-out drawing. Biased scenarios",
        "forecast every draw but sample Box tickets at the fixed stride;",
        "their observed Box wins are too sparse for reliable superiority claims.",
        "",
        "| Game | Injected mechanism | Held-out draws | Box trials | VAL Box wins | Random Box wins | VAL *true* expected wins | Random *true* expected wins | Active draws | Log gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for game, scenarios in data["games"].items():
        for label, r in scenarios.items():
            lines.append(
                f'| {game} | {label} | {r["held_out_draws"]:,} | '
                f'{r["box_target_draws"]:,} | {r["candidate_full_box_wins"]} | '
                f'{r["random_full_box_wins"]} | '
                f'{r["candidate_true_expected_wins"]:.2f} | '
                f'{r["random_true_expected_wins"]:.2f} | '
                f'{r["gate_active_targets"]:,} | '
                f'{r["mean_prequential_log_gain_vs_fair"]:+.6f} |')
    lines += [
        "",
        "## Fair generator: maximum-coverage three-Box baseline",
        "",
        "| Game | Expected full Box matches in 40,000 draws | VAL observed | Random observed | VAL minus random (percentage points) | Approx paired 95% range (points) |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for game, r in data["games"].items():
        s = r["fair_independent"]
        ci = s["paired_rate_interval_95_approx"]
        lines.append(
            f'| {game} | {s["box_target_draws"]*s["null_full_box_rate_for_3_distinct_sets"]:.1f} | '
            f'{s["candidate_full_box_wins"]} | {s["random_full_box_wins"]} | '
            f'{100*s["candidate_minus_random_rate"]:+.3f} | '
            f'[{100*ci[0]:+.3f}, {100*ci[1]:+.3f}] |')
    lines += [
        "",
        "## Interpretation",
        "",
        "Only the fair scenario is sized to evaluate stable hit-rate estimates.",
        "Even with a known injected statistical bias, observed Box wins in the",
        "small sampled biased scenario can deviate greatly from expected wins.",
        "The known-mechanism *true expected wins* measure whether the model",
        "actually selected higher-probability Box outcomes under simulation.",
        "Those oracles are strictly post-prediction diagnostics.",
        "",
        "This mock draw cannot demonstrate that real Virginia drawings",
        "are predictable. An exploitable real-world claim needs frozen",
        "prospective results that beat fair/random on full Box outcomes.",
        "",
        "[Machine-readable results](research_mock_box_stress.json).",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fair-test", type=int, default=FAIR_TEST)
    ap.add_argument("--other-test", type=int, default=CHALLENGE_TEST)
    ap.add_argument("--bias-stride", type=int, default=BIAS_SAMPLE_STRIDE)
    ap.add_argument("--games", nargs="+", choices=GAMES, default=GAMES)
    ap.add_argument("--scenarios", nargs="+", choices=SCENARIOS, default=SCENARIOS)
    args = ap.parse_args()
    data = {
        "version": VERSION,
        "seed": SEED,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "unseen_virtual_outcomes_only": True,
        "all_results_synthetic": True,
        "games": {},
    }
    for game in args.games:
        data["games"][game] = {}
        for scenario in args.scenarios:
            fair = scenario == "fair_independent"
            d = run_case(game, scenario,
                         test=args.fair_test if fair else args.other_test,
                         stride=1 if fair else args.bias_stride)
            data["games"][game][scenario] = d
            print(json.dumps({
                "game": game, "scenario": scenario,
                "held_out": d["held_out_draws"],
                "box_trials": d["box_target_draws"],
                "val_box_wins": d["candidate_full_box_wins"],
                "random_box_wins": d["random_full_box_wins"],
                "expected_val": round(d["candidate_true_expected_wins"], 3),
                "expected_random": round(d["random_true_expected_wins"], 3),
                "active": d["gate_active_targets"],
                "log_gain": round(d["mean_prequential_log_gain_vs_fair"], 5),
            }), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    MD.write_text(table(data))
    print("Saved", OUT, MD, flush=True)


if __name__ == "__main__":
    main()
