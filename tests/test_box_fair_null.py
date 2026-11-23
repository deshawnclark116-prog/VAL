"""Regression checks for exact full-Box fair baseline."""
import unittest

from research.box_fair_null import (
    canonical_box, fair_box_distribution, fair_box_probability,
    portfolio_fair_probability,
)


class BoxFairNullTests(unittest.TestCase):
    def test_distribution_normalizes_all_games(self):
        for length in (3, 4, 5):
            with self.subTest(length=length):
                self.assertAlmostEqual(sum(fair_box_distribution(length).values()), 1.0, places=12)

    def test_exact_multiplicity(self):
        self.assertAlmostEqual(fair_box_probability("123"), 6 / 1000)
        self.assertAlmostEqual(fair_box_probability("112"), 3 / 1000)
        self.assertAlmostEqual(fair_box_probability("111"), 1 / 1000)
        self.assertAlmostEqual(fair_box_probability("0012"), 12 / 10000)
        self.assertAlmostEqual(fair_box_probability("00112"), 30 / 100000)

    def test_leading_zeros_and_duplicate_tickets(self):
        self.assertEqual(canonical_box("010", 3), "001")
        self.assertAlmostEqual(portfolio_fair_probability(["010", "001", "123"], 3), 0.003 + 0.006)

    def test_distinct_ticket_portfolio_not_uniform(self):
        self.assertAlmostEqual(portfolio_fair_probability(["123", "456", "789"], 3), 0.018)
        self.assertAlmostEqual(portfolio_fair_probability(["112", "334", "556"], 3), 0.009)

    def test_all_identical_is_in_outcome_space(self):
        for length in (3, 4, 5):
            dist = fair_box_distribution(length)
            self.assertIn("0" * length, dist)
            self.assertAlmostEqual(dist["0" * length], 10 ** (-length))

    def test_invalid_inputs(self):
        for ticket, length in (("12", 3), ("1234", 3), ("12a", 3)):
            with self.assertRaises(ValueError):
                canonical_box(ticket, length)


if __name__ == "__main__":
    unittest.main()
