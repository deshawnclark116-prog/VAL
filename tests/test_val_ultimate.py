import random
import unittest

from val import GAMES
from val_ultimate import max_run, spread_pick, ultimate_digit_pick, ultimate_pick

HISTORY = [dict(numbers=n) for n in ([5, 7, 2], [3, 1, 8], [9, 0, 4], [5, 5, 1], [7, 2, 5])]


class UltimateTests(unittest.TestCase):
    def test_digit_pick_is_distinct_and_repeatable(self):
        for width in (3, 4, 5):
            hist = [dict(numbers=[random.Random(i).randrange(10) for _ in range(width)]) for i in range(300)]
            pick = ultimate_digit_pick(hist, width)
            self.assertEqual(len(set(pick["numbers"])), width)
            self.assertEqual(pick["numbers"], sorted(pick["numbers"]))
            self.assertEqual(pick, ultimate_digit_pick(hist, width))

    def test_needs_history(self):
        with self.assertRaises(ValueError):
            ultimate_digit_pick(HISTORY[:2], 3)

    def test_spread_pick_avoids_common_patterns(self):
        rng = random.Random(3)
        for game in ("cash5", "powerball", "megamillions", "millionaireforlife", "bankamillion", "cashpop"):
            g = GAMES[game]
            for _ in range(50):
                pick = spread_pick(game, rng)
                nums = pick["numbers"]
                self.assertEqual(len(set(nums)), g["size"])
                self.assertTrue(all(1 <= n <= g["pool"] for n in nums))
                self.assertLess(max_run(nums), 3)
                if g["pool"] > 31 and g["size"] > 1:
                    self.assertGreaterEqual(sum(n > 31 for n in nums), 2)
                self.assertEqual(pick["bonus"] is None, not g.get("bonus"))

    def test_ultimate_pick_routes_by_game(self):
        self.assertEqual(len(ultimate_pick("pick3", HISTORY)[0]["numbers"]), 3)
        self.assertEqual(len(ultimate_pick("powerball", [])[0]["numbers"]), 5)


if __name__ == "__main__":
    unittest.main()
