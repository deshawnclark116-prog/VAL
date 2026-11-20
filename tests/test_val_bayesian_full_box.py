"""Leak-safe verification of direct complete Box probability models."""
import math
import random
import unittest
from itertools import combinations_with_replacement
from val_bayesian_full_box import (
    BayesianBox,combos,METHODS,EXACT_PRIOR_DRAWS,PAIR_PRIOR_DRAWS
)
from val_box import box_ways,digits_key


class StructuralBoxTests(unittest.TestCase):
    def test_every_joint_box_distribution_normalized_including_repeats(self):
        for game in ("pick3","pick4","pick5"):
            m=BayesianBox(game)
            for step in range(70):
                m.observe({"numbers":[(step+i*3)%10 for i in
                                       range(int(game[-1]))]})
            predictions=m.predict()
            self.assertEqual(set(predictions),set(METHODS))
            for name,snapshot in predictions.items():
                dist=snapshot["distribution"]
                self.assertAlmostEqual(sum(dist.values()),1.,places=10)
                self.assertTrue(all(x>0 for x in dist.values()))
                self.assertEqual(len(snapshot["picks"]),3)
                self.assertEqual(
                    len({digits_key(p) for p in snapshot["picks"]}),3)
                self.assertEqual(
                    len(dist),math.comb(10+int(game[-1])-1,int(game[-1])))

    def test_fair_model_exactly_counts_full_set_permutations(self):
        for game in ("pick3","pick4","pick5"):
            m=BayesianBox(game)
            p=m.distributions()["fair"]
            for key,q,pairs,eligible in combos(game):
                self.assertAlmostEqual(p[key],box_ways(key)/10**len(key))
                self.assertEqual(len(pairs),len(key)*(len(key)-1)//2)

    def test_model_finds_favored_complete_box_without_digit_position_signal(self):
        # Repeatedly selecting one unordered BOX key creates genuine
        # high-order structure rather than a general hot-digit score.
        rng=random.Random(212)
        m=BayesianBox("pick3")
        favorite=(0,5,9)
        for _ in range(1400):
            if rng.random()<.08:
                sample=list(favorite)
                rng.shuffle(sample)
            else:
                sample=[rng.randrange(10) for _ in range(3)]
            m.observe({"numbers":sample})
        predictions=m.predict()
        self.assertIn(list(favorite),predictions["exact_bag"]["picks"])
        self.assertGreater(
            predictions["exact_bag"]["distribution"][favorite],
            predictions["fair"]["distribution"][favorite]*2)

    def test_prior_only_without_observations_equals_fair(self):
        for game in ("pick3","pick4","pick5"):
            d=BayesianBox(game).distributions()
            for name in METHODS:
                for key,p in d["fair"].items():
                    self.assertAlmostEqual(d[name][key],p,places=11)

    def test_past_only_forecast_and_rolling_expiration(self):
        rng=random.Random(8199)
        a=BayesianBox("pick3",window=100)
        b=BayesianBox("pick3",window=100)
        old=[[rng.randrange(10) for _ in range(3)] for _ in range(180)]
        for draw in old:
            a.observe({"numbers":draw})
        for draw in old[-100:]:
            b.observe({"numbers":draw})
        self.assertEqual(a.predict(),b.predict())
        frozen=a.predict()
        # The result can change the future, never the snapshot already made.
        a.observe({"numbers":[9,9,9]})
        self.assertEqual(b.predict(),frozen)

    def test_pairwise_correlation_changes_model_without_necessarily_changing_marginals(self):
        m=BayesianBox("pick3")
        rng=random.Random(47)
        for _ in range(1500):
            d=rng.randrange(10)
            m.observe({"numbers":[d,d,d]})
        p=m.distributions()
        key=(2,2,2)
        self.assertGreater(p["pair_shape"][key],p["fair"][key]*2)
        self.assertLess(abs(p["pooled"][key]-p["fair"][key]),1e-3)


if __name__=="__main__":
    unittest.main()
