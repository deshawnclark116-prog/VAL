import random
import unittest

import numpy as np

from research_tuned_ultimate import SOURCES, features
from val_ultimate import HOT_WINDOW, SOURCE_ORDER, ultimate_digit_pick, weighted_digit_pick


class TunedPickTests(unittest.TestCase):
    def test_matches_research_scoring(self):
        self.assertEqual(SOURCES, SOURCE_ORDER)
        rng = random.Random(9)
        hist = [dict(numbers=[rng.randrange(10) for _ in range(4)]) for _ in range(HOT_WINDOW + 30)]
        votes, tiebreak, _ = features(hist, 4)
        for weights in ([0, 2, 1, 3, 0, 3, 0], [1] * 7, [3, 0, 0, 1, 2, 0, 1]):
            scores = np.einsum("s,nsd->nd", np.array(weights, float), votes) + tiebreak
            for j in range(30):
                i = HOT_WINDOW + j
                expected = sorted(np.argsort(-scores[j])[:4].tolist())
                self.assertEqual(weighted_digit_pick(hist[:i], 4, weights)["numbers"], expected)

    def test_equal_weights_equal_ultimate(self):
        rng = random.Random(2)
        hist = [dict(numbers=[rng.randrange(10) for _ in range(4)]) for _ in range(150)]
        self.assertEqual(weighted_digit_pick(hist, 4, [1] * 7)["numbers"], ultimate_digit_pick(hist, 4)["numbers"])


if __name__ == "__main__":
    unittest.main()
