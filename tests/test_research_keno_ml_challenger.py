import math,random,unittest
import numpy as np
from research_keno_ml_challenger import (
  build_dataset, normalized_prob, calibrate, brier, pick_one,
  day_cluster_interval, score, FEATURE_NAMES
)

def draws(n=30):
    rand=random.Random(511)
    rows=[]
    for i in range(n):
        nums=sorted(rand.sample(range(1,81),20))
        rows.append(dict(draw_id=7000+i,timestamp="2026-11-01T12:00:00",
                         date="2026-11-01",numbers=nums))
    return rows

class AdvancedMLTests(unittest.TestCase):
    def test_no_future_number_leakage(self):
        rows=draws(35)
        x1,y1=build_dataset(rows)
        changed=draws(35)
        changed[18]["numbers"]=list(range(1,21))
        x2,y2=build_dataset(changed)
        # The test draw's features are built before its result exists.
        np.testing.assert_array_equal(x1[:19],x2[:19])
        self.assertFalse(np.array_equal(y1[18],y2[18]))
        # Subsequent features SHOULD now change because results become known.
        self.assertFalse(np.array_equal(x1[19],x2[19]))
        self.assertEqual(x1.shape,(35,80,len(FEATURE_NAMES)))
        self.assertTrue(np.all(y1.sum(axis=1)==20))
    def test_one_ball_probabilities_per_draw_sum_20(self):
        raw=np.tile(np.linspace(.1,.4,80),(3,1))
        for alpha in (0,.25,.5,.75,1):
            p=calibrate(raw,alpha)
            self.assertEqual(p.shape,(3,80))
            np.testing.assert_allclose(p.sum(axis=1),20,atol=1e-8)
            self.assertTrue(np.all(p>0))
            self.assertTrue(np.all(p<1))
            guess=pick_one(p,[300,301,302],"unit")
            self.assertEqual(len(guess),3)
            self.assertTrue(all(1<=x<=80 for x in guess))
    def test_fair_brier_and_bootstrap(self):
        fair=np.full((4,80),.25)
        y=np.zeros((4,80))
        for k in range(4):y[k,k*20:k*20+20]=1
        self.assertAlmostEqual(brier(fair,y),.1875)
        ci=day_cluster_interval([.1,.1,.2,.2,.3,.3],
                                ["a","a","b","b","c","c"])
        self.assertTrue(ci[0]<=.2<=ci[1])
    def test_detects_strong_synthetic_bias(self):
        # A genuine biased generator is easy for the probability score to
        # distinguish from fair guessing: first ball ALWAYS appears.
        y=np.zeros((100,80))
        y[:,0]=1
        for i in range(100):
            y[i,1+i%79]=1
        pred=np.full((100,80),.25)
        pred[:,0]=.75
        pred=normalized_prob(pred)
        # The targeted ball prediction hits 100% in this controlled case.
        winning=np.array([bool(y[i,int(ball)-1]) for i,ball in
                          enumerate(pick_one(pred,np.arange(100)+2000,"biased"))])
        self.assertEqual(winning.sum(),100)

if __name__=="__main__":unittest.main()
