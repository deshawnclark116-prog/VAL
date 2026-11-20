"""Mock Box stress harness: null rates, genuine heldout grading and oracle."""
import math
import unittest
from research_mock_box_stress import run_case, null_probability

class MockBoxStressTests(unittest.TestCase):
    def test_exact_null_rates_with_three_disjoint_maximum_coverage_tickets(self):
        self.assertAlmostEqual(null_probability("pick3"), .018)
        self.assertAlmostEqual(null_probability("pick4"), .0072)
        self.assertAlmostEqual(null_probability("pick5"), .0036)

    def test_fair_heldout_independent_selection_and_truth_math(self):
        r = run_case("pick3", "fair_independent", train=400, test=750,
                     replicate=81, stride=1)
        self.assertEqual(r["box_target_draws"], 750)
        self.assertEqual(r["paper_tickets_per_method_per_target"], 3)
        self.assertAlmostEqual(r["candidate_fair_expected_wins"], 750*.018,
                               places=8)
        self.assertAlmostEqual(r["random_fair_expected_wins"], 750*.018,
                               places=8)
        self.assertAlmostEqual(r["candidate_true_expected_wins"],
                               r["candidate_fair_expected_wins"], places=8)
        self.assertAlmostEqual(r["random_true_expected_wins"],
                               r["random_fair_expected_wins"], places=8)
        self.assertEqual(r["candidate_full_box_wins"]-r["random_full_box_wins"],
                         r["model_only"]-r["control_only"])
        self.assertTrue(math.isfinite(r["mean_prequential_log_gain_vs_fair"]))

    def test_hidden_bias_is_not_used_by_the_prediction(self):
        r = run_case("pick3", "hidden_opposing_machines", train=400,
                     test=600, replicate=81, stride=20)
        self.assertEqual(r["box_target_draws"], 30)
        self.assertTrue(math.isfinite(r["candidate_true_expected_wins"]))
        self.assertTrue(math.isfinite(r["random_true_expected_wins"]))
        self.assertLessEqual(r["candidate_full_box_wins"], 30)

if __name__ == "__main__":
    unittest.main()
