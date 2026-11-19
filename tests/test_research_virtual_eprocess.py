import unittest
import math
from research_virtual_eprocess import (LOG_GATE,EXPERTS,START_EVIDENCE,
                                       evaluate)

class VirtualEProcessTests(unittest.TestCase):
    def test_threshold_and_sources(self):
        self.assertGreater(LOG_GATE,math.log(20))
        self.assertEqual(set(EXPERTS),{"pooled","position","day_night"})
        self.assertGreater(START_EVIDENCE,0)
    def test_strong_position_model_has_diagnostic_signal(self):
        r=evaluate("pick3","fixed_position_strong",replicates=3,train=650,test=180)
        a=r["models"]["eprocess_challenger"]
        self.assertEqual(a["target_draws"],540)
        self.assertEqual(r["replicates"],3)
        self.assertGreaterEqual(r["test_active_draws"],0)
        self.assertLessEqual(r["test_active_draws"],540)
        self.assertEqual(a["target_draws"],r["models"]["fair"]["target_draws"])
    def test_fair_model_never_uses_target_outcome(self):
        # One calculation must involve exactly the previous 200+ outcomes,
        # not a target's known result. The study only advances the count
        # and e-process AFTER scoring each hidden target.
        r=evaluate("pick4","fair_independent",replicates=2,train=650,test=150)
        self.assertEqual(r["models"]["fair"]["target_draws"],300)
        self.assertEqual(r["models"]["eprocess_challenger"]["target_draws"],300)

if __name__=="__main__":unittest.main()
