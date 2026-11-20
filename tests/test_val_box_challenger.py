"""Unit and synthetic tests for the research-only Box evidence challenger."""
import math
import random
import unittest
from itertools import product

from val_box import digits_key
from val_box_challenger import (BoxEvidence, EXPERTS, LOG_GATE,
                                box_candidates, grade_box)
from research_virtual_draw_lab import simulate


class BoxEvidenceTests(unittest.TestCase):
    def test_joint_models_normalized_including_echo(self):
        engine = BoxEvidence("pick3")
        for row in simulate("pick3", "within_draw_echo", 410, 2):
            engine.observe(row)
        for name, forecast in engine.forecasts("Night").items():
            self.assertIn(name, EXPERTS)
            total = sum(engine.probability(forecast, x)
                        for x in product(range(10), repeat=3))
            self.assertAlmostEqual(total, 1., places=9)

    def test_all_box_multisets_include_multiplicities(self):
        self.assertEqual(len(box_candidates("pick3")), 210)
        self.assertEqual(len(box_candidates("pick4")), 705)
        self.assertEqual(len(box_candidates("pick5")), 1992)
        pick = [{"numbers": [0, 1, 1]}]
        self.assertEqual(grade_box(pick, [1, 0, 1]), 1)
        self.assertEqual(grade_box(pick, [1, 0, 0]), 0)

    def test_true_fair_draws_do_not_force_an_expert(self):
        model = BoxEvidence("pick3")
        for row in simulate("pick3", "fair_independent", 1300, 8):
            model.observe(row)
        self.assertIsNone(model.active())
        self.assertTrue(all(x < LOG_GATE for x in model.log_e.values()))
        selected, tickets = model.picks("Day", random.Random(9))
        self.assertIsNone(selected)
        self.assertEqual(len({digits_key(p["numbers"]) for p in tickets}), 3)

    def test_detects_artificial_within_draw_echo(self):
        model = BoxEvidence("pick3")
        for row in simulate("pick3", "within_draw_echo", 1500, 4):
            model.observe(row)
        self.assertEqual(model.active(), "echo")
        self.assertGreater(model.log_e["echo"], LOG_GATE)

    def test_previous_results_only(self):
        rows = simulate("pick3", "fixed_position_strong", 600, 1)
        a, b = BoxEvidence("pick3"), BoxEvidence("pick3")
        for row in rows[:480]:
            a.observe(row)
            b.observe(row)
        first = a.prediction("Day")
        edited = dict(rows[480], numbers=[9, 9, 9])
        # The upcoming result is not part of either past-only state.
        self.assertEqual(first, b.prediction("Day"))
        a.observe(rows[480])
        b.observe(edited)
        self.assertNotEqual(a.forecasts("Day"), b.forecasts("Day"))


if __name__ == "__main__":
    unittest.main()
