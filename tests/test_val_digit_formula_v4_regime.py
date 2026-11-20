"""VAL Box v4 fixed-epoch correction: no ancient evidence debt."""
import math
import random
import unittest

from research_virtual_draw_lab import simulate
from val_digit_formula_v2 import (
    _online_evidence, forecast, generate_picks, ONLINE_EPOCH_DRAWS,
    ONLINE_EPOCH_ANCHOR, FORMULA_REVISION,
)
from val_box_challenger import LOG_GATE


class BoxRegimeFormulaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fair = simulate("pick3", "fair_independent", 3100, 51)
        cls.echo = simulate("pick3", "within_draw_echo", 3100, 51)

    def test_ancient_drawings_do_not_accumulate_negative_evidence_debt(self):
        recent = self.echo[:1500]
        pre = [dict(row, at=row["at"].replace("2026-", "2023-"))
               for row in self.fair[:1500]]
        a = _online_evidence("pick3", recent, "Day")
        b = _online_evidence("pick3", pre + recent, "Day")
        self.assertEqual(a, b)
        self.assertEqual(a["epoch"], 0)
        self.assertEqual(a["anchor"], ONLINE_EPOCH_ANCHOR)
        self.assertTrue(a["confirmed"])
        self.assertEqual(a["active"], "echo")

    def test_new_strong_pattern_after_fair_epoch_can_be_learned(self):
        rows = self.fair[:ONLINE_EPOCH_DRAWS] + self.echo[ONLINE_EPOCH_DRAWS:3100]
        detail = _online_evidence("pick3", rows, "Night")
        self.assertEqual(detail["epoch"], 1)
        self.assertEqual(detail["epoch_draws"], 1500)
        self.assertEqual(detail["prewarm_draws"], 700)
        self.assertGreater(detail["threshold"], LOG_GATE)
        self.assertTrue(detail["confirmed"], detail)
        self.assertEqual(detail["active"], "echo")
        model = forecast("pick3", rows, "Night")
        self.assertTrue(model["gate_passed"])
        self.assertIn("online_echo", model["weights"])
        tickets,meta=generate_picks("pick3",rows,"Night",3,random.Random(3))
        self.assertEqual(meta["formula_revision"], FORMULA_REVISION)
        self.assertTrue(meta["signal_gate_passed"])
        self.assertTrue(all(p["formula_revision"]==FORMULA_REVISION
                            for p in tickets))

    def test_old_bias_is_not_credited_as_evidence_after_reset(self):
        rows = [dict(r) for r in self.echo[:2100]]
        rng=random.Random(74213)
        for row in rows[1600:]:
            row["numbers"]=[rng.randrange(10) for _ in range(3)]
        state=_online_evidence("pick3",rows,"Night")
        self.assertEqual(state["epoch"],1)
        self.assertEqual(state["epoch_draws"],500)
        self.assertGreater(state["threshold"],LOG_GATE)
        self.assertFalse(state["confirmed"])
        self.assertIsNone(state["active"])

    def test_new_draw_unknown_cannot_change_current_epoch_forecast(self):
        a=self.fair[:1740]
        baseline=forecast("pick3",a,"Day")
        altered=[dict(r) for r in self.fair[:1900]]
        altered[1740]["numbers"]=[9,9,9]
        altered[1800]["numbers"]=[1,1,1]
        self.assertEqual(baseline,forecast("pick3",altered[:1740],"Day"))


if __name__ == "__main__":
    unittest.main()
