"""Checks for complete Any Order mock-drawing stress evaluation."""
import unittest

from research_virtual_box_stress import (
    BLOCK, TRAIN, TEST, TRIALS, run_single, aggregate, fair_coverage, report,
)
from val_box import random_box_picks
import random


class VirtualBoxStressTests(unittest.TestCase):
    def test_fair_coverage_is_complete_multiset_probability(self):
        tickets = random_box_picks("pick3", 3, random.Random(3))
        self.assertAlmostEqual(fair_coverage(tickets, 3), 18 / 1000)
        self.assertAlmostEqual(fair_coverage(
            random_box_picks("pick4", 3, random.Random(3)), 4), 72 / 10000)
        self.assertAlmostEqual(fair_coverage(
            random_box_picks("pick5", 3, random.Random(3)), 5), 360 / 100000)

    def test_mock_draws_score_every_later_result(self):
        sample = run_single("pick3", "fair_independent", 110,
                            train=850, test=20, block=10)
        self.assertEqual(sample["draws"], 20)
        self.assertEqual(sample["blocks"], 2)
        self.assertEqual(sample["active_draws"], 0)
        for m in ("challenger", "production_v3", "random"):
            self.assertAlmostEqual(sample["fair_expected_box_wins"][m],
                                   20 * .018)
            self.assertGreaterEqual(sample["box_wins"][m], 0)
            self.assertLessEqual(sample["box_wins"][m], 20)

    def test_repeatability_and_no_retrospective_replacement(self):
        a = run_single("pick3", "within_draw_echo", 118,
                       train=850, test=15, block=15)
        b = run_single("pick3", "within_draw_echo", 118,
                       train=850, test=15, block=15)
        self.assertEqual(a, b)
        totals = aggregate([a, b])
        self.assertEqual(totals["draws"], 30)
        self.assertEqual(totals["ticket_budget_each_method"], 90)
        self.assertEqual(totals["trials"], 2)

    def test_markdown_table_header_is_single_line(self):
        sample = {"draws": 20, "box_wins":
                  {"challenger": 0, "production_v3": 1, "random": 0},
                  "fair_expected_box_wins": {"challenger": .36},
                  "active_blocks": 0, "total_blocks": 2}
        md = report({"trials": 1, "train_draws": 850,
                     "test_draws": 20, "block_draws": 10,
                     "games": {"pick3": {"fair_independent": sample}}})
        self.assertIn("| pick3 | fair_independent | 20 | 0 | 1 | 0 |", md)
        self.assertEqual(len([x for x in md.splitlines()
                              if x.startswith("| ---")]), 1)


if __name__ == "__main__":
    unittest.main()
