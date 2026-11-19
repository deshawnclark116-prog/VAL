import random
import unittest
from datetime import datetime,timedelta,timezone
from research_pooled_digit_ablation import formulas,examine,MODELS

class PooledAblationTests(unittest.TestCase):
    def test_normalized_formula_families(self):
        a=[2]*10
        s={"Day":a[:],"Night":[0]*10}
        model=formulas("pick3",a,s,a,s,"Night")
        self.assertEqual(set(model),set(MODELS))
        for name,p in model.items():
            self.assertAlmostEqual(sum(p),1)
            self.assertTrue(all(0<z<1 for z in p))
    def test_day_night_forecasts_strictly_prior(self):
        rng=random.Random(20)
        t=datetime(2025,1,1,tzinfo=timezone.utc)
        h=[dict(game="pick3",at=(t+timedelta(hours=12*i)).isoformat(),
                numbers=[rng.randrange(10) for _ in range(3)],
                stream="Day" if i%2 else "Night") for i in range(850)]
        a=examine("pick3",h)
        self.assertEqual(a["models"]["global_5000"]["all"]["draws"],350)
        self.assertEqual(a["models"]["global_5000"]["all"]["draws"],
                         a["models"]["stream_5000"]["all"]["draws"])
        changed=[dict(row) for row in h]
        changed[-1]["numbers"]=[9,9,9]
        b=examine("pick3",changed)
        self.assertNotEqual(a["models"]["global_5000"]["all"],
                            b["models"]["global_5000"]["all"])

if __name__=="__main__":unittest.main()
