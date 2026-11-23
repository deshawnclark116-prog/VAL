import random
import unittest

import numpy as np

from research_tuned_ultimate import SOURCES, evaluate, features, hits_for, markdown
from val_ultimate import HOT_WINDOW, ultimate_digit_pick


def fake_history(width, n, seed=1):
    rng = random.Random(seed)
    return [dict(at=f"{2000 + i * 26 // n}-01-01T12:00:00+00:00",
                 numbers=[rng.randrange(10) for _ in range(width)]) for i in range(n)]


class TunedUltimateTests(unittest.TestCase):
    def test_equal_weights_reproduce_live_ultimate_pick(self):
        for width in (3, 4, 5):
            hist = fake_history(width, HOT_WINDOW + 40, seed=width)
            votes, tiebreak, _ = features(hist, width)
            scores = votes.sum(axis=1) + tiebreak
            for j in range(40):
                i = HOT_WINDOW + j
                live = ultimate_digit_pick(hist[i - HOT_WINDOW:i], width)["numbers"]
                self.assertEqual(sorted(np.argsort(-scores[j])[:width].tolist()), live)

    def test_hits_count_only_exact_box_matches(self):
        votes = np.zeros((2, len(SOURCES), 10)); votes[:, 0, [1, 2, 3]] = 1
        tiebreak = np.zeros((2, 10))
        target = np.array([(1 << 1) + (1 << 2) + (1 << 3), -1])
        self.assertEqual(hits_for(np.ones((1, len(SOURCES))), votes, tiebreak, target, 3).tolist(), [1])

    def test_evaluate_runs_and_reports(self):
        row = evaluate("pick3", fake_history(3, 2600))
        self.assertGreater(row["test_draws"], 0)
        self.assertEqual(row["weightings_tried"], 4 ** len(SOURCES) - 1)
        self.assertIn("Tuned ultimate generator", markdown([row], "now"))


if __name__ == "__main__":
    unittest.main()
