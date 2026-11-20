"""Immutable future-only trial for Day->Night complete Box challenger."""
import json
import random
import unittest
from datetime import datetime,timedelta,timezone

from research_day_night_future import forecast_for,update,grade


def prior_nights(game="pick3",days=500):
    rng=random.Random(6093)
    ending=datetime(2026,11,20,tzinfo=timezone.utc)
    start=ending-timedelta(days=days-1)
    rows=[]
    for i in range(days):
        day=(start+timedelta(days=i)).date().isoformat()
        for session in ("Day","Night"):
            if i==days-1 and session=="Night":
                continue
            rows.append(dict(date=day,stream=session,
                             numbers=[rng.randrange(10) for _ in
                                      range(int(game[-1]))],
                             fireball=None))
    return rows


class FutureConditionalTests(unittest.TestCase):
    def test_forecast_only_uses_pre_night_day_results(self):
        rows=prior_nights()
        target={"date":"2026-11-20","stream":"Night"}
        f=forecast_for("pick3",target,rows)
        later=rows+[dict(date="2026-11-20",stream="Night",
                         numbers=[9,9,9],fireball=None)]
        self.assertEqual(f,forecast_for("pick3",target,later))
        self.assertEqual(f["latest_training_draw"]["stream"],"Day")
        self.assertEqual(len(f["candidate_tickets"]),3)
        self.assertEqual(len(f["random_control_tickets"]),3)
        with self.assertRaises(ValueError):
            forecast_for("pick3",dict(target,stream="Day"),rows)

    def test_cannot_save_before_day_result(self):
        now=datetime(2026,11,20,21,0,tzinfo=timezone.utc)
        rows=prior_nights()[:-1]
        records,stats=update("pick3",rows,[],now)
        self.assertEqual(records,[])
        self.assertEqual(stats["created"],0)
        self.assertIn("Day",stats["withheld"])

    def test_freeze_and_grading_are_immutable(self):
        now=datetime(2026,11,20,21,0,tzinfo=timezone.utc)
        original=prior_nights()
        records,stats=update("pick3",original,[],now)
        self.assertEqual(stats["created"],1)
        self.assertEqual(records[0]["target"]["stream"],"Night")
        self.assertLess(records[0]["created_utc"],
                        records[0]["target"]["wagers_close_utc"])
        frozen=json.loads(json.dumps(records[0]))
        again,repeat=update("pick3",original,records,now)
        self.assertEqual(repeat["created"],0)
        self.assertEqual(again,records)
        outcome=frozen["forecast"]["candidate_tickets"][0][:]
        settled,stats=update(
            "pick3",original+[dict(date="2026-11-20",stream="Night",
                                   numbers=outcome,fireball=None)],
            records,datetime(2026,11,21,14,tzinfo=timezone.utc))
        self.assertEqual(stats["settled"],1)
        self.assertEqual(settled[0]["forecast"],frozen["forecast"])
        self.assertEqual(
            settled[0]["result"]["accuracy"]["model_box_wins"],1)

    def test_fair_fallback_log_score_is_zero(self):
        f=dict(candidate_tickets=[[0,1,2],[1,3,4],[2,3,9]],
               random_control_tickets=[[1,2,3],[1,4,5],[1,5,6]],
               selected_joint_forecast=None)
        result=grade("pick3",f,{"numbers":[2,0,1]})
        self.assertEqual(result["model_box_wins"],1)
        self.assertAlmostEqual(result["model_log_gain_vs_fair"],0.)


if __name__=="__main__":
    unittest.main()
