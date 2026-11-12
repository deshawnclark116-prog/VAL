import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import scheduled_bot
from val import GAMES, Store, draw_schedule, next_draw, parse_latest_digits, ET


class DailyBotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.now=datetime(2026,11,12,22,30,tzinfo=timezone.utc)
    def tearDown(self): self.temp.cleanup()
    def fake_sync(self,store,game):
        # Legal session history, not claimed to be real winning numbers.
        rows=[]
        for i in range(12):
            for draw in draw_schedule(game,self.now-timedelta(days=i*16)):
                if datetime.fromisoformat(draw['at'])>self.now:continue
                g=GAMES[game]; nums=list(range(g['size'])) if g.get('digits') else list(range(1,g['size']+1))
                rows.append(dict(game=game,**draw,numbers=nums,bonus=1 if g.get('bonus') else None,source='Synthetic fixture'))
        store.put(rows)
    def test_report_round_trip_and_same_day_reuse(self):
        output=self.root/'reports'
        with patch.object(scheduled_bot,'backtest',return_value=dict(results=[dict(method=m,exact=0,tickets=300) for m in ('ensemble','random')])), patch.object(scheduled_bot,'simulate',return_value=dict(p_value=.5)):
            first=scheduled_bot.run(Store(self.root/'first.db'),output,syncer=self.fake_sync,now=self.now)
            self.assertEqual(first['batches'],9)
            self.assertEqual(first['failures'],[])
            before=json.loads((output/'ledger.json').read_text())
            scheduled_bot.run(Store(self.root/'second.db'),output,syncer=self.fake_sync,now=self.now)
            after=json.loads((output/'ledger.json').read_text())
            self.assertEqual(before,after)
            self.assertTrue(all(r['result'] is None for r in after['predictions']))
            self.assertIn('Keno needs a CSV import',(output/'latest.md').read_text())
            batches=json.loads((output/'picks.json').read_text())['batches']
            p3=next(b for b in batches if b['game']=='pick3')
            self.assertEqual(p3['target']['stream'],'Night')
            self.assertEqual(p3['training_latest']['stream'],'Day')
            self.assertEqual(datetime.fromisoformat(p3['target']['at']).astimezone(ET).date(),self.now.astimezone(ET).date())
    def test_feed_failure_skips_new_picks_and_is_visible(self):
        def fail(store,game): raise OSError('feed unavailable')
        result=scheduled_bot.run(Store(self.root/'failed.db'),self.root/'reports',syncer=fail)
        self.assertEqual(result['batches'],0)
        self.assertEqual(len(result['failures']),9)
        self.assertIn('feed unavailable',(self.root/'reports'/'latest.md').read_text())
    def test_missing_day_result_withholds_night_picks(self):
        def lagging(store,game):
            self.fake_sync(store,game)
            if game=='pick3':
                latest=max(d['at'] for d in store.history(game))
                with store.connect() as db:db.execute('DELETE FROM draws WHERE game=? AND at=?',(game,latest))
        with patch.object(scheduled_bot,'backtest',return_value=dict(results=[dict(method=m,exact=0,tickets=300) for m in ('ensemble','random')])),patch.object(scheduled_bot,'simulate',return_value=dict(p_value=.5)):
            result=scheduled_bot.run(Store(self.root/'lag.db'),self.root/'reports',syncer=lagging,now=self.now)
        self.assertEqual(result['batches'],8)
        self.assertEqual(result['failures'][0]['game'],'pick3')
        self.assertIn('Waiting for latest completed Day',result['failures'][0]['error'])
    def test_next_draw_skips_completed_sessions_and_uses_weekdays(self):
        self.assertEqual(next_draw('pick3',self.now)['stream'],'Night')
        self.assertEqual(next_draw('cashpop',self.now)['stream'],'Prime Time')
        self.assertEqual(datetime.fromisoformat(next_draw('megamillions',self.now)['at']).astimezone(ET).weekday(),4)
        self.assertEqual(datetime.fromisoformat(next_draw('bankamillion',self.now)['at']).astimezone(ET).weekday(),5)
        late=datetime(2026,11,13,4,30,tzinfo=timezone.utc)
        self.assertEqual(next_draw('pick3',late)['stream'],'Day')
        self.assertEqual(datetime.fromisoformat(next_draw('pick3',late)['at']).astimezone(ET).day,13)
    def test_latest_card_preserves_zeros_and_ignores_future_dashes(self):
        html='<a id="game-1050"><span>Latest Drawing: Thu 11/12/2026</span><ul class="daytime"><li>Day:</li><li>6</li><li>0</li><li>0</li><li>2</li></ul><ul class="evening"><li>Night:</li><li>-</li><li>-</li><li>-</li><li>-</li></ul></a>'
        rows=parse_latest_digits('pick3',html)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['numbers'],[6,0,0]);self.assertEqual(rows[0]['extra'],2)
    def test_explicit_target_settles_same_day_only_against_named_draw(self):
        store=Store(self.root/'target.db');target=next_draw('pick3',self.now)
        picks=[dict(numbers=[1,2,3],bonus=None)]
        store.record('pick3','Night','ensemble',picks,picks,target=target,created=self.now)
        store.put([dict(game='pick3',at=self.now.isoformat(),stream='Day',numbers=[1,2,3],bonus=None)])
        self.assertIsNone(store.ledger('pick3')[0]['result'])
        store.put([dict(game='pick3',**target,numbers=[1,2,3],bonus=None)])
        self.assertEqual(store.ledger('pick3')[0]['result']['model']['exact'],1)


if __name__=='__main__':unittest.main()
