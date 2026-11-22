import math
import unittest
from val_online_box_mixture import OnlineBoxMixture, EXPERTS
from val_bayesian_full_box import BayesianBox


class TestOnlineBoxMixture(unittest.TestCase):
    def test_all_games_normalize_and_fair_floor(self):
        for game in ("pick3", "pick4", "pick5"):
            with self.subTest(game=game):
                model = OnlineBoxMixture(game)
                forecast = model.predict()
                fair = model.machine.distributions()["fair"]
                self.assertAlmostEqual(sum(forecast["distribution"].values()), 1)
                self.assertEqual(len(forecast["picks"]), 3)
                self.assertEqual(len(set(map(tuple, forecast["picks"]))), 3)
                for key, probability in forecast["distribution"].items():
                    self.assertGreaterEqual(probability + 1e-15, .5 * fair[key])

    def test_no_future_observation_in_frozen_prediction(self):
        model = OnlineBoxMixture("pick3")
        for i in range(100):
            model.observe({"numbers": [1, 1, 9] if i % 2 else [1, 2, 3]})
        before = model.predict()
        old = dict(before["distribution"])
        old_weights = dict(model.log_weights)
        # Forecast and expert scores remain fixed until observe.
        self.assertEqual(model.predict()["distribution"], old)
        self.assertEqual(model.log_weights, old_weights)
        model.observe({"numbers": [1, 1, 9]})
        self.assertIsNone(model.frozen)
        self.assertNotEqual(model.log_weights, old_weights)
        self.assertEqual(model.machine.counts[(1, 1, 9)], 1)

    def test_discounted_expert_update_is_past_only(self):
        # Compare the exact prequential recurrence against the frozen
        # probability of the observed complete unordered outcome.
        for discount in (1.0, 0.95):
            model = OnlineBoxMixture("pick3", discount=discount)
            row = {"numbers": [1, 1, 9]}
            model.predict()
            frozen = {name: model.frozen[name][(1, 1, 9)]
                      for name in EXPERTS}
            model.observe(row)
            for name in EXPERTS:
                self.assertAlmostEqual(model.log_weights[name],
                                       math.log(frozen[name]))
            previous = dict(model.log_weights)
            model.predict()
            frozen2 = {name: model.frozen[name][(1, 1, 9)]
                       for name in EXPERTS}
            model.observe(row)
            for name in EXPERTS:
                self.assertAlmostEqual(
                    model.log_weights[name],
                    discount * previous[name] + math.log(frozen2[name]))
            self.assertIsNone(model.frozen)

    def test_invalid_hyperparameters(self):
        for floor, rate in ((-0.1, .25), (1.1, .25), (.5, 0), (.5, 1.1)):
            with self.assertRaises(ValueError):
                OnlineBoxMixture("pick3", floor, rate)
        for discount in (0, -0.01, 1.01):
            with self.assertRaises(ValueError):
                OnlineBoxMixture("pick3", discount=discount)


if __name__ == "__main__":
    unittest.main()
