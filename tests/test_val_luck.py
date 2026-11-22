import unittest

from val_luck import chance_at_least, luck_check, luck_report, one_in, picks_needed


def entry(game, version, pick, control, draw, fallback=True, created="2026-11-20T12:00:00+00:00"):
    return dict(game=game, method=version, created=created,
                model_meta=dict(formula_version=version, signal_gate_passed=not fallback),
                picks=[dict(numbers=pick)], baseline=[dict(numbers=control)],
                result=dict(draw=dict(numbers=draw)))


class LuckCheckTests(unittest.TestCase):
    def test_chance_at_least_matches_binomial(self):
        self.assertAlmostEqual(chance_at_least([0.5, 0.5], 1), 0.75)
        self.assertAlmostEqual(chance_at_least([0.1] * 3, 2), 3 * 0.01 * 0.9 + 0.001)
        self.assertEqual(chance_at_least([0.2], 0), 1.0)

    def test_picks_needed_grows_as_wins_get_rarer(self):
        self.assertLess(picks_needed(6 / 1000), picks_needed(24 / 10000))
        self.assertIsNone(picks_needed(0))

    def test_one_in_is_readable(self):
        self.assertEqual(one_in(0.002), "about 1 in 500")
        self.assertEqual(one_in(0.9), "very likely")

    def test_only_first_ticket_counts_and_adjusts_for_many_formulas(self):
        winner = entry("pick4", "v_test", [1, 2, 3, 4], [5, 6, 7, 8], [4, 3, 2, 1])
        winner["picks"].append(dict(numbers=[5, 6, 7, 8]))  # alternative never counts
        loser = entry("pick3", "other", [1, 2, 3], [4, 5, 6], [7, 8, 9], fallback=False)
        rows = {r["version"]: r for r in luck_check([winner, loser, dict(game="pick3", result=None)])}
        self.assertEqual(rows["v_test"]["wins"], 1)
        self.assertEqual(rows["v_test"]["control_wins"], 0)
        self.assertAlmostEqual(rows["v_test"]["adjusted_chance"], 2 * rows["v_test"]["luck_chance"])
        self.assertIn("Luck by design", rows["v_test"]["verdict"])
        self.assertIn("No wins yet", rows["other"]["verdict"])

    def test_tracking_since_is_first_saved_pick(self):
        rows = luck_check([entry("pick3", "v", [1, 2, 3], [4, 5, 6], [7, 8, 9], created="2026-11-21T12:00:00+00:00"),
                           entry("pick3", "v", [1, 2, 3], [4, 5, 6], [7, 8, 9], created="2026-11-19T12:00:00+00:00")])
        self.assertEqual(rows[0]["since"], "2026-11-19T12:00:00+00:00")
        self.assertEqual(rows[0]["settled"], 2)

    def test_report_handles_empty_ledger(self):
        text = "\n".join(luck_report([], {}))
        self.assertIn("No settled picks yet", text)


if __name__ == "__main__":
    unittest.main()
