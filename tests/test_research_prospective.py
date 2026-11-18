import copy
import random
import unittest
from datetime import datetime, date, timedelta, timezone

from research_prospective import METHOD_SPECS, legal_target, prepare_pick, score_saved_pick, update


def synthetic(game, rows=1100):
    width=int(game[-1])
    start=date(2024,10,1)
    rng=random.Random(17)
    out=[]
    for i in range(rows):
        date_value=(start+timedelta(days=i//2)).isoformat()
        out.append({"date":date_value,"stream":"Day" if i%2==0 else "Night",
                    "numbers":[rng.randrange(10) for _ in range(width)],
                    "fireball":None})
    return out


class ProspectiveTests(unittest.TestCase):
    def test_target_before_sales_close(self):
        early=datetime(2026,11,16,12,30,tzinfo=timezone.utc)
        d=legal_target("pick3",early)
        self.assertEqual(d["date"],"2026-11-16")
        self.assertEqual(d["stream"],"Day")
        late=datetime(2026,11,16,19,0,tzinfo=timezone.utc)
        e=legal_target("pick3",late)
        self.assertEqual(e["stream"],"Night")

    def test_cutoff_blocks_same_draw_predictions(self):
        from zoneinfo import ZoneInfo
        ny=ZoneInfo("America/New_York")
        near=datetime(2026,11,16,13,55,tzinfo=ny)
        self.assertIsNone(legal_target("pick3",near))
        at_night=datetime(2026,11,16,22,50,tzinfo=ny)
        self.assertIsNone(legal_target("pick3",at_night))

    def test_deterministic_single_ticket_per_method(self):
        hist=synthetic("pick3")
        target={"game":"pick3","date":"2026-11-16","stream":"Day"}
        for method in METHOD_SPECS:
            a=prepare_pick("pick3",target,hist,method)
            b=prepare_pick("pick3",target,hist,method)
            self.assertEqual(a,b)
            self.assertEqual(len(a["numbers"]),3)
            self.assertTrue(all(len(x)==10 for x in a["forecast_by_position"]))

    def test_append_then_settle_only_with_named_target(self):
        hist=synthetic("pick3")
        now=datetime(2026,11,16,12,30,tzinfo=timezone.utc)
        entries,counts=update("pick3",hist,[],now)
        self.assertEqual(counts["created"],1)
        self.assertIsNone(entries[-1]["result"])
        duplicate,_=update("pick3",hist,entries,now)
        self.assertEqual(entries,duplicate)
        # A result with a DIFFERENT session/date must not settle target.
        yesterday=dict(hist[-1])
        yesterday["date"]="2026-11-15"
        pending,_=update("pick3",hist+[yesterday],entries,now)
        self.assertIsNone(pending[-1]["result"])
        official={"date":"2026-11-16","stream":"Day",
                  "numbers":[1,2,3],"fireball":5}
        # After the draw and before night cutoff, settle Day and predict Night.
        after=datetime(2026,11,16,20,0,tzinfo=timezone.utc)
        settled,c=update("pick3",hist+[official],entries,after)
        self.assertEqual(c["settled"],1)
        self.assertEqual(settled[0]["result"]["official_numbers"],[1,2,3])
        self.assertEqual(c["created"],1)
        self.assertEqual(len(settled),2)
        self.assertEqual(settled[1]["target"]["stream"],"Night")

    def test_frozen_forecast_receives_only_available_later_horizon_grades(self):
        past=synthetic("pick3")
        target={"game":"pick3","date":"2026-11-15","stream":"Day"}
        entries=[{"id":"fixed-prior-record","target":target,
                  "created_at_utc":"2026-11-14T12:00:00+00:00",
                  "version":"val_prospective_one_pick_v1",
                  "predictions":{method:prepare_pick("pick3",target,past,method)
                                 for method in METHOD_SPECS},
                  "result":None}]
        future=[
            {"date":"2026-11-15","stream":"Day","numbers":[1,2,3],"fireball":6},
            {"date":"2026-11-15","stream":"Night","numbers":[2,3,4],"fireball":7},
            {"date":"2026-11-16","stream":"Day","numbers":[3,4,5],"fireball":8},
        ]
        now=datetime(2026,11,17,12,30,tzinfo=timezone.utc)
        original=copy.deepcopy(entries[0]["predictions"])
        updated,c=update("pick3",past+future,entries,now)
        e=updated[0]
        self.assertEqual(e["predictions"],original)
        self.assertEqual(e["target"],target)
        self.assertEqual(e["result"]["official_numbers"],[1,2,3])
        self.assertEqual(sorted(e["horizon_results"]),["0","1","2"])
        self.assertEqual(e["horizon_results"]["1"]["actual_numbers"],[2,3,4])
        self.assertEqual(c["horizon_graded"],3)
        replay,c2=update("pick3",past+future,updated,now)
        self.assertEqual(replay[0],updated[0])
        self.assertEqual(c2["horizon_graded"],0)
        changed=copy.deepcopy(past+future)
        changed[-1]["numbers"]=[9,9,9]
        revised,c3=update("pick3",changed,updated,now)
        self.assertTrue(revised[0]["source_revision_warning"])
        self.assertEqual(revised[0]["horizon_results"]["2"]["actual_numbers"],[3,4,5])
        self.assertGreater(c3["correction_warnings"],0)

    def test_score_counts_fireball_and_precommitted_distribution(self):
        pick={"numbers":[2,8,4],
              "forecast_by_position":[[.1]*10 for _ in range(3)]}
        result=score_saved_pick(pick,{"numbers":[6,8,4],"fireball":2})
        self.assertFalse(result["straight"])
        self.assertFalse(result["any_order_including_straight"])
        self.assertTrue(result["fireball_any_order"])
        self.assertAlmostEqual(result["log_score_gain_vs_fair"],0)


if __name__=="__main__":unittest.main()
