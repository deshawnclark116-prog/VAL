"""Exact full-Box fair-null probability checks; no historical data required.

Run: python -m unittest discover -s tests -p 'test_box_combinatorial_null.py'
"""
import itertools
import math
import unittest
from collections import Counter


def box_key(digits):
    return tuple(sorted(digits))


def box_probability(digits):
    """Exact probability of this unordered multiset under independent fair digits."""
    n = len(digits)
    multiplicities = Counter(digits).values()
    return math.factorial(n) / math.prod(math.factorial(k) for k in multiplicities) / (10 ** n)


def portfolio_probability(tickets):
    """Probability of at least one complete Any Order hit, with duplicate tickets deduplicated."""
    return sum(box_probability(k) for k in {box_key(t) for t in tickets})


def expected_wins_from_ordered_draws(tickets, n):
    winners = {box_key(t) for t in tickets}
    return sum(box_key(outcome) in winners for outcome in itertools.product(range(10), repeat=n)) / (10 ** n)


class ExactFairBoxNull(unittest.TestCase):
    def test_exhaustive_fair_null(self):
        for n in (3, 4, 5):
            keys = {box_key(t) for t in itertools.product(range(10), repeat=n)}
            self.assertAlmostEqual(sum(box_probability(k) for k in keys), 1.0, places=12)
            sample = [
                tuple(range(n)),
                tuple([0] * n),
                tuple([0] * (n - 1) + [1]),
            ]
            self.assertAlmostEqual(portfolio_probability(sample), expected_wins_from_ordered_draws(sample, n), places=12)

    def test_multiplicity_matters(self):
        self.assertAlmostEqual(box_probability((1, 2, 3)), 0.006)
        self.assertAlmostEqual(box_probability((1, 1, 2)), 0.003)
        self.assertAlmostEqual(box_probability((1, 1, 1)), 0.001)
        self.assertAlmostEqual(box_probability((0, 1, 2, 3, 4)), 0.012)

    def test_duplicate_tickets_do_not_increase_coverage(self):
        self.assertEqual(portfolio_probability([(1, 2, 3), (3, 2, 1)]), 0.006)


if __name__ == "__main__":
    unittest.main()
