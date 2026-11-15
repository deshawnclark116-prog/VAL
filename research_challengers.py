"""VAL challenger lab: strictly historical, leak-free comparisons.

Research-only. Does not alter live candidate generation, ranking, schedules,
or the permanent prospective ledger. Uses fixed method specifications and
10,000 tickets per method per digit game spread across real held-out draws.
The original previous 10k replay was already inspected; this is exploratory,
not an untouched confirmatory holdout.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_10k import load_official_history, labels, fair_box_probability, stable_rng
from val import GAMES, generate, model_selection_weights

METHODS = (
    "random", "ensemble",
    "bayes_long", "decay_30", "session_hier",
    "transition", "pair_chain", "echo_repeat",
)
NEW_METHODS = METHODS[2:]
TRAIN = 50
TICKET_COUNT = 10_000


def normalize(v):
    z = sum(v)
    if not z > 0: raise ValueError("All weights are zero")
    return [x / z for x in v]


def prior_rows(history, limit=500):
    return history[-limit:]


def build_model(method, history, target_stream, width):
    """Construct a probability model using ONLY observations before target draw.

    All methods use strong smoothing to avoid assigning zero probability to an
    unobserved outcome. target_stream is known from the draw schedule.
    """
    if method not in METHODS: raise ValueError(method)
    if len(history) < TRAIN: raise ValueError("Insufficient prior history")
    h = prior_rows(history)
    width = int(width)
    p = [[0.1] * 10 for _ in range(width)]
    if method == "random": return {"marginal": p, "conditional": None}
    if method == "ensemble":
        p = [normalize(model_selection_weights(f"pick{width}", h, position=i))
             for i in range(width)]
        return {"marginal": p, "conditional": None}

    counts = [[0.0] * 10 for _ in range(width)]
    stream_counts = [[0.0] * 10 for _ in range(width)]
    decayed = [[0.0] * 10 for _ in range(width)]
    for age, row in enumerate(reversed(h)):
        weight = 2 ** (-age / 30)
        is_stream = row["stream"] == target_stream
        for i, d in enumerate(row["numbers"]):
            counts[i][d] += 1
            decayed[i][d] += weight
            if is_stream: stream_counts[i][d] += 1
    base = [normalize([5 + x for x in c]) for c in counts]

    if method == "bayes_long":
        return {"marginal": base, "conditional": None}
    if method == "decay_30":
        p = [normalize([4 + v for v in c]) for c in decayed]
        return {"marginal": p, "conditional": None}
    if method == "session_hier":
        p = [normalize([5 + s + 0.2 * g for s, g in zip(sc, gc)])
             for sc, gc in zip(stream_counts, counts)]
        return {"marginal": p, "conditional": None}

    if method == "transition":
        transition = [[[0.0] * 10 for _ in range(10)] for _ in range(width)]
        for before, after in zip(h, h[1:]):
            for i in range(width):
                transition[i][before["numbers"][i]][after["numbers"][i]] += 1
        last_digits = h[-1]["numbers"]
        p = [normalize([35 * b + t for b, t in zip(base[i], transition[i][last_digits[i]])])
             for i in range(width)]
        return {"marginal": p, "conditional": None}

    if method == "echo_repeat":
        repeats = [0] * width
        for before, after in zip(h, h[1:]):
            for i in range(width):
                repeats[i] += before["numbers"][i] == after["numbers"][i]
        prev = h[-1]["numbers"]
        p = []
        n = len(h) - 1
        for i in range(width):
            # Beta(2,18) shrinkage toward fair 1-in-10 same-position repeat.
            repeat_p = (repeats[i] + 2) / (n + 20)
            remaining = [base[i][j] if j != prev[i] else 0 for j in range(10)]
            other_p = normalize(remaining)
            p.append([repeat_p if j == prev[i] else (1 - repeat_p) * other_p[j]
                      for j in range(10)])
        return {"marginal": p, "conditional": None}

    if method == "pair_chain":
        # Within-draw conditional digit relationships, rather than independent
        # position weights. Only the observed prior pair sequence is consulted.
        pair = [[[0.0] * 10 for _ in range(10)] for _ in range(width)]
        for row in h:
            for i in range(1, width):
                pair[i][row["numbers"][i - 1]][row["numbers"][i]] += 1
        conditional = []
        for i in range(width):
            if i == 0:
                conditional.append(None)
            else:
                conditional.append([
                    normalize([40 * b + obs for b, obs in zip(base[i], pair[i][digit])])
                    for digit in range(10)
                ])
        return {"marginal": base, "conditional": conditional}
    raise AssertionError(method)


def dist(model, position, prefix):
    if model["conditional"] and position > 0:
        return model["conditional"][position][prefix[-1]]
    return model["marginal"][position]


def probability_of_digits(model, digits):
    likelihood = 1.0
    for i, digit in enumerate(digits):
        likelihood *= dist(model, i, digits[:i])[digit]
    return likelihood


def sample_unique(model, width, n, rng):
    picks, seen = [], set()
    for _ in range(n * 1000):
        if len(picks) >= n: break
        digits = []
        for i in range(width):
            weights = dist(model, i, digits)
            digits.append(rng.choices(range(10), weights=weights, k=1)[0])
        key = tuple(digits)
        if key not in seen:
            seen.add(key)
            picks.append({"numbers": digits, "bonus": None})
    if len(picks) != n: raise AssertionError("Failed to generate unique predictions")
    return picks


def one_method(game, history, method, tickets, train, seed):
    width = GAMES[game]["size"]
    count = len(history) - train
    min_per_draw, remainder = divmod(tickets, count)
    rng = stable_rng(seed, game, method)
    results = Counter()
    expected_box = 0.0
    likelihood_deltas = []
    mid = train + (count * 2) // 3
    blocks = {
        "exploratory_early": Counter(),
        "exploratory_late": Counter(),
    }
    for offset, index in enumerate(range(train, len(history))):
        row = history[index]
        n = min_per_draw + (offset < remainder)
        previous = history[max(0, index - 500):index]
        model = build_model(method, previous, row["stream"], width)
        if method in ("random", "ensemble"):
            picks = generate(game, previous, method, n, rng)
        else:
            picks = sample_unique(model, width, n, rng)
        if len(picks) != n:
            raise AssertionError("Ticket allocation mismatch")
        segment = "exploratory_early" if index < mid else "exploratory_late"
        blocks[segment]["draws"] += 1
        for pick in picks:
            straight, box, fst, fbox = labels(pick, row)
            results["tickets"] += 1
            results["straight"] += straight
            results["any_order"] += box
            results["fireball_any_order"] += fbox
            results["fireball_straight"] += fst
            results["fireball_only_any_order"] += fbox and not box
            blocks[segment]["tickets"] += 1
            blocks[segment]["straight"] += straight
            blocks[segment]["any_order"] += box
            expected_box += fair_box_probability(pick)
        actual_probability = probability_of_digits(model, row["numbers"])
        # Positive = higher probability assigned to the ACTUAL full ordered
        # outcome than fair uniform; negative = worse.
        likelihood_deltas.append(math.log(actual_probability) + width * math.log(10))
    n_draw = len(likelihood_deltas)
    mean = statistics.mean(likelihood_deltas)
    se = statistics.stdev(likelihood_deltas) / math.sqrt(n_draw)
    return {
        "tickets": results["tickets"],
        "straight": results["straight"],
        "any_order": results["any_order"],
        "box_only": results["any_order"] - results["straight"],
        "fireball_any_order": results["fireball_any_order"],
        "fireball_straight": results["fireball_straight"],
        "fireball_only_any_order": results["fireball_only_any_order"],
        "expected_straight_fair": round(tickets / (10 ** width), 3),
        "expected_any_order_fair": round(expected_box, 3),
        "mean_log_score_advantage_vs_fair_nats": round(mean, 7),
        "approx_95pct_interval_nats": [round(mean - 1.96 * se, 7),
                                     round(mean + 1.96 * se, 7)],
        "exploratory_periods": {k: dict(v) for k, v in blocks.items()},
    }


def evaluate(game, history, tickets=TICKET_COUNT, train=TRAIN, seed=20261115):
    if game not in ("pick3", "pick4", "pick5"): raise ValueError("Unknown digit game")
    if train < 50 or len(history) <= train: raise ValueError("Too little history")
    held_out = len(history) - train
    low, rem = divmod(tickets, held_out)
    if low == 0 or low + bool(rem) > 20:
        raise ValueError("Each draw requires 1 to 20 picks")
    data = {method: one_method(game, history, method, tickets, train, seed)
            for method in METHODS}
    return {
        "history_draws": len(history),
        "heldout_draws": held_out,
        "heldout_first": history[train]["at"],
        "heldout_last": history[-1]["at"],
        "tickets_per_method": tickets,
        "tickets_per_draw": [low, low + bool(rem)],
        "methods": data,
    }


def markdown(report):
    out = [
        "# VAL method challengers: historical research",
        "",
        f"Produced: {report['produced_utc']}",
        "",
        "**Exploratory replay, not evidence of predictable lottery outcomes.**",
        "Each method makes 10,000 predictions per game on identical real historical draws.",
        "Predictions only use earlier outcomes; model definitions were selected after",
        "a previous analysis of overlapping history, so neither the full replay",
        "nor the last-third segment is an independent untouched confirmation.",
        "Live VAL predictions, ranked primary, random controls, and ledger are unchanged.",
        "",
        "New approaches: Bayes Long (smoothed long-run digit position counts),",
        "Decay 30 (recency-weighted), Session Hier (Day/Night context),",
        "Transition (last-draw digit dependencies), Pair Chain (within-number digit",
        "dependencies), Echo Repeat (same-position repeats from preceding draw).",
        "",
        "Straight counts full ordered matches. Any Order counts the correct",
        "digit multiset (including Straights); Box-only excludes Straights.",
        "FIREBALL Any Order is separate and overlaps ordinary matches.",
        "All outcomes are simulated paper plays, not actual winning tickets.",
        "",
    ]
    for game, details in report["games"].items():
        out.extend([
            f"## {GAMES[game]['name']}",
            "",
            f"{details['heldout_draws']} actual test drawings; 10,000 predictions per method.",
            "",
            "| Method | Straight | Any Order | FIREBALL Any Order | Expected Any Order (fair) | Mean log-score edge vs fair (nats/draw) |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ])
        for method, result in details["methods"].items():
            out.append(f"| {method} | {result['straight']} | {result['any_order']} | "
                       f"{result['fireball_any_order']} | "
                       f"{result['expected_any_order_fair']:.1f} | "
                       f"{result['mean_log_score_advantage_vs_fair_nats']:+.5f} |")
        out.extend(["",
                    "The log-score statistic assigns a probability to the actual full",
                    "ordered draw before seeing it; positive is better than a uniform",
                    "fair model, negative is worse. This is an exploratory comparison.",
                    "Method rankings may be dominated by chance and multiple testing.",
                    ""])
    out.extend([
        "## What would justify a promotion?",
        "",
        "Do not promote a method on these replay results. First freeze its settings;",
        "then evaluate future draws that were not available while selecting models.",
        "Require repeatable improvement in precommitted log scoring and target-draw",
        "outcomes over random controls, with uncertainty and multiple tests accounted",
        "for. A fair lottery supplies no persistent exploitable prediction signal.",
        "",
    ])
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets", type=int, default=TICKET_COUNT)
    parser.add_argument("--seed", type=int, default=20261115)
    parser.add_argument("--json", default="reports/research_challengers.json")
    parser.add_argument("--md", default="reports/research_challengers.md")
    args = parser.parse_args()
    report = {"produced_utc": datetime.now(timezone.utc).isoformat(),
              "version": "val_challenger_lab_v1", "seed": args.seed,
              "methods": list(METHODS), "games": {}}
    for game in ("pick3", "pick4", "pick5"):
        history = load_official_history(game)
        result = evaluate(game, history, tickets=args.tickets, seed=args.seed)
        report["games"][game] = result
        print(json.dumps({"game": game, "methods": {
            m: {"straight": d["straight"], "any_order": d["any_order"],
                "logscore_advantage": d["mean_log_score_advantage_vs_fair_nats"]}
            for m, d in result["methods"].items()}}), flush=True)
    for path, content in [(args.json, json.dumps(report, indent=2) + "\n"),
                          (args.md, markdown(report) + "\n")]:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    print("Saved challenger research results.")


if __name__ == "__main__":
    main()
