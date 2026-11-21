"""Prospective immutable freeze and grading tests for contextual Box v1."""
import copy
import random
import unittest
from datetime import date,timedelta,datetime,timezone

from research_contextual_future import frozen_forecast, update, audit, settle, VERSION


def fake_history(game="pick3",days=400):
    rng=random.Random(902)
    width=int(game[-1])
    start=date(2025,10,17)
    rows=[]
    for i in range(days):
        day=(start+timedelta(days=i)).isoformat()
        for stream in ("Day","Night"):
            if day=="2026-11-20" and stream=="Night":
                continue
            if day>"2026-11-20":
                continue
            rows.append(dict(date=day,stream=stream,
                             numbers=[rng.randrange(10) for _ in range(width)],
                             fireball=None))
    return rows


class FutureContextualTests(unittest.TestCase):
    def test_freeze_forecast_ignores_a_later_night_result(self):
        rows=fake_history()
        target=dict(game="pick3",date="2026-11-20",stream="Night",
                    wagers_close_utc="2026-11-21T03:45:00+00:00")
        a=frozen_forecast("pick3",target,rows)
        contaminated=copy.deepcopy(rows)
        contaminated.append(dict(date="2026-11-20",stream="Night",
                                 numbers=[9,9,9]))
        b=frozen_forecast("pick3",target,contaminated)
        self.assertEqual(a,b)
        self.assertEqual(a["prepared_joint_model"]["eligible_features"],())
        self.assertEqual(len({tuple(sorted(x)) for x in a["candidate_tickets"]}),3)

    def test_can_create_then_settle_immutable_candidate(self):
        history=fake_history()
        now=datetime(2026,11,20,21,0,tzinfo=timezone.utc)
        records,changes=update("pick3",history,[],now)
        self.assertEqual(changes["created"],1)
        self.assertTrue(audit("pick3",records))
        frozen=copy.deepcopy(records[0]["forecast"])
        duplicate,again=update("pick3",history,records,now)
        self.assertEqual(again["created"],0)
        self.assertEqual(records,duplicate)
        winner=frozen["candidate_tickets"][0]
        observed=history+[dict(date="2026-11-20",
                               stream="Night",numbers=winner,
                               fireball=None)]
        graded,changes=update(
            "pick3",observed,records,
            datetime(2026,11,21,20,0,tzinfo=timezone.utc))
        self.assertEqual(changes["graded"],1)
        self.assertEqual(graded[0]["forecast"],frozen)
        self.assertEqual(
            graded[0]["result"]["stats"]["model_full_box_wins"],1)
        self.assertTrue(audit("pick3",graded))

    def test_catches_corrupt_or_late_forecast(self):
        history=fake_history()
        now=datetime(2026,11,20,21,0,tzinfo=timezone.utc)
        records,_=update("pick3",history,[],now)
        damaged=copy.deepcopy(records)
        damaged[0]["created_utc"]="2026-11-21T04:05:00+00:00"
        with self.assertRaisesRegex(ValueError,"Late"):
            audit("pick3",damaged)
        damaged=copy.deepcopy(records)
        damaged[0]["forecast"]["candidate_tickets"][1]=list(
            damaged[0]["forecast"]["candidate_tickets"][0])
        with self.assertRaisesRegex(ValueError,"Three distinct"):
            audit("pick3",damaged)

    def test_no_real_external_equipment_source_is_invented(self):
        history=fake_history()
        target=dict(game="pick3",date="2026-11-20",stream="Night",
                    wagers_close_utc="2026-11-21T03:45:00+00:00")
        f=frozen_forecast("pick3",target,history)
        self.assertNotIn("equipment",f["prepared_joint_model"]["models"])
        self.assertNotIn("pretest",f["prepared_joint_model"]["models"])
        self.assertEqual(f["version"],VERSION)


if __name__=="__main__":
    unittest.main()
