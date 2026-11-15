import json
import random
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import val

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=val.Store(Path(self.temp.name)/"test.sqlite3")
    def tearDown(self): self.temp.cleanup()
    def history(self,game,n=90):
        g=val.GAMES[game]; rng=random.Random(12); start=datetime(2026,1,1,tzinfo=timezone.utc)
        rows=[]
        for i in range(n):
            low=0 if g.get("digits") else 1
            pool=range(low,low+g["pool"])
            nums=rng.choices(pool,k=g["size"]) if g.get("digits") else sorted(rng.sample(pool,g.get("drawn",g["size"])))
            rows.append(dict(game=game,at=(start+timedelta(days=i)).isoformat(),stream="Night",numbers=nums,
                             bonus=rng.randint(1,g["bonus"]) if g.get("bonus") else None,extra=None,source="Synthetic test fixture"))
        return rows
    def test_parse_digits_preserves_zeros_and_repeats(self):
        rows=val.parse_official("pick3","Results for Pick 3\n11/10/2026; Day: 0,7,7; Fireball: 2; Night: 5,7,2; Fireball: 5")
        self.assertEqual(rows[0]["numbers"],[0,7,7]);self.assertEqual(rows[0]["extra"],2)
        self.assertLess(rows[0]["at"],rows[1]["at"])
    def test_parse_bonus_types(self):
        for game,label,main,bonus in [("powerball","Powerball","8,42,45,51,57",17),("megamillions","Mega Ball","2,18,25,30,65",22),("millionaireforlife","Millionaire Ball","6,17,28,41,47",1),("bankamillion","Bonus Ball","5,6,15,24,25,28",12)]:
            row=val.parse_official(game,f"11/11/2026; {main}; {label}: {bonus}")[0]
            self.assertEqual(row["bonus"],None if game=="bankamillion" else bonus)
            if game=="bankamillion":self.assertEqual(row["extra"],12)
    def test_parse_cashpop_sessions_and_cash5(self):
        row=val.parse_official("cashpop","Thu 11/12/2026 - 05:00 PM; 13; Rush Hour")[0]
        self.assertEqual(row["numbers"],[13]);self.assertEqual(row["stream"],"Rush Hour")
        self.assertEqual(val.parse_official("cash5","11/11/2026; 11,15,19,32,39")[0]["numbers"],[11,15,19,32,39])
    def test_official_download_footer_and_unexpected_format(self):
        text="Results for Cash 5\n11/11/2026; 11,15,19,32,39\n\nAll information is entered manually, and is subject to human error. \nTherefore, we can not guarantee the accuracy of this information."
        self.assertEqual(len(val.parse_official("cash5",text)),1)
        with self.assertRaises(ValueError):val.parse_official("cash5",text+'\nunexpected source change')
    def test_obsolete_matrix_excluded(self):
        rows=val.parse_official("megamillions","04/04/2025; 1,2,3,4,5; Mega Ball: 25\n04/08/2025; 1,2,3,4,5; Mega Ball: 24")
        self.assertEqual(len(rows),1)
    def test_invalid_data_rejected(self):
        for game,nums,bonus in [("cash5",[1,1,2,3,4],None),("pick3",[0,1,10],None),("powerball",[1,2,3,4,5],27),("megamillions",[1,2,3,4,5],25),("keno",list(range(1,20)),None)]:
            with self.assertRaises(ValueError):val.validate(game,nums,bonus)
    def test_all_methods_all_games_produce_legal_unique_tickets(self):
        for game in val.GAMES:
            h=self.history(game)
            for method in val.METHODS:
                picks=val.generate(game,h,method,20,random.Random(8))
                self.assertEqual(len(picks),15 if game=="cashpop" else 20)
                self.assertEqual(len({json.dumps(p) for p in picks}),len(picks))
                for p in picks:val.validate(game,p["numbers"],p["bonus"],draw=False)
    def test_ranked_primary_keeps_all_original_candidates(self):
        for game in ("pick3", "pick4", "pick5", "cash5", "powerball", "megamillions",
                     "millionaireforlife", "bankamillion", "cashpop"):
            history = self.history(game)
            picks = val.generate(game, history, "ensemble", 3, random.Random(42))
            ranked = val.rank_ensemble_picks(game, history, picks)
            self.assertEqual(sorted((tuple(p["numbers"]), p["bonus"]) for p in picks),
                             sorted((tuple(p["numbers"]), p["bonus"]) for p in ranked))
            self.assertEqual([p["rank"] for p in ranked], [1, 2, 3])
            self.assertEqual([p["role"] for p in ranked],
                             ["primary", "alternative_1", "alternative_2"])
            self.assertEqual([p["ranking_version"] for p in ranked],
                             ["ensemble_sampling_v1"] * 3)
            self.assertEqual([p["model_weight_score"] for p in ranked],
                             sorted((p["model_weight_score"] for p in ranked), reverse=True))
            self.assertTrue(all(p["model_weight_score"] > 0 for p in ranked))
            self.assertTrue(all("rank" not in p for p in picks))

    def test_digit_ranking_uses_per_position_weights(self):
        history = self.history("pick3")
        candidates = [dict(numbers=[9,9,9],bonus=None), dict(numbers=[0,0,0],bonus=None),
                      dict(numbers=[1,1,1],bonus=None)]
        ranked = val.rank_ensemble_picks("pick3", history, candidates)
        weights = [val.model_selection_weights("pick3", history, position=i) for i in range(3)]
        for pick in ranked:
            expected = 1.0
            for i, n in enumerate(pick["numbers"]): expected *= weights[i][n]
            self.assertAlmostEqual(pick["model_weight_score"], expected)

    def test_match_semantics(self):
        p=dict(numbers=[0,1,1],bonus=None); d=dict(numbers=[1,0,1],bonus=None)
        self.assertEqual(val.score("pick3",p,d)["matches"],1)
        p=dict(numbers=[1,2,3,4,5],bonus=1); d=dict(numbers=[5,4,3,2,1],bonus=2)
        self.assertEqual(val.score("powerball",p,d)["matches"],5)
        self.assertFalse(val.score("powerball",p,d)["exact"])
    def test_backtest_never_sees_test_or_future_draw(self):
        history=self.history("pick3",85); real=val.generate; observed=[]
        def spy(game,training,method,count,rng):
            observed.append((len(training),training[-1]["at"]))
            return real(game,training,method,count,rng)
        with patch.object(val,"generate",side_effect=spy):
            result=val.backtest("pick3",history,count=2,tests=50)
        self.assertEqual(len(observed),250)
        for j,(length,at) in enumerate(observed):
            index=35+j%50
            self.assertEqual(length,index);self.assertEqual(at,history[index-1]["at"])
        self.assertEqual(result["expected_matches"],.3)
        self.assertTrue(all(r["tickets"]==100 for r in result["results"]))
    def test_backtest_reproducible(self):
        h=self.history("cash5",80)
        self.assertEqual(val.backtest("cash5",h,tests=50),val.backtest("cash5",h,tests=50))
    def test_import_atomic_and_idempotent(self):
        good='game,at,stream,numbers,bonus\npick3,2026-01-01T23:00:00-05:00,Night,"0 1 1",\n'
        bad=good+'cash5,2026-01-02T23:00:00-05:00,Main,"1 1 2 3 4",\n'
        with self.assertRaises(ValueError):val.import_csv(self.store,bad)
        self.assertEqual(self.store.history("pick3"),[])
        self.assertEqual(val.import_csv(self.store,good)["added"],1)
        self.assertEqual(val.import_csv(self.store,good)["added"],0)
    def test_future_import_rejected(self):
        with self.assertRaises(ValueError):val.import_csv(self.store,'game,at,stream,numbers,bonus\npick3,2099-01-01T23:00:00-05:00,Night,"0 1 1",\n')
    def test_ledger_excludes_same_day_and_settles_next_session(self):
        picks=[dict(numbers=[0,1,1],bonus=None)]
        pid=self.store.record("pick3","Night","random",picks,picks)
        with self.store.connect() as db: db.execute("UPDATE predictions SET created=? WHERE id=?",("2026-01-01T12:00:00+00:00",pid))
        rows=[dict(game="pick3",at=at,stream=s,numbers=[0,1,1],bonus=None,extra=None,source="Fixture") for at,s in [("2026-01-02T04:00:00+00:00","Night"),("2026-01-02T18:59:00+00:00","Day"),("2026-01-03T04:00:00+00:00","Night")]]
        self.store.put(rows[:2]);self.assertIsNone(self.store.ledger("pick3")[0]["result"])
        self.store.put(rows[2:]);record=self.store.ledger("pick3")[0]
        self.assertEqual(record["result"]["draw"]["at"],rows[2]["at"])
        self.assertEqual(record["result"]["model"]["exact"],1)
    def test_simulation_bounds_and_repeatability(self):
        h=self.history("pick3",30)
        a=val.simulate("pick3",h,trials=1000)
        self.assertTrue(0<a["p_value"]<=1)
        self.assertEqual(a,val.simulate("pick3",h,trials=1000))
    def test_history_streams_and_duplicate_draws(self):
        h=self.history("pick3",3)
        self.assertEqual(self.store.put(h),3);self.assertEqual(self.store.put(h),0)
        self.assertEqual(len(self.store.history("pick3","Night")),3)
        self.assertEqual(self.store.history("pick3","Day"),[])

if __name__=="__main__":unittest.main()
