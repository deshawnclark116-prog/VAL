"""Evidence-gated next-draw Any Order challenger for VAL research.

No live production integration. Each probability forecast is made before
the corresponding drawing is observed. Four normalized models:
pooled digit bias, per-position bias, Day/Night position bias, and
within-draw predecessor dependence. Their likelihood-ratio evidence
accumulates against the fixed iid fair null.

The threshold is a *family-wide* anytime fair-null error budget over
four models and three games, assuming independent uniform digits.
Crossing it in already-inspected history does not establish a real edge.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import combinations_with_replacement, permutations
import math
import random

from val_box import any_order_prize, digits_key, random_box_picks

VERSION = "box_evidence_challenger_v1"
EXPERTS = ("pooled", "position", "session", "echo")
GAMES = ("pick3", "pick4", "pick5")
WINDOW = 700
WARMUP = 200
# Bonferroni + Ville's inequality: four adaptive likelihood-ratio
# martingales x three games, under iid independent uniform draws.
LOG_GATE = math.log(len(EXPERTS) * len(GAMES) / .05)


def smooth(counts, prior):
    denominator = sum(counts) + 10 * prior
    return tuple((c + prior) / denominator for c in counts)


@lru_cache(maxsize=3)
def box_candidates(game):
    """Cache each legal Box multiset and its distinct ordered outcomes."""
    width = int(game[-1])
    return tuple((combo, tuple(set(permutations(combo))))
                 for combo in combinations_with_replacement(range(10), width)
                 if any_order_prize(game, combo) > 0)


class BoxEvidence:
    def __init__(self, game, window=WINDOW, warmup=WARMUP):
        if game not in GAMES:
            raise ValueError(game)
        self.game = game
        self.width = int(game[-1])
        self.window = window
        self.warmup = warmup
        self.queue = deque()
        self.pooled = [0] * 10
        self.positions = [[0] * 10 for _ in range(self.width)]
        self.sessions = {s: [[0] * 10 for _ in range(self.width)]
                         for s in ("Day", "Night")}
        self.transitions = [[0] * 10 for _ in range(10)]
        self.seen = 0
        self.log_e = {name: 0. for name in EXPERTS}

    def _change(self, row, sign):
        numbers = row["numbers"]
        if (len(numbers) != self.width or
                any(type(d) is not int or d not in range(10) for d in numbers) or
                row["stream"] not in self.sessions):
            raise ValueError("Bad digit drawing")
        for pos, digit in enumerate(numbers):
            self.pooled[digit] += sign
            self.positions[pos][digit] += sign
            self.sessions[row["stream"]][pos][digit] += sign
            if pos:
                self.transitions[numbers[pos - 1]][digit] += sign

    def forecasts(self, stream):
        if stream not in self.sessions:
            raise ValueError("Unknown drawing stream")
        p = smooth(self.pooled, 180.)
        return {
            "pooled": (tuple(p for _ in range(self.width)), None),
            "position": (tuple(smooth(c, 60.) for c in self.positions), None),
            "session": (tuple(smooth(c, 45.) for c in self.sessions[stream]), None),
            # First digit uses the pooled distribution; later digits are
            # conditioned on their immediate predecessor within the same draw.
            "echo": (tuple(p for _ in range(self.width)),
                     tuple(smooth(c, 18.) for c in self.transitions)),
        }

    @staticmethod
    def probability(forecast, numbers):
        positions, conditionals = forecast
        probability = 1.
        for i, digit in enumerate(numbers):
            dist = (conditionals[numbers[i - 1]]
                    if i and conditionals is not None else positions[i])
            probability *= dist[digit]
        return probability

    def active(self):
        if self.seen < self.warmup:
            return None
        qualified = [name for name in EXPERTS
                     if self.log_e[name] >= LOG_GATE]
        return max(qualified, key=lambda name: self.log_e[name]) if qualified else None

    def prediction(self, stream):
        """Return evidence-selected model and past-only forecast distributions."""
        forecasts = self.forecasts(stream)
        chosen = self.active()
        return chosen, forecasts[chosen] if chosen else None

    def observe(self, row):
        """Call only AFTER current draw decisions have been recorded."""
        forecasts = self.forecasts(row["stream"])
        if self.seen >= self.warmup:
            fair_p = .1 ** self.width
            for name in EXPERTS:
                p = self.probability(forecasts[name], row["numbers"])
                self.log_e[name] += math.log(p / fair_p)
        self._change(row, +1)
        self.queue.append(row)
        if len(self.queue) > self.window:
            self._change(self.queue.popleft(), -1)
        self.seen += 1

    def picks(self, stream, rng=None, count=3):
        """Rank complete Box sets only if evidence passes, else fair controls."""
        chosen, forecast = self.prediction(stream)
        if chosen is None:
            return None, random_box_picks(self.game, count, rng)
        scored = []
        for combo, ordered in box_candidates(self.game):
            p = sum(self.probability(forecast, path) for path in ordered)
            scored.append((p, combo))
        scored.sort(key=lambda x: (-x[0], x[1]))
        picks = [dict(numbers=list(combo), bonus=None, play_type="any_order",
                      model_box_probability=p, formula_version=VERSION)
                 for p, combo in scored[:count]]
        return chosen, picks

    def log_gain(self, row, chosen=None):
        if chosen is None:
            return 0.
        forecasts = self.forecasts(row["stream"])
        return math.log(self.probability(forecasts[chosen], row["numbers"])
                        / (.1 ** self.width))


def grade_box(picks, numbers):
    key = digits_key(numbers)
    return int(any(digits_key(p["numbers"]) == key for p in picks))
