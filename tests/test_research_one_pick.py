import copy
import math
import random
import unittest

from research_one_pick import (
    Rolling, build_probabilities, choose_one, evaluate, fair_box_probability_digits
)


def history(game="pick3", n=90):
    rng = random.Random(123)
    return [{
        "date": f"{2000 + i//365:04d}-{i%28+1:02d}-04",
        "stream": "Day" if i%2==0 else "Night",
        "numbers": [rng.randrange(10) for _ in range(int(game[-1]))],
        "fireball": i%10 if i>=40 else None
    } for i in range(n)]


class OnePickResearchTests(unittest.TestCase):
    def test_rolling_window_is_exact_with_no_future_rows(self):
        h = history(n=80)
        tracker=Rolling(h[:30],3,30)
        for target_index in range(30,70):
            previous=h[target_index-30:target_index]
            self.assertEqual(tracker.n,30)
            for position in range(3):
                for digit in range(10):
                    expected=sum(row["numbers"][position]==digit for row in previous)
                    self.assertEqual(tracker.position[position][digit],expected)
            for session in ("Day","Night"):
                self.assertEqual(tracker.stream_count[session],sum(row["stream"]==session for row in previous))
            tracker.add(h[target_index])
            tracker.remove(h[target_index-30])

    def test_all_distributions_valid_and_positive(self):
        h=history()
        rolling=Rolling(h[:30],3,30)
        for family in ("position_hot","position_cold","pooled_hot","session_hier"):
            p=rolling.probabilities(family,"Night")
            self.assertEqual(len(p),3)
            for row in p:
                self.assertAlmostEqual(sum(row),1)
                self.assertTrue(all(x>0 for x in row))
            self.assertEqual(len(choose_one(p,"top",random.Random(4))),3)
            self.assertEqual(len(choose_one(p,"sample",random.Random(4))),3)

    def test_box_probability_adjusts_digit_repetitions(self):
        self.assertAlmostEqual(fair_box_probability_digits([1,1,2]),3/1000)
        self.assertAlmostEqual(fair_box_probability_digits([1,2,3]),6/1000)
        self.assertAlmostEqual(fair_box_probability_digits([0,0,0,0,0]),1/100000)
        self.assertAlmostEqual(fair_box_probability_digits([1,2,3,4,5]),120/100000)

    def test_one_exact_pick_per_target_per_method(self):
        h=history(n=70)
        a=evaluate("pick3",h,windows=(20,30),seed=42)
        b=evaluate("pick3",h,windows=(20,30),seed=42)
        self.assertEqual(a,b)
        self.assertEqual(a["walk_forward_draws"],40)
        for name,info in a["models"].items():
            self.assertEqual(info["all"]["draws_and_tickets"],40)
            self.assertEqual(info["all"]["straight"]+info["all"]["box_only"],
                             info["all"]["any_order_including_straight"])
            self.assertEqual(sum(x["draws_and_tickets"] for x in info["by_period"].values()),40)
        self.assertGreater(a["models"]["random_distinct"]["all"]["expected_any_order_if_fair"],
                           a["models"]["random"]["all"]["expected_any_order_if_fair"])

    def test_heldout_changes_do_not_change_previous_prediction_window(self):
        h=history(n=80)
        prior=Rolling(h[:30],3,30)
        baseline=prior.probabilities("session_hier","Day")
        future=copy.deepcopy(h)
        future[30]["numbers"]=[9,9,9]
        retrain=Rolling(future[:30],3,30)
        self.assertEqual(baseline,retrain.probabilities("session_hier","Day"))


if __name__ == "__main__":unittest.main()
