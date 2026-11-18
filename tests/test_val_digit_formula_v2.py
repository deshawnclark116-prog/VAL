import math
import random
import unittest
from datetime import datetime,timedelta,timezone

from val_digit_formula_v2 import (EXPERT_NAMES,BEAM_WIDTH,calibration,expert_models,
    forecast,generate_picks,joint_probability,log_gain,path_probability,_top_candidates)

def fixtures(game="pick3",n=810,seed=19):
    w=int(game[-1])
    rng=random.Random(seed)
    t=datetime(2025,1,1,tzinfo=timezone.utc)
    return [dict(game=game,at=(t+timedelta(hours=12*i)).isoformat(),
                 stream="Day" if i%2==0 else "Night",
                 numbers=[rng.randrange(10) for _ in range(w)])
            for i in range(n)]

class DigitFormulaTests(unittest.TestCase):
    def test_all_five_experts_define_valid_joint_distribution(self):
        for game in ("pick3","pick4","pick5"):
            hist=fixtures(game,90)
            experts=expert_models(game,hist,"Night")
            self.assertEqual(set(experts),set(EXPERT_NAMES))
            for name,m in experts.items():
                for dist in m["marginal"]:
                    self.assertAlmostEqual(sum(dist),1,places=11)
                    self.assertTrue(all(0<p<1 for p in dist))
                if m["within"]:
                    for block in m["within"][1:]:
                        for cond in block:self.assertAlmostEqual(sum(cond),1,places=11)
                if game=="pick3":
                    total=sum(path_probability(m,[a,b,c])
                              for a in range(10) for b in range(10) for c in range(10))
                    self.assertAlmostEqual(total,1,places=10)

    def test_past_isolation_and_future_outcomes_cannot_affect_predictions(self):
        h=fixtures(n=810)
        before=forecast("pick3",h[:800],"Day")
        mutated=fixtures(n=810)
        mutated[800]["numbers"]=[9,9,9]
        mutated[807]["numbers"]=[1,1,1]
        after=forecast("pick3",mutated[:800],"Day")
        self.assertEqual(before,after)
        altered=fixtures(n=810)
        altered[799]["numbers"]=[9,9,9]
        newer=forecast("pick3",altered[:800],"Day")
        self.assertNotEqual(before["experts"],newer["experts"])

    def test_fair_control_null_fallback_is_normalized_and_not_marketed_as_edge(self):
        h=fixtures()
        ready=forecast("pick3",h,"Day")
        self.assertEqual(ready["game"],"pick3")
        self.assertGreaterEqual(ready["signal_strength"],0)
        self.assertLessEqual(ready["signal_strength"],.5)
        total=sum(joint_probability(ready,[i,j,k])
                  for i in range(10) for j in range(10) for k in range(10))
        self.assertAlmostEqual(total,1,places=10)
        picks,meta=generate_picks("pick3",h,"Day",3,random.Random(77))
        self.assertEqual(len({tuple(x["numbers"]) for x in picks}),3)
        self.assertEqual(meta["signal_gate_passed"],ready["gate_passed"])
        for pick in picks:
            self.assertEqual(pick["signal_gate_passed"],ready["gate_passed"])
            self.assertAlmostEqual(pick["model_weight_score"],
                joint_probability(ready,pick["numbers"]))
        if not ready["gate_passed"]:
            self.assertAlmostEqual(log_gain(ready,[0,1,2]),0,places=10)
            self.assertEqual(meta["signal_strength"],0)

    def test_best_candidate_selection_when_gate_active(self):
        h=fixtures(n=90)
        fake=dict(version="digit_conditional_v2",game="pick3",stream="Day",
                  experts=expert_models("pick3",h,"Day"),
                  weights={"long_1500":1.},signal_strength=.5,
                  gate_passed=True)
        selected=_top_candidates(fake,3)
        ordered=sorted([(joint_probability(fake,[a,b,c]),(a,b,c))
                        for a in range(10) for b in range(10) for c in range(10)],
                       reverse=True)
        self.assertEqual(selected,[z[1] for z in ordered[:3]])

    def test_no_future_data_in_calibration(self):
        h=fixtures(n=650)
        a=calibration("pick3",h)
        self.assertIn("experts",a)
        self.assertEqual(set(a["experts"]),set(EXPERT_NAMES))
        self.assertGreater(a["observations"],0)
        self.assertEqual(a,calibration("pick3",h))
        self.assertTrue(all(math.isfinite(x["mean_gain"]) for x in a["experts"].values()))

    def test_rejects_non_digit_game(self):
        with self.assertRaises(ValueError):expert_models("cash5",fixtures(), "Main")

if __name__=="__main__":
    unittest.main()
