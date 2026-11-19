import unittest
from collections import Counter
from research_virtual_draw_lab import (SCENARIOS,normalize,truth_distribution,
    simulate,RollingCounts,evaluate)

class VirtualDrawLabTests(unittest.TestCase):
    def test_probabilities_and_repeats(self):
        for name in SCENARIOS:
            rows=simulate("pick3",name,120,2)
            self.assertEqual(len(rows),120)
            self.assertEqual(len({r["at"] for r in rows}),120)
            for r in rows:
                self.assertEqual(len(r["numbers"]),3)
                self.assertEqual(len(r["pretests"]),2)
                for p in r["truth_probs"]:self.assertAlmostEqual(sum(p),1)
    def test_null_unconditional_hidden_two_machine_mix(self):
        width=4
        a=truth_distribution("hidden_opposing_machines",width,"Day",0,.2,0,[])
        b=truth_distribution("hidden_opposing_machines",width,"Day",1,.2,0,[])
        self.assertAlmostEqual(a[7],.17)
        self.assertAlmostEqual(b[7],.03)
        for d in range(10):
            self.assertAlmostEqual((a[d]+b[d])/2,.1)
    def test_known_bias_and_change_are_controlled(self):
        fair=truth_distribution("fair_independent",3,"Day",0,.2,0,[])
        biased=truth_distribution("fixed_position_strong",3,"Day",0,.2,0,[])
        late=truth_distribution("halfway_replacement",3,"Night",0,.8,1,[])
        self.assertAlmostEqual(fair[7],.1)
        self.assertAlmostEqual(biased[7],.22)
        self.assertAlmostEqual(late[2],.18)
        echo=truth_distribution("within_draw_echo",3,"Day",0,.8,1,[9])
        self.assertGreater(echo[9],.3)
    def test_rolling_forecast_no_lookahead(self):
        rows=simulate("pick3","pooled_device_bias",110,3)
        roll=RollingCounts(3,50)
        for row in rows[:80]:roll.add(row)
        original=roll.models("Day",0)
        rows[80]["numbers"]=[9,9,9]
        self.assertEqual(original,roll.models("Day",0))
        roll.add(rows[80])
        self.assertNotEqual(original,roll.models("Day",0))
    def test_end_to_end_lab(self):
        output=evaluate("pick3","fixed_position_strong",
                        trials=2,train=700,test=80,probe_v2=False)
        models=output["methods"]
        self.assertEqual(models["fair"]["target_draws"],160)
        self.assertEqual(models["oracle"]["target_draws"],160)
        self.assertEqual(models["v2_production_probe"]["targets_checked"],0)

if __name__=="__main__":unittest.main()
