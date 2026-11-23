"""Research-only prequential mixture of complete Any Order probability models.

Each expert is scored on the *next* complete multiset BEFORE observing it.
The fair component retains at least half of all predictive mass. Expert
weights use sequential log likelihood RATIO to the fair model, with no target leakage. This is not
an assertion of a real lottery edge or an approved production model.
"""
from __future__ import annotations
from math import exp, log
from val_bayesian_full_box import BayesianBox
from val_box import digits_key

EXPERTS = ("fair", "pooled", "exact_bag", "pair_shape")
FAIR_FLOOR = 0.5
LEARNING_RATE = 0.25
# Research alternative: forgetting prevents ancient expert evidence from
# permanently dominating when a genuine generating mechanism changes.
DEFAULT_DISCOUNT = 1.0


class OnlineBoxMixture:
    def __init__(self, game, fair_floor=FAIR_FLOOR, learning_rate=LEARNING_RATE, discount=DEFAULT_DISCOUNT):
        if not 0 <= fair_floor <= 1 or not 0 < learning_rate <= 1 or not 0 < discount <= 1:
            raise ValueError("Invalid mixture parameters")
        self.machine = BayesianBox(game)
        self.fair_floor = fair_floor
        self.learning_rate = learning_rate
        self.discount = discount
        self.log_weights = {name: 0.0 for name in EXPERTS}
        self.frozen = None
        self.last_distribution = None

    def predict(self, tickets=3):
        distributions = self.machine.distributions()
        high = max(self.log_weights.values())
        raw = {name: exp(self.learning_rate * (score-high))
               for name, score in self.log_weights.items()}
        total = sum(raw.values())
        weights = {name: value/total for name,value in raw.items()}
        fair = distributions["fair"]
        mixture = {
            key: self.fair_floor * q + (1-self.fair_floor) *
            sum(weights[name]*distributions[name][key] for name in EXPERTS)
            for key,q in fair.items()
        }
        if abs(sum(mixture.values())-1) > 1e-9:
            raise AssertionError("Not normalized")
        self.frozen = distributions
        self.last_distribution = mixture
        return {"distribution": mixture,
                "picks": self.machine.top_box(mixture, tickets),
                "weights": weights}

    def observe(self, row):
        # If a forecast was frozen, score it before updating any expert.
        if self.frozen is not None:
            actual = digits_key(row["numbers"])
            for name in EXPERTS:
                self.log_weights[name] = (self.discount * self.log_weights[name]
                                          + log(self.frozen[name][actual] / self.frozen["fair"][actual]))
            self.frozen = None
        self.machine.observe(row)

    def log_gain_vs_fair(self, actual):
        if self.last_distribution is None:
            raise ValueError("Predict first")
        key = digits_key(actual)
        fair = self.machine.distributions()["fair"][key]
        return log(self.last_distribution[key]/fair)
