"""Production formula v4: true next-draw tests of conditional experts."""
import math
import random
import unittest

from research_virtual_draw_lab import simulate
from val_digit_formula_v2 import (
    VERSION, forecast, generate_picks, joint_probability,
    _top_box_candidates, _online_evidence, path_probability,
)
from val_box import distinct_permutations, box_ways


class LiveDigitFormulaV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fair = simulate("pick3", "fair_independent", 1550, 108)
        cls.echo = simulate("pick3", "within_draw_echo", 1550, 108)

    def test_fair_drawing_returns_unchanged_maximum_coverage_baseline(self):
        ready = forecast("pick3", self.fair, "Day")
        self.assertEqual(VERSION, "digit_box_v4")
        self.assertFalse(ready["gate_passed"])
        self.assertFalse(ready["online_evidence"]["confirmed"])
        tickets, metadata = generate_picks(
            "pick3", self.fair, "Day", 3, random.Random(118))
        self.assertEqual(len(tickets), 3)
        self.assertFalse(metadata["signal_gate_passed"])
        self.assertEqual(len({tuple(sorted(p["numbers"])) for p in tickets}), 3)
        self.assertTrue(all(box_ways(p["numbers"]) == 6 for p in tickets))
        self.assertAlmostEqual(joint_probability(ready, [2, 3, 6]), .001)

    def test_echo_bias_changes_production_joint_formula_and_box_selection(self):
        ready = forecast("pick3", self.echo, "Night")
        evidence = ready["online_evidence"]
        self.assertTrue(evidence["confirmed"], evidence)
        self.assertEqual(evidence["active"], "echo")
        self.assertTrue(ready["gate_passed"])
        self.assertIn("online_echo", ready["weights"])
        self.assertGreater(ready["signal_strength"], .10)
        self.assertNotAlmostEqual(
            joint_probability(ready, [2, 2, 2]),
            joint_probability(ready, [2, 3, 4]), places=6)
        tickets, meta = generate_picks(
            "pick3", self.echo, "Night", 3, random.Random(118))
        expected = _top_box_candidates(ready, 3)
        self.assertEqual([tuple(p["numbers"]) for p in tickets], expected)
        self.assertEqual(meta["passed_experts"], ["online_echo"])
        self.assertTrue(meta["signal_gate_passed"])
        for p in tickets:
            self.assertAlmostEqual(
                p["box_probability"],
                sum(joint_probability(ready, arr)
                    for arr in distinct_permutations(p["numbers"])), places=12)

    def test_online_joint_formula_matches_evidence_predictor_distribution(self):
        evidence = _online_evidence("pick3", self.echo, "Day")
        self.assertTrue(evidence["confirmed"])
        from val_box_challenger import BoxEvidence
        direct = BoxEvidence("pick3")
        for row in self.echo:
            direct.observe(row)
        name, model = direct.prediction("Day")
        self.assertEqual(name, evidence["active"])
        self.assertIsNotNone(model)
        for combo in ([0, 0, 0], [1, 2, 3], [7, 7, 5], [0, 9, 9]):
            self.assertAlmostEqual(
                path_probability(evidence["model"], combo),
                direct.probability(model, combo), places=12)

    def test_future_outcome_cannot_affect_frozen_forecast(self):
        now = forecast("pick3", self.echo[:1450], "Night")
        changed = [dict(row) for row in self.echo]
        changed[1450]["numbers"] = [9, 9, 9]
        changed[1500]["numbers"] = [7, 7, 7]
        next_version = forecast("pick3", changed[:1450], "Night")
        self.assertEqual(now, next_version)


if __name__ == "__main__":
    unittest.main()
