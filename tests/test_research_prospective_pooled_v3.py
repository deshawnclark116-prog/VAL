import copy
import random
import unittest
from datetime import date,datetime,timedelta,timezone
from research_prospective_pooled_v3 import VERSION,prepare,grade,update

def fixture(n=1100):
    rng=random.Random(93)
    start=date(2024,1,1)
    return [dict(date=(start+timedelta(days=i//2)).isoformat(),
        stream="Day" if i%2==0 else "Night",
        numbers=[rng.randrange(10) for _ in range(3)],fireball=None)
        for i in range(n)]

class ProspectivePooledTests(unittest.TestCase):
    def test_candidate_diversity_and_uniform_control(self):
        h=fixture()
        target={"date":"2026-11-20","stream":"Day","game":"pick3"}
        p=prepare("pick3",target,h)
        self.assertEqual(len(p["model_tickets"]),3)
        self.assertEqual(len(p["uniform_coverage_controls"]),3)
        for column in range(3):
            self.assertEqual(len({row[column] for row in p["model_tickets"]}),3)
            self.assertEqual(len({row[column] for row in p["uniform_coverage_controls"]}),3)
        self.assertAlmostEqual(sum(p["probability_by_digit"]),1)
    def test_target_immutable_and_settlement_explicit(self):
        h=fixture()
        now=datetime(2026,11,19,12,0,tzinfo=timezone.utc)
        records,changes=update("pick3",h,[],now)
        self.assertEqual(changes["created"],1)
        initial=copy.deepcopy(records[0]["forecast"])
        target=records[0]["target"]
        self.assertIsNone(records[0]["result"])
        replay,changes=update("pick3",h,records,now)
        self.assertEqual(changes["created"],0)
        self.assertEqual(replay,records)
        later=fixture()
        later.append({"date":target["date"],"stream":target["stream"],
                      "numbers":[8,9,9],"fireball":7})
        after=datetime(2026,11,20,22,0,tzinfo=timezone.utc)
        settled,changes=update("pick3",later,records,after)
        self.assertEqual(changes["settled"],1)
        self.assertEqual(settled[0]["forecast"],initial)
        self.assertEqual(settled[0]["result"]["official_numbers"],[8,9,9])
        self.assertIn("accuracy",settled[0]["result"])
    def test_no_future_leakage_in_predictor(self):
        h=fixture()
        target={"date":"2026-11-20","stream":"Night","game":"pick3"}
        a=prepare("pick3",target,h)
        modified=fixture()
        modified.append({"date":"2026-11-20","stream":"Day",
                         "numbers":[9,9,9],"fireball":5})
        # Day result legitimately becomes available for the Night forecast;
        # a result for the SAME Night target cannot enter the model.
        b=prepare("pick3",target,modified)
        self.assertNotEqual(a["training_size"],b["training_size"])
        modified.append({"date":"2026-11-20","stream":"Night",
                         "numbers":[7,7,7],"fireball":4})
        c=prepare("pick3",target,modified)
        self.assertEqual(b,c)

if __name__=="__main__":unittest.main()
