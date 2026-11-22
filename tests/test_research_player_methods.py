import random
import unittest

from research_player_methods import evaluate, judge, markdown, poisson_upper


def history(game_width, n, seed=1):
    rng = random.Random(seed)
    return [dict(at=f"2020-01-01T00:00:{i:02d}+00:00" if i < 60 else "2020-01-02T00:00:00+00:00",
                 numbers=[rng.randrange(10) for _ in range(game_width)]) for i in range(n)]


class ResearchPlayerMethodsTests(unittest.TestCase):
    def test_poisson_upper(self):
        self.assertEqual(poisson_upper(2.0, 0), 1.0)
        self.assertAlmostEqual(poisson_upper(1.0, 1), 1 - 0.36787944, places=6)
        self.assertLess(poisson_upper(1.0, 10), 1e-6)

    def test_counts_only_use_earlier_draws(self):
        # Mirror of the previous draw always predicts the next draw exactly here.
        draws = [dict(at="2020-01-01T00:00:00+00:00", numbers=[1, 2, 3])]
        for _ in range(20):
            draws.append(dict(at="2020-01-01T00:00:00+00:00", numbers=[(d + 5) % 10 for d in draws[-1]["numbers"]]))
        rows = {r["method"]: r for r in evaluate("pick3", draws)}
        self.assertEqual(rows["player_mirror"]["draws"], 18)
        self.assertEqual(rows["player_mirror"]["straight_hits"], 18)
        flagged = judge(list(rows.values()))
        mirror = next(r for r in flagged if r["method"] == "player_mirror")
        self.assertIn("more than luck", mirror["verdict"])

    def test_random_history_looks_like_luck(self):
        rows = judge(evaluate("pick3", history(3, 3000)))
        self.assertEqual(len(rows), 5)
        for r in rows:
            self.assertEqual(r["draws"], 2997)
            self.assertGreater(r["box_expected"], 0)
        self.assertIn("Popular player methods", markdown(rows, "now"))


if __name__ == "__main__":
    unittest.main()
