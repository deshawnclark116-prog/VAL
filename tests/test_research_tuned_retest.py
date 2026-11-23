import random
import unittest

from research_tuned_retest import evaluate, markdown


def fake_history(width, n, seed=1):
    rng = random.Random(seed)
    return [dict(at=f"{1995 + i * 32 // n}-06-01T12:00:00+00:00",
                 numbers=[rng.randrange(10) for _ in range(width)]) for i in range(n)]


class RetestTests(unittest.TestCase):
    def test_rounds_never_tune_on_their_test_years(self):
        row = evaluate("pick3", fake_history(3, 3300))
        self.assertTrue(row["rounds"])
        self.assertTrue(all(r["tuned_before"] == r["test"][:4] for r in row["rounds"]))
        self.assertEqual(len(row["stretches"]), 4)
        self.assertIn("retest", markdown([row], "now"))


if __name__ == "__main__":
    unittest.main()
