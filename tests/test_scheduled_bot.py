import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import scheduled_bot
from val import GAMES, Store


class DailyBotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.now=datetime.now(timezone.utc)
    def tearDown(self): self.temp.cleanup()
    def fake_sync(self,store,game):
        # Legal session history, not claimed to be real winning numbers.
        for stream in scheduled_bot.sessions(game):
            rows=[]
            for i in range(90):
                g=GAMES[game]; nums=list(range(g['size'])) if g.get('digits') else list(range(1,g['size']+1))
                rows.append(dict(game=game,at=(self.now-timedelta(days=90-i)).isoformat(),stream=stream,numbers=nums,bonus=1 if g.get('bonus') else None,source='Synthetic fixture'))
            store.put(rows)
    def test_report_round_trip_and_same_day_reuse(self):
        output=self.root/'reports'
        with patch.object(scheduled_bot,'backtest',return_value=dict(results=[dict(method=m,exact=0,tickets=300) for m in ('ensemble','random')])), patch.object(scheduled_bot,'simulate',return_value=dict(p_value=.5)):
            first=scheduled_bot.run(Store(self.root/'first.db'),output,syncer=self.fake_sync)
            self.assertEqual(first['batches'],16)
            self.assertEqual(first['failures'],[])
            before=json.loads((output/'ledger.json').read_text())
            scheduled_bot.run(Store(self.root/'second.db'),output,syncer=self.fake_sync)
            after=json.loads((output/'ledger.json').read_text())
            self.assertEqual(before,after)
            self.assertTrue(all(r['result'] is None for r in after['predictions']))
            self.assertIn('Keno needs a CSV import',(output/'latest.md').read_text())
    def test_feed_failure_skips_new_picks_and_is_visible(self):
        def fail(store,game): raise OSError('feed unavailable')
        result=scheduled_bot.run(Store(self.root/'failed.db'),self.root/'reports',syncer=fail)
        self.assertEqual(result['batches'],0)
        self.assertEqual(len(result['failures']),9)
        self.assertIn('feed unavailable',(self.root/'reports'/'latest.md').read_text())


if __name__=='__main__':unittest.main()
