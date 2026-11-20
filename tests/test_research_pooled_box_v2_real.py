"""Regression for real-draw complete Any Order evaluation; no partial hits."""
import math
import random
import unittest
from datetime import date,timedelta

from research_pooled_box_v2_real import (
    v1_rotations,unique_box_prob,bernoulli_upper_tail,
    evaluate,seeded
)
from val_pooled_box_formula import generate
from val_box import digits_key


class RealOutcomeTests(unittest.TestCase):
    def test_rotations_are_not_three_independent_box_opportunities(self):
        uniform=[.1]*10
        v1=v1_rotations(uniform,3)
        self.assertEqual(len({digits_key(v) for v in v1}),1)
        self.assertAlmostEqual(unique_box_prob("pick3",v1),.006,places=12)
        self.assertAlmostEqual(unique_box_prob("pick4",v1_rotations(uniform,4)),
                               .0036,places=12)
        self.assertAlmostEqual(unique_box_prob("pick5",v1_rotations(uniform,5)),
                               .0009,places=12)

    def test_exact_null_probability_tail(self):
        self.assertAlmostEqual(bernoulli_upper_tail([.2,.2],1),.36)
        self.assertAlmostEqual(bernoulli_upper_tail([.2,.2],2),.04)
        self.assertAlmostEqual(bernoulli_upper_tail([.2,.2],0),1.)
        self.assertAlmostEqual(bernoulli_upper_tail([0.]*100,1),0.)
        self.assertAlmostEqual(bernoulli_upper_tail([1.],1),1.)

    def test_picks_depend_on_past_only(self):
        rows=[]
        rng=random.Random(87)
        start=date(2023,10,1)
        for i in range(1100):
            rows.append(dict(date=(start+timedelta(days=i//2)).isoformat(),
                             stream="Day" if i%2==0 else "Night",
                             numbers=[rng.randrange(10) for _ in range(3)]))
        for i in (520,740,1099):
            target=rows[i]
            a=generate("pick3",rows[:i],3,seeded("pick3",target))
            changed=[dict(r) for r in rows]
            changed[i]["numbers"]=[9,9,9]
            changed[-1]["numbers"]=[0,0,0]
            b=generate("pick3",changed[:i],3,seeded("pick3",target))
            self.assertEqual(a,b)

    def test_genuine_full_box_grading_prequential(self):
        rng=random.Random(701)
        start=date(2024,1,1)
        rows=[dict(date=(start+timedelta(days=i//2)).isoformat(),
                   stream="Day" if i%2==0 else "Night",
                   numbers=[rng.randrange(10) for _ in range(3)])
              for i in range(750)]
        result=evaluate("pick3",rows)
        self.assertEqual(result["total_scored_targets"],18)
        for r in result["events"]:
            self.assertEqual(r["v2_unique"],3)
            self.assertEqual(r["random_unique"],3)
            self.assertEqual(r["v1_unique"],1)
            self.assertAlmostEqual(r["v2_fair_prob"],.018,places=12)
            self.assertAlmostEqual(r["random_fair_prob"],.018,places=12)
            self.assertAlmostEqual(r["v1_fair_prob"],.006,places=12)
            self.assertIn(r["v2_win"],(0,1))
            self.assertIn(r["random_win"],(0,1))


if __name__=="__main__":
    unittest.main()
