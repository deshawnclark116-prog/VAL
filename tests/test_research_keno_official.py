import random,unittest
from research_keno_official import normalize,Counters,predict
from research_keno import PRIZE_FIVE_SPOT,exact_fair_match_probabilities,stable_rng
from val import generate,model_selection_weights

class ExpandedKenoTests(unittest.TestCase):
    def test_official_row_validation(self):
        d=dict(DrawGameId=30,DrawNumber=77,DrawDate="2026-11-17T08:00:00",
               DailyDraws=[dict(SelectedNumbers=dict(Value=list(range(1,21))),
                                InlineBonusValue=1)])
        self.assertEqual(normalize(d)["draw_id"],77)
        d["DailyDraws"][0]["SelectedNumbers"]["Value"]=[1]*20
        with self.assertRaises(ValueError):normalize(d)
    def test_exact_parity_with_original_VAL(self):
        rng=random.Random(11)
        h=[dict(numbers=sorted(rng.sample(range(1,81),20)),draw_id=i+101)
           for i in range(560)]
        for i in (30,50,400,500,550):
            c=Counters(h,i)
            past=[dict(numbers=q["numbers"],bonus=None,stream="Main")
                  for q in h[max(0,i-500):i]]
            for m in ("random","frequency","recent","cold","ensemble"):
                weights=c.weights(m)
                expected=model_selection_weights("keno",past,m)
                for x,y in zip(weights,expected):
                    self.assertAlmostEqual(x,y,places=12)
                number=stable_rng(20261117,m,h[i]["draw_id"])
                observed=predict(weights,number)
                baseline=generate("keno",[] if m=="random" else past,m,3,
                        stable_rng(20261117,m,h[i]["draw_id"]))
                self.assertEqual(observed,[a["numbers"] for a in baseline])
    def test_signed_2026_five_spot_prize(self):
        fair=exact_fair_match_probabilities()
        self.assertEqual(PRIZE_FIVE_SPOT[0],0)
        self.assertAlmostEqual(sum(fair[k]*PRIZE_FIVE_SPOT[k] for k in range(6)),.699933,places=5)

if __name__=="__main__":unittest.main()
