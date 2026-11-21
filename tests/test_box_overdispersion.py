"""Mathematical tests for research-only overdispersion Box formula."""
import math
import unittest
from itertools import combinations_with_replacement
from val_box import box_ways
from val_box_overdispersion import box_probability, ranked_boxes, distribution_log_gain

class TestOverdispersion(unittest.TestCase):
    def test_normalization_and_permutation_invariance(self):
        for n in (3,4,5):
            for concentration in (0.5, 2, 20, 1000):
                p=[.1]*10
                total=sum(box_probability(c,p,concentration)
                          for c in combinations_with_replacement(range(10),n))
                self.assertAlmostEqual(total,1.,places=9)
                self.assertAlmostEqual(box_probability((1,2,1) if n==3 else
                    tuple([1]*(n-1)+[2]),p,concentration),
                    box_probability((2,1,1) if n==3 else
                    tuple([2]+[1]*(n-1)),p,concentration),places=12)
    def test_repetition_is_not_iid(self):
        p=[.1]*10
        # Small concentration increases the probability of repeated digits.
        self.assertGreater(box_probability((1,1,1),p,2),
                           box_probability((1,1,1),p,1000))
    def test_fair_limit_and_distinct_top(self):
        p=[.1]*10
        for n in (3,4,5):
            combo=tuple(range(n))
            self.assertAlmostEqual(box_probability(combo,p,1e8),
                                   math.factorial(n)/10**n,delta=1e-7)
            tickets=ranked_boxes("pick"+str(n),p,1e8)
            self.assertEqual(len({tuple(x["numbers"]) for x in tickets}),3)
            self.assertTrue(all(len(set(x["numbers"]))==n for x in tickets))
    def test_ordered_log_score(self):
        self.assertTrue(math.isfinite(distribution_log_gain([1,1,2],[.1]*10,20)))

if __name__=="__main__":unittest.main()
