import random
import unittest
from datetime import datetime,timedelta,timezone
from research_pooled_digit_followup import probabilities,evaluate
from research_digit_accuracy_v3 import build

class PooledFollowupTests(unittest.TestCase):
    def history(self,n=900):
        rng=random.Random(12)
        at=datetime(2025,1,1,tzinfo=timezone.utc)
        return [dict(game="pick3",at=(at+timedelta(hours=12*i)).isoformat(),
                     stream="Day" if i%2 else "Night",
                     numbers=[rng.randrange(10) for _ in range(3)]) for i in range(n)]
    def test_match_original_prospective_formula(self):
        h=self.history()
        m=build("pick3",h,"Night",1,5)["pooled_digit_bias"]
        counts=[0]*10
        for r in h:
            for d in r["numbers"]: counts[d]+=1
        p=probabilities(counts,3)
        for position in m:
            for a,b in zip(position,p):self.assertAlmostEqual(a,b)
    def test_later_draws_not_used_in_their_forecasts(self):
        h=self.history(900)
        a=evaluate("pick3",h)
        changed=self.history(900)
        changed[-1]["numbers"]=[9,9,9]
        b=evaluate("pick3",changed)
        self.assertEqual(a["results"]["all"]["draws"],b["results"]["all"]["draws"])
        self.assertNotEqual(a["results"]["all"],b["results"]["all"])

if __name__=="__main__":unittest.main()
