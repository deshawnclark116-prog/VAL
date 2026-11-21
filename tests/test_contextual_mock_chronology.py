"""Check pretest-first mock equipment simulation and visibility counterfactual."""
import unittest
from datetime import datetime,timezone

from research_contextual_regime_box import (
    simulate_temporally_valid,prior_target,local_day,
)
from val_contextual_regime_box import _features,ContextualBox


class MockChronologyTests(unittest.TestCase):
    def test_synthetic_machine_selection_stable_with_day_night_pairs(self):
        for game in ("pick3","pick4","pick5"):
            rows=simulate_temporally_valid(
                game,"hidden_opposing_machines",200,41)
            clone=simulate_temporally_valid(
                game,"hidden_opposing_machines",200,41)
            self.assertEqual(rows,clone)
            self.assertEqual(len(rows),200)
            for i in range(0,200,2):
                self.assertEqual(rows[i]["machine"],rows[i+1]["machine"])
                self.assertEqual(rows[i]["stream"],"Day")
                self.assertEqual(rows[i+1]["stream"],"Night")
                self.assertEqual(local_day(rows[i]),local_day(rows[i+1]))
                for row in rows[i:i+2]:
                    self.assertTrue(row["simulation_pretests_before_official"])
                    self.assertEqual(len(row["pretests"]),2)
                    self.assertEqual(len(row["numbers"]),int(game[-1]))
                    self.assertTrue(all(len(x)==int(game[-1])
                                        for x in row["pretests"]))

    def test_counterfactual_only_changes_observability_not_outcomes(self):
        draws=simulate_temporally_valid(
            "pick3","hidden_opposing_machines",800,81)
        m=ContextualBox("pick3")
        for row in draws:
            hidden=prior_target(row,public_equipment=False)
            exposed=prior_target(row,public_equipment=True)
            self.assertEqual(_features(hidden),{})
            self.assertEqual(set(_features(exposed)),
                             {"equipment_id","pretests"})
            self.assertLess(
                datetime.fromisoformat(
                    exposed["observables"]["pretests"]["published_at_utc"]),
                datetime.fromisoformat(exposed["wagers_close_utc"]))
            self.assertEqual(m.forecast(hidden)["eligible_features"],())
            self.assertEqual(
                set(m.forecast(exposed)["eligible_features"]),
                {"equipment_id","pretests"})
            # The observed numbers are from the SAME immutable simulator row.
            m.observe(hidden,row["numbers"],m.forecast(hidden))


if __name__=="__main__":
    unittest.main()
