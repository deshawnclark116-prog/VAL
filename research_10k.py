"""VAL research-only chronological 10,000-pick comparison for digit games.

No live picks, schedules, ledger records, or production weights are modified.
Each method gets exactly 10,000 predictions distributed across the same real
historical drawings, using ONLY earlier drawing results to select each ticket.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from val import CUTOFF, ET, GAMES, METHODS, generate, parse_official

GAMES_TO_TEST = ("pick3", "pick4", "pick5")
TICKET_TARGET = 10_000
TRAINING_DRAWS = 50


def load_official_history(game):
    game_id = GAMES[game]["id"]
    request = urllib.request.Request(
        f"https://www.valottery.com/api/v1/downloadall?gameId={game_id}",
        headers={"User-Agent": "VAL/1.0 (retrospective lottery research)"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        content = response.read(12_000_000).decode("utf-8-sig")
    records = parse_official(game, content)
    return sorted(
        (row for row in records if row["game"] == game),
        key=lambda row: (row["at"], row["stream"])
    )


def labels(pick, draw):
    """Strict digit-multiplicity grading, with FIREBALL separate."""
    a = pick["numbers"]
    b = draw["numbers"]
    straight = a == b
    box = sorted(a) == sorted(b)
    fireball_straight = False
    fireball_any_order = False
    fire = draw.get("extra")
    if fire is not None:
        for i in range(len(b)):
            substituted = list(b)
            substituted[i] = fire
            fireball_straight |= substituted == a
            fireball_any_order |= sorted(substituted) == sorted(a)
    return straight, box, fireball_straight, fireball_any_order


def fair_box_probability(pick):
    digits = pick["numbers"]
    possibilities = math.factorial(len(digits))
    for repeat_count in Counter(digits).values():
        possibilities //= math.factorial(repeat_count)
    return possibilities / 10 ** len(digits)


def stable_rng(seed, game, method):
    data = f"{seed}:{game}:{method}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(data).digest()[:8], "big"))


def evaluate(game, history, tickets=TICKET_TARGET, train=TRAINING_DRAWS, seed=20261115):
    if game not in GAMES_TO_TEST:
        raise ValueError("Only Pick 3, Pick 4 and Pick 5 are supported")
    if train < 30 or len(history) <= train:
        raise ValueError("Insufficient chronological history")
    if tickets < (len(history) - train):
        raise ValueError("Need at least one prediction per held-out drawing")

    # Each actual drawing is counted once; budget varies by at most one ticket.
    held_out = len(history) - train
    base, remainder = divmod(tickets, held_out)
    if base < 1 or base + bool(remainder) > 20:
        raise ValueError("Tickets per drawing exceed generate() capacity (20)")

    out = {}
    for method in METHODS:
        rng = stable_rng(seed, game, method)
        counts = Counter()
        box_expectation = 0.0
        draw_hits_straight = 0
        draw_hits_box = 0
        draw_hits_fireball = 0
        for offset, index in enumerate(range(train, len(history))):
            draw = history[index]
            n = base + (offset < remainder)
            # This slice ends strictly BEFORE the held-out drawing.
            previous_draws = history[max(0, index - 500):index]
            choices = generate(game, previous_draws, method, n, rng)
            if len(choices) != n:
                raise AssertionError(f"{method}: expected {n} unique picks")
            this_straight = this_box = this_fireball = False
            for p in choices:
                st, box, fire_st, fire_box = labels(p, draw)
                counts["tickets"] += 1
                counts["straight"] += st
                counts["any_order_including_straight"] += box
                counts["box_only"] += box and not st
                counts["fireball_straight"] += fire_st
                counts["fireball_any_order"] += fire_box
                counts["fireball_only_any_order"] += fire_box and not box
                box_expectation += fair_box_probability(p)
                this_straight |= st
                this_box |= box
                this_fireball |= fire_box
            draw_hits_straight += this_straight
            draw_hits_box += this_box
            draw_hits_fireball += this_fireball
        if counts["tickets"] != tickets:
            raise AssertionError(f"Ticket budget mismatch: {method} {counts['tickets']}")
        out[method] = {
            **dict(counts),
            "straight": counts["straight"],
            "any_order_including_straight": counts["any_order_including_straight"],
            "box_only": counts["box_only"],
            "fireball_straight": counts["fireball_straight"],
            "fireball_any_order": counts["fireball_any_order"],
            "fireball_only_any_order": counts["fireball_only_any_order"],
            "expected_straight_fair_draw": tickets / (10 ** GAMES[game]["size"]),
            "expected_any_order_fair_draw": round(box_expectation, 3),
            "draws_with_straight": draw_hits_straight,
            "draws_with_any_order": draw_hits_box,
            "draws_with_fireball_any_order": draw_hits_fireball,
        }
    return {
        "game": game,
        "history_draws": len(history),
        "training_draws_before_first_test": train,
        "distinct_held_out_draws": held_out,
        "held_out_from": history[train]["at"],
        "held_out_to": history[-1]["at"],
        "draw_sessions": sorted(set(x["stream"] for x in history[train:])),
        "tickets_per_method": tickets,
        "ticket_allocation_per_draw": [base, base + bool(remainder)],
        "methods": out,
    }


def to_markdown(report):
    lines = [
        "# VAL: 10,000 chronological predictions per method",
        "",
        f"Generated (UTC): {report['generated_at']}",
        "",
        "Each method makes **10,000 picks per game**, spread over the **same real later drawings**."
        " Only strictly earlier draw results are available when each pick is generated."
        " Random is the comparison group.",
        "",
        "**Straight** = all digits in exact order. **Any Order** = same digits with the"
        " same repetitions, including Straight. **Box-only** excludes Straight."
        " FIREBALL matches are hypothetical optional-wager checks, not paid tickets.",
        "",
        "This is a *historical replay*, NOT 10,000 independent drawings or 10,000"
        " real bets. A method does not demonstrate skill merely by exceeding its"
        " single-draw chance expectation. Method selection from the same test is"
        " vulnerable to overfitting; confirm anything promising on future draws.",
        "",
    ]
    for game, detail in report["games"].items():
        lines += [
            f"## {GAMES[game]['name']}",
            "",
            f"Real historical drawings: {detail['history_draws']}; held-out drawings: "
            f"{detail['distinct_held_out_draws']}; first held-out UTC: "
            f"{detail['held_out_from']}; last held-out UTC: {detail['held_out_to']}.",
            "",
            "| Method | Predictions | Straight | Any Order (total) | Box-only | Expected Any Order if fair | FIREBALL Any Order |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for method, x in detail["methods"].items():
            lines.append(f"| {method.title()} | {x['tickets']:,} | {x['straight']} | "
                         f"{x['any_order_including_straight']} | {x['box_only']} | "
                         f"{x['expected_any_order_fair_draw']:.1f} | {x['fireball_any_order']} |")
        lines += ["", "Fair-draw expected Straight hits per method: "
                  f"{next(iter(detail['methods'].values()))['expected_straight_fair_draw']:.2f}."
                  " FIREBALL counts can overlap regular hits and are not included in the Any Order total.",
                  ""]
    lines += [
        "## Safeguards",
        "",
        "- All tested dates come from official Virginia Lottery bulk drawing histories.",
        "- Same held-out drawings, same number of tickets, and predefined methods for fair comparisons.",
        "- Ranking and live production picks are not used or changed by this report.",
        "- Predictions within a drawing share the same outcome and are not independent trials.",
        "- No real tickets purchased; no gambling profit or winning advantage established.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickets", type=int, default=TICKET_TARGET)
    parser.add_argument("--seed", type=int, default=20261115)
    parser.add_argument("--out", default="reports/research_10k.json")
    parser.add_argument("--markdown", default="reports/research_10k.md")
    args = parser.parse_args()
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Virginia Lottery official bulk download",
        "research_version": "val_historical_digit_methods_10k_v1",
        "cutoff": CUTOFF,
        "seed": args.seed,
        "games": {},
    }
    for game in GAMES_TO_TEST:
        history = load_official_history(game)
        result["games"][game] = evaluate(game, history, tickets=args.tickets, seed=args.seed)
        print(json.dumps({
            "game": game, "held_out_draws": result["games"][game]["distinct_held_out_draws"],
            "methods": {method: {"straight": x["straight"],
                                "any_order": x["any_order_including_straight"],
                                "fireball_any": x["fireball_any_order"]}
                        for method, x in result["games"][game]["methods"].items()}
        }), flush=True)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    md = Path(args.markdown); md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(to_markdown(result) + "\n")
    print(f"Saved {out} and {md}")


if __name__ == "__main__":
    main()
