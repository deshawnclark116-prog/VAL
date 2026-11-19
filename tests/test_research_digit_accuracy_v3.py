import random
import unittest
from datetime import datetime,timedelta,timezone
from research_digit_accuracy_v3 import CANDIDATES,build,evaluate

def rows(game="pick3",n=660):
    width=int(game[-1]);rng=random.Random(12)
    at=datetime(2024,1,1,tzinfo=timezone.utc)
    return [dict(game=game,at=(at+timedelta(hours=12*i)).isoformat(),
             numbers=[rng.randrange(10) for j in range(width)],
             stream="Day" if i%2 else "Night") for i in range(n)]

class AccuracyResearchTests(unittest.TestCase):
    def test_joint_distribution_per_digit_position(self):
        for game in ("pick3","pick4","pick5"):
            h=rows(game,230)
            models=build(game,h,"Day",2,5)
            self.assertEqual(set(models),set(CANDIDATES))
            for name,pos in models.items():
                self.assertEqual(len(pos),int(game[-1]))
                for p in pos:
                    self.assertAlmostEqual(sum(p),1,places=9)
                    self.assertEqual(len(p),10)
                    self.assertTrue(all(0<x<1 for x in p))
    def test_strict_leakage(self):
        h=rows("pick3",230)
        first=build("pick3",h[:220],"Night",3,5)
        h[220]["numbers"]=[9,9,9]
        h[229]["numbers"]=[8,8,8]
        second=build("pick3",h[:220],"Night",3,5)
        self.assertEqual(first,second)
        h[219]["numbers"]=[0,0,0]
        self.assertNotEqual(first,build("pick3",h[:220],"Night",3,5))
    def test_future_evaluation_and_expected_baselines(self):
        h=rows("pick3",650)
        s=evaluate("pick3",h,train_min=200,predictions=400,calibration=150)
        self.assertEqual(s["later_targets"],250)
        for method in CANDIDATES:
            r=s["models"][method]["test"]
            self.assertEqual(r["forecasts"],250)
            self.assertEqual(r["expected_top1_position_rate_if_fair"],.1)
            self.assertEqual(r["expected_top3_position_rate_if_fair"],.3)
            self.assertLessEqual(r["top1_position_hits"],750)
            self.assertLessEqual(r["top3_position_hits"],750)

if __name__=="__main__":unittest.main()
