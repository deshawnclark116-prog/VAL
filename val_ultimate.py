"""VAL ultimate number generator.

Pick 3/4/5: every player method plus hot and due digits vote, and the top
distinct digits become one pick. Distinct digits give the most Box ways
(6-way on Pick 3, 24-way on Pick 4, 120-way on Pick 5).

Other games: numbers spread across the whole range, avoiding the patterns
lots of people play (all birthday numbers 1-31, long runs, one decade).

Every Pick 3/4/5 ultimate pick is saved and tracked by the bot's scoreboard.
"""
from __future__ import annotations

import random
from collections import Counter

from val import GAMES
from val_box import box_ways
from val_player_methods import METHODS, player_pick

VERSION = "player_ultimate"
LABEL = "Ultimate generator (all methods vote)"
HOT_WINDOW = 100


def digit_votes(history, width):
    """Votes per digit from every method plus hot and due digits."""
    votes = Counter()
    for method in METHODS:
        votes.update(set(player_pick(method, history, width)["numbers"]))
    recent = Counter(d for r in history[-HOT_WINDOW:] for d in r["numbers"])
    for d, _ in recent.most_common(width):
        votes[d] += 1                                   # hot digits
    last_seen = {}
    for i, r in enumerate(history):
        for d in r["numbers"]:
            last_seen[d] = i
    for d in sorted(range(10), key=lambda d: last_seen.get(d, -1))[:width]:
        votes[d] += 1                                   # due digits
    return votes, recent


def ultimate_digit_pick(history, width):
    if len(history) < width:
        raise ValueError(f"Need at least {width} completed results")
    votes, recent = digit_votes(history[-HOT_WINDOW:], width)  # hot/due use the last 100 results
    ranked = sorted(range(10), key=lambda d: (-votes[d], -recent[d], d))
    digits = sorted(ranked[:width])
    return dict(numbers=digits, bonus=None, play_type="any_order", box_ways=box_ways(digits),
                rank=1, role="primary", votes={str(d): votes[d] for d in range(10)})


def spread_pick(game, rng=None):
    """Jackpot-style pick that avoids the most commonly played patterns."""
    g = GAMES[game]
    rng = rng or random.SystemRandom()
    pool = list(range(1, g["pool"] + 1))
    while True:
        nums = sorted(rng.sample(pool, g["size"]))
        high = sum(n > 31 for n in nums)
        run = max_run(nums)
        decades = len({(n - 1) // 10 for n in nums})
        if (g["pool"] <= 31 or high >= min(2, g["size"])) and run < 3 and decades >= min(3, g["size"]):
            break
    bonus = rng.randint(1, g["bonus"]) if g.get("bonus") else None
    return dict(numbers=nums, bonus=bonus)


def max_run(nums):
    best = cur = 1
    for a, b in zip(nums, nums[1:]):
        cur = cur + 1 if b == a + 1 else 1
        best = max(best, cur)
    return best


def ultimate_pick(game, history):
    if GAMES[game].get("digits"):
        return ultimate_digit_pick(history, GAMES[game]["size"]), "All methods voted; top distinct digits (most Box ways)"
    return spread_pick(game), "Spread across the range; avoids birthdays, runs and one-decade picks"
