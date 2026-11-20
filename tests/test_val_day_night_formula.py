"""Tests for genuinely conditional Day-to-Night full-Box formula."""
import math
import random
import unittest

from research_virtual_draw_lab import simulate
from val_box import box_ways, distinct_permutations
from val_day_night_formula import (
    _NightCounts, NightConditionalEvidence, fit_before,
    optimal_boxes, full_box_probability, GATE_0, WARMUP, EPOCH, EXPERTS,
)


class NightFormulaTests(unittest.TestCase):
    def test_exact_complete_box_mass_for_all_digit_multiplicities(self):
        dist=tuple([.09]*9+[.19])
        for game in ("pick3","pick4","pick5"):
            width=int(game[-1])
            keys=[tuple(range(width)),tuple([9]*(width-1)+[8])]
            for combo in keys:
                p=full_box_probability(game,dist,combo)
                brute=sum(math.prod(dist[d] for d in perm)
                          for perm in distinct_permutations(combo))
                self.assertAlmostEqual(p,brute,places=13)
            picks=optimal_boxes(game,dist,3)
            self.assertEqual(len(picks),3)
            self.assertEqual(len({tuple(t["numbers"]) for t in picks}),3)

    def test_two_conditional_experts_are_normalized(self):
        machine=NightConditionalEvidence("pick3")
        rows=simulate("pick3","hidden_opposing_machines",1000,52)
        for i in range(0,1000,2):
            pair_day,pair_night=rows[i],rows[i+1]
            before=machine.accumulator.distributions(pair_day["numbers"])
            self.assertEqual(set(before),set(EXPERTS))
            for p in before.values():
                self.assertAlmostEqual(sum(p),1.)
                self.assertTrue(all(0 < x < 1 for x in p))
            machine.observe(pair_day["numbers"],pair_night["numbers"])
        self.assertEqual(machine.paired,500)

    def test_old_night_cannot_leak_into_same_day_prediction(self):
        rows=simulate("pick3","hidden_opposing_machines",1002,54)
        prior=rows[:-1]
        self.assertEqual(prior[-1]["stream"],"Day")
        name,p,detail=fit_before("pick3",prior,"Night")
        altered=[dict(row) for row in rows]
        altered[-1]["numbers"]=[9,9,9]
        newname,newp,newdetail=fit_before("pick3",altered[:-1],"Night")
        self.assertEqual((name,p,detail),(newname,newp,newdetail))
        self.assertIsNone(fit_before("pick3",prior,"Day")[1])
        self.assertIsNone(fit_before("pick3",rows,"Night")[1])

    def test_fair_null_no_forced_lookahead_edge(self):
        rows=simulate("pick3","fair_independent",3000,73)
        machine=NightConditionalEvidence("pick3")
        for k in range(0,len(rows),2):
            d,n=rows[k:k+2]
            if k>0:
                active,forecast,meta=machine.predict(d["numbers"])
                if active:
                    self.assertGreaterEqual(
                        meta["experts"][active]["log_e"],GATE_0)
            machine.observe(d["numbers"],n["numbers"])
        self.assertEqual(machine.paired,1500)
        self.assertTrue(all(abs(v)<250 for v in machine.log_e.values()))

    def test_mock_hidden_equipment_is_unavailable_to_formula(self):
        rows=simulate("pick3","hidden_opposing_machines",1002,7)
        stripped=[{k:v for k,v in r.items()
                   if k in ("game","at","stream","numbers")} for r in rows]
        a=fit_before("pick3",rows[:-1],"Night")
        b=fit_before("pick3",stripped[:-1],"Night")
        self.assertEqual(a,b)
        self.assertNotIn("machine",str(a[2]))
        self.assertNotIn("pretests",str(a[2]))


if __name__ == "__main__":
    unittest.main()
