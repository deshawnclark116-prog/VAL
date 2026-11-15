import random
import unittest

from research_10k import evaluate, fair_box_probability, labels
from val import METHODS


def draw(numbers, i, fireball=9):
    return {"game": "pick3", "at": f"2026-01-{i + 1:02d}T23:00:00+00:00",
            "stream": "Night", "numbers": numbers, "bonus": None, "extra": fireball}


class Research10KTests(unittest.TestCase):
    def test_digit_multiplicity_and_box(self):
        d = draw([0, 1, 1], 1)
        self.assertEqual(labels({"numbers": [1, 0, 1]}, d)[:2], (False, True))
        self.assertEqual(labels({"numbers": [0, 1, 1]}, d)[:2], (True, True))
        self.assertEqual(labels({"numbers": [0, 0, 1]}, d)[:2], (False, False))
        self.assertEqual(fair_box_probability({"numbers": [1, 1, 2]}), 3 / 1000)
        self.assertEqual(fair_box_probability({"numbers": [1, 2, 3]}), 6 / 1000)

    def test_fireball_is_one_replacement_only(self):
        d = draw([6, 8, 4], 1, fireball=2)
        self.assertEqual(labels({"numbers": [2, 8, 4]}, d), (False, False, True, True))
        self.assertEqual(labels({"numbers": [4, 2, 8]}, d), (False, False, False, True))
        self.assertEqual(labels({"numbers": [2, 2, 8]}, d)[2:], (False, False))

    def test_exact_ticket_budget_and_chronology(self):
        rng = random.Random(21)
        history = [draw(rng.choices(range(10), k=3), i % 28) for i in range(85)]
        # Date strings are synthetic; only pre-draw row ordering matters for this test.
        result = evaluate("pick3", history, tickets=140, train=50, seed=123)
        self.assertEqual(result["distinct_held_out_draws"], 35)
        self.assertEqual(result["ticket_allocation_per_draw"], [4, 4])
        for method in METHODS:
            row = result["methods"][method]
            self.assertEqual(row["tickets"], 140)
            self.assertEqual(row["straight"] + row["box_only"],
                             row["any_order_including_straight"])
            self.assertGreaterEqual(row["fireball_any_order"], row["fireball_straight"])
        self.assertEqual(result, evaluate("pick3", history, tickets=140, train=50, seed=123))

    def test_overallocating_raises(self):
        rng = random.Random(22)
        history = [draw(rng.choices(range(10), k=3), i % 28) for i in range(85)]
        with self.assertRaises(ValueError):
            evaluate("pick3", history, tickets=736, train=50)


if __name__ == "__main__":
    unittest.main()
