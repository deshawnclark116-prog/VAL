"""Don't freeze a Box prediction from stale or unverified same-day feeds."""
import io
import unittest
from datetime import datetime,timezone
from unittest.mock import patch

import research_prospective_pooled_box_v2 as trial


class FreshSourceTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,20,23,0,tzinfo=timezone.utc)
        self.archive=[
            dict(date="2026-11-19",stream="Day",numbers=[1,2,3],fireball=0),
            dict(date="2026-11-19",stream="Night",numbers=[4,5,6],fireball=0),
        ]
        self.day=dict(game="pick3",at="2026-11-20T18:59:00+00:00",
                      stream="Day",numbers=[7,8,9],extra=4)
        self.future=dict(game="pick3",at="2026-11-21T04:00:00+00:00",
                         stream="Night",numbers=[9,9,9],extra=7)

    def load(self,recent):
        with patch.object(trial,"fetch_full",return_value=(self.archive,{})), \
             patch.object(trial.urllib.request,"urlopen",
                          return_value=io.BytesIO(b"official card")), \
             patch.object(trial,"parse_latest_digits",return_value=recent):
            return trial.load_fresh_official_history("pick3",self.now)

    def test_same_day_result_used_for_night_and_future_result_ignored(self):
        rows,meta=self.load([self.day,self.future])
        self.assertEqual(rows[-1]["date"],"2026-11-20")
        self.assertEqual(rows[-1]["stream"],"Day")
        self.assertEqual(rows[-1]["numbers"],[7,8,9])
        self.assertEqual(len(rows),3)
        self.assertEqual(meta["supplemented"],1)

    def test_stale_feed_blocks_unverified_prediction(self):
        with self.assertRaisesRegex(ValueError,"Latest completed"):
            self.load([self.future])

    def test_conflicting_result_is_not_silently_accepted(self):
        altered=dict(self.day,at="2026-11-20T18:59:00+00:00",
                     numbers=[8,8,9])
        archive=self.archive+[dict(date="2026-11-20",stream="Day",
                                   numbers=[7,8,9],fireball=4)]
        with patch.object(trial,"fetch_full",return_value=(archive,{})), \
             patch.object(trial.urllib.request,"urlopen",
                          return_value=io.BytesIO(b"official card")), \
             patch.object(trial,"parse_latest_digits",return_value=[altered]):
            with self.assertRaisesRegex(ValueError,"Conflict"):
                trial.load_fresh_official_history("pick3",self.now)


if __name__=="__main__":
    unittest.main()
