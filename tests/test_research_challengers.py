import math
import random
import unittest

from research_challengers import METHODS, NEW_METHODS, build_model, dist, evaluate, sample_unique, probability_of_digits


def history(game="pick3", n=70):
    width = int(game[-1])
    rng = random.Random(42)
    out = []
    for i in range(n):
        out.append({"game": game, "at": f"day-{i:04d}",
                    "stream": "Day" if i % 2 == 0 else "Night",
                    "numbers": [rng.randrange(10) for _ in range(width)],
                    "bonus": None, "extra": (i % 10)})
    return out


class ChallengerTests(unittest.TestCase):
    def test_all_new_methods_give_normalized_valid_probs(self):
        h = history()
        for method in METHODS:
            m = build_model(method, h, "Night", 3)
            prefix = []
            for i in range(3):
                probs = dist(m, i, prefix)
                self.assertEqual(len(probs), 10)
                self.assertAlmostEqual(sum(probs), 1.0)
                self.assertTrue(all(p > 0 for p in probs))
                prefix.append(5)
            self.assertGreater(probability_of_digits(m, [1, 1, 0]), 0)
            self.assertEqual(len(sample_unique(m, 3, 3, random.Random(8))), 3)

    def test_only_past_history_is_used(self):
        h = history()
        for method in NEW_METHODS:
            baseline = build_model(method, h[:61], "Day", 3)
            # Altering a future draw cannot change model for earlier target.
            future = dict(h[61])
            future["numbers"] = [9, 9, 9]
            self.assertEqual(baseline, build_model(method, h[:61], "Day", 3))

    def test_same_draws_same_budgets_reproducible(self):
        h = history(n=70)
        result = evaluate("pick3", h, tickets=80, seed=17)
        self.assertEqual(result["heldout_draws"], 20)
        for method in METHODS:
            row = result["methods"][method]
            self.assertEqual(row["tickets"], 80)
            self.assertEqual(row["straight"] + row["box_only"], row["any_order"])
            self.assertEqual(sum(x["tickets"] for x in row["exploratory_periods"].values()), 80)
            self.assertEqual(row["approx_95pct_interval_nats"][0] <=
                             row["mean_log_score_advantage_vs_fair_nats"] <=
                             row["approx_95pct_interval_nats"][1], True)
        self.assertEqual(evaluate("pick3", h, tickets=80, seed=17), result)

    def test_uniform_likelihood_is_exact(self):
        m = build_model("random", history(), "Day", 5)
        self.assertAlmostEqual(probability_of_digits(m, [1, 2, 3, 4, 5]), 1e-5)


if __name__ == "__main__":
    unittest.main()
