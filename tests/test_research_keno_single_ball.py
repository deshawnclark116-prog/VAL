import random,unittest
from research_keno_single_ball import (
    get_rows,train_models,pick_one,choose_max,evaluate,
    wilson,binomial_approx_p,paired_p,MODEL_NAMES,TEST_NAMES
)
from research_keno_official import Counters

def synthetic(n=5200):
    rng=random.Random(57)
    rows=[]
    for i in range(n):
        rows.append(dict(draw_id=9000+i,
                         timestamp="2026-10-01T12:00:00",
                         date="2026-10-01",
                         numbers=sorted(rng.sample(range(1,81),20))))
    return rows

class SingleBallKenoTests(unittest.TestCase):
    def test_math_and_tie_break(self):
        self.assertAlmostEqual(binomial_approx_p(100,400),1.0)
        a=wilson(100,400)
        self.assertTrue(a[0]<.25<a[1])
        p=paired_p([True,False],[False,True],2)
        self.assertEqual(p["discordants"],2)
        self.assertEqual(choose_max({i:2 for i in range(1,81)},"hot",101),
                         choose_max({i:2 for i in range(1,81)},"hot",101))

    def test_single_ball_no_leakage(self):
        rows=synthetic(5200)
        cut=int(len(rows)*.6)
        fit=train_models(rows[:cut])
        roll=Counters(rows,cut)
        for m in TEST_NAMES:
            n=pick_one(m,rows[cut],rows[cut-1],roll,fit,rows[:cut])
            self.assertTrue(type(n)==int and 1<=n<=80)
        result=evaluate(rows,controls=3)
        self.assertEqual(result["testing_draws"],2080)
        for m,v in result["results"].items():
            self.assertEqual(v["draws"],2080)
            self.assertEqual(v["hits"]+v["misses"],2080)
            self.assertEqual(v["first_half"]["hits"]+v["second_half"]["hits"],v["hits"])

if __name__=="__main__":unittest.main()
