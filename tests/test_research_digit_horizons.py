import random
import unittest
from datetime import datetime,timedelta,timezone
from research_digit_horizons import (
    MODEL_NAMES,HORIZONS,build_models,predictive_gain,analyze,provenance
)

def fake_history(game,width,n=650):
    rng=random.Random(22)
    at=datetime(2025,1,1,tzinfo=timezone.utc)
    return [dict(game=game,at=(at+timedelta(hours=12*i)).isoformat(),
                 stream="Day" if i%2==0 else "Night",
                 numbers=[rng.randrange(10) for _ in range(width)])
            for i in range(n)]

class DigitHorizonFalsificationTests(unittest.TestCase):
    def test_all_probabilities_normalized(self):
        rows=fake_history("pick3",3,90)
        model=build_models(rows[:-1],"Night",3)
        self.assertEqual(set(model),set(MODEL_NAMES))
        for name,arr in model.items():
            self.assertEqual(len(arr),3)
            for distribution in arr:
                self.assertEqual(len(distribution),10)
                self.assertAlmostEqual(sum(distribution),1)
                self.assertTrue(all(0<x<1 for x in distribution))
        self.assertAlmostEqual(predictive_gain(model["uniform"],[4,5,6]),0)
    def test_future_draw_change_cannot_change_forecast(self):
        rows=fake_history("pick4",4,90)
        origin=70
        first=build_models(rows[:origin],"Day",4)
        mutated=fake_history("pick4",4,90)
        mutated[origin]["numbers"]=[9,9,9,9]
        mutated[origin+5]["numbers"]=[8,8,8,8]
        second=build_models(mutated[:origin],"Day",4)
        self.assertEqual(first,second)
        changed=fake_history("pick4",4,90)
        changed[origin-1]["numbers"]=[5,5,5,5]
        different=build_models(changed[:origin],"Day",4)
        self.assertNotEqual(first,different)
    def test_multidraw_real_temporal_contract(self):
        rows=fake_history("pick3",3,650)
        result=analyze("pick3",rows,max_origins=55)
        self.assertEqual(result["origin_calibration"]["count"]+
                         result["origin_final"]["count"],55)
        self.assertEqual(set(result["final_frozen_ticket_horizon_comparison"]),
                         set(map(str,HORIZONS)))
        self.assertEqual(result["history"]["n"],650)
        self.assertEqual(len(result["history"]["fingerprint_sha256"]),64)
        for h,row in result["final_frozen_ticket_horizon_comparison"].items():
            a=row["ensemble"]; b=row["uniform_control"]
            self.assertEqual(a["tickets"],b["tickets"])
            self.assertEqual(a["tickets"],a["origins"]*3)
            self.assertEqual(b["tickets"],b["origins"]*3)
            self.assertGreater(a["origins"],0)
        self.assertFalse(result["selected_by_calibration_only"]["immediate"]
                         ["eligible_for_live_promotion"])
    def test_rejects_duplicate_timestamp(self):
        rows=fake_history("pick3",3,650)
        rows[50]["at"]=rows[49]["at"]
        with self.assertRaises(ValueError):analyze("pick3",rows,max_origins=40)

if __name__=="__main__":unittest.main()
