"""Frozen shadow ledger tests; no external network or real wager."""
import json
import random
import unittest
from datetime import datetime, timedelta, timezone

from research_box_future import forecast_for, update, grade


def rows(n=850):
    rng = random.Random(901)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    records = []
    for i in range(n):
        t = start + timedelta(days=i // 2)
        records.append({
            "date": t.date().isoformat(),
            "stream": "Day" if i % 2 == 0 else "Night",
            "numbers": [rng.randrange(10) for _ in range(3)],
            "fireball": None,
        })
    return records


class FutureBoxTests(unittest.TestCase):
    def test_prediction_independent_of_future_outcomes(self):
        old = rows()
        target = {"date": "2026-11-20", "stream": "Day"}
        a = forecast_for("pick3", target, old)
        later = old + [{"date": "2026-11-21", "stream": "Night",
                        "numbers": [9, 9, 9], "fireball": None}]
        b = forecast_for("pick3", target, later)
        self.assertEqual(a, b)
        self.assertEqual(len(a["candidate_tickets"]), 3)
        self.assertEqual(len(a["random_control_tickets"]), 3)
        self.assertEqual(a["selected_joint_forecast"] is None,
                         a["selected_expert"] is None)

    def test_target_tickets_frozen_even_when_rerun(self):
        now = datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc)
        source = rows()
        first, m1 = update("pick3", source, [], now, require_latest=False)
        self.assertEqual(m1["created"], 1)
        self.assertEqual(len(first), 1)
        second, m2 = update("pick3", source, first, now, require_latest=False)
        self.assertEqual(m2["created"], 0)
        self.assertEqual(first, second)
        self.assertTrue(first[0]["created_utc"] <
                        first[0]["target"]["wagers_close_utc"])
        self.assertEqual(json.loads(json.dumps(first)), first)

    def test_settles_only_named_original_prediction(self):
        first_now = datetime(2026, 11, 20, 14, 0, tzinfo=timezone.utc)
        source = rows()
        records, _ = update("pick3", source, [], first_now,
                            require_latest=False)
        frozen = json.loads(json.dumps(records[0]))
        target = frozen["target"]
        later = source + [{
            "date": target["date"], "stream": target["stream"],
            "numbers": frozen["forecast"]["candidate_tickets"][0][:],
            "fireball": None,
        }]
        night = datetime(2026, 11, 20, 22, 0, tzinfo=timezone.utc)
        settled, status = update("pick3", later, records, night,
                                 require_latest=False)
        self.assertEqual(status["settled"], 1)
        self.assertEqual(settled[0]["forecast"], frozen["forecast"])
        self.assertEqual(settled[0]["result"]["accuracy"]["model_box_wins"], 1)
        again, repeat = update("pick3", later, settled, night,
                               require_latest=False)
        self.assertEqual(repeat["settled"], 0)
        self.assertEqual(again[0], settled[0])

    def test_no_bogus_probability_gain_for_fair_fallback(self):
        frozen = {"candidate_tickets": [[0, 1, 2], [2, 3, 4], [3, 4, 5]],
                  "random_control_tickets": [[1, 2, 3], [2, 4, 5], [7, 8, 9]],
                  "selected_joint_forecast": None}
        out = grade("pick3", frozen, {"numbers": [2, 1, 0]})
        self.assertEqual(out["model_box_wins"], 1)
        self.assertEqual(out["model_log_gain_vs_fair"], 0.)


if __name__ == "__main__":
    unittest.main()
