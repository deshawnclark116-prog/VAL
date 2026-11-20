import random
import math
import unittest

import val
from val_box import (
    BOX_PRIZES_USD,box_ways,digits_key,any_order_prize,
    fair_any_order_probability,is_any_order_win,random_box_picks,
    distinct_permutations,box_score_batch
)

class AnyOrderLotteryTests(unittest.TestCase):
    def test_duplicates_and_zeros_remain_in_the_box_key(self):
        self.assertEqual(digits_key([0,1,1]),(0,1,1))
        self.assertEqual(digits_key([1,0,1]),(0,1,1))
        self.assertNotEqual(digits_key([1,0,1]),digits_key([1,0,0]))
        self.assertTrue(is_any_order_win("pick3",[1,0,1],[0,1,1]))
        self.assertFalse(is_any_order_win("pick3",[1,0,1],[0,1,0]))
    def test_official_any_order_permutation_classes(self):
        self.assertEqual(box_ways([1,2,3]),6)
        self.assertEqual(box_ways([1,1,2]),3)
        self.assertEqual(box_ways([1,1,1]),1)
        self.assertEqual(box_ways([1,1,1,2]),4)
        self.assertEqual(box_ways([1,1,2,2]),6)
        self.assertEqual(box_ways([1,1,2,3]),12)
        self.assertEqual(box_ways([1,2,3,4]),24)
        for digits,ways in [
            ([1,1,1,1,2],5),([1,1,1,2,2],10),
            ([1,1,1,2,3],20),([1,1,2,2,3],30),
            ([1,1,2,3,4],60),([1,2,3,4,5],120)
        ]:
            self.assertEqual(box_ways(digits),ways)
            self.assertEqual(len(distinct_permutations(digits)),ways)
        self.assertEqual(any_order_prize("pick3",[1,1,2]),160)
        self.assertEqual(any_order_prize("pick3",[1,2,3]),80)
        self.assertEqual(any_order_prize("pick4",[1,1,2,3]),400)
        self.assertEqual(any_order_prize("pick5",[1,2,3,4,5]),400)
        self.assertEqual(any_order_prize("pick5",[1,1,1,1,1]),0)
        self.assertFalse(is_any_order_win("pick5",[1]*5,[1]*5))
    def test_real_box_win_requires_all_digits_not_some_positions(self):
        picks=[{"numbers":[4,5,9,8],"bonus":None},
               {"numbers":[8,9,4,4],"bonus":None},
               {"numbers":[1,0,8,4],"bonus":None}]
        draw={"numbers":[4,4,9,8],"bonus":None}
        s=val.score_batch("pick4",picks,draw)
        self.assertEqual(s["box_wins"],1)
        self.assertEqual(s["exact"],0)
        self.assertEqual(s["box_payout_usd"],1200)
        self.assertEqual(s["box_spend_usd"],3)
        self.assertEqual(s["box_net_usd"],1197)
        self.assertFalse(val.score("pick4",picks[0],draw)["box"])
        self.assertTrue(val.score("pick4",picks[1],draw)["box"])
    def test_box_vs_straight_same_digits_different_order(self):
        p={"numbers":[1,0,1],"bonus":None}
        draw={"numbers":[0,1,1],"bonus":None}
        r=val.score("pick3",p,draw)
        self.assertTrue(r["box"])
        self.assertFalse(r["exact"])
        b=val.score_batch("pick3",[p],draw)
        self.assertEqual(b["box_wins"],1)
        self.assertEqual(b["box_payout_usd"],160)
        self.assertEqual(b["box_spend_usd"],1)
        self.assertEqual(b["box_net_usd"],159)
        self.assertAlmostEqual(fair_any_order_probability("pick3",p["numbers"]),.003)
    def test_random_control_cost_and_coverage_are_matched(self):
        for game in ("pick3","pick4","pick5"):
            a=random_box_picks(game,3,random.Random(42))
            b=random_box_picks(game,3,random.Random(42))
            self.assertEqual(a,b)
            self.assertEqual(len({digits_key(p["numbers"]) for p in a}),3)
            self.assertTrue(all(len(set(p["numbers"]))==int(game[-1]) for p in a))
            for p in a:
                self.assertGreater(any_order_prize(game,p["numbers"]),0)
            summary=box_score_batch(game,a,{"numbers":[0]*int(game[-1])})
            self.assertEqual(summary["box_spend_usd"],3)
            self.assertEqual(summary["box_wins"],0)
            self.assertAlmostEqual(summary["box_fair_at_least_one_prob"],
                                   3*math.factorial(int(game[-1]))/10**int(game[-1]))
    def test_partial_match_never_claimed_as_box_win(self):
        p={"numbers":[4,5,9,8],"bonus":None}
        d={"numbers":[4,4,9,8],"bonus":None}
        r=val.score("pick4",p,d)
        self.assertEqual(r["matches"],3)
        self.assertFalse(r["box"])
        self.assertFalse(r["exact"])

if __name__=="__main__":unittest.main()
