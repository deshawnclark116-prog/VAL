import unittest
from datetime import datetime,timedelta,timezone
from research_digit_formula_placebos import (
  fair_tickets,analyze,exact_tail
)

class PlaceboAuditTests(unittest.TestCase):
    def test_deterministic_unique_tickets(self):
        x=fair_tickets("pick4","2026-11-16T04:00:00+00:00",7,3)
        self.assertEqual(x,fair_tickets("pick4","2026-11-16T04:00:00+00:00",7,3))
        self.assertEqual(len({tuple(y["numbers"]) for y in x}),3)
        self.assertNotEqual(x,fair_tickets("pick4","2026-11-16T04:00:00+00:00",8,3))
    def test_exact_probability(self):
        self.assertAlmostEqual(exact_tail(1,.1,1),.1)
        self.assertAlmostEqual(exact_tail(1,.1,0),1)
        self.assertAlmostEqual(exact_tail(2,.1,2),.01)
    def test_replicates_never_select_favorable_seed(self):
        base=datetime(2025,1,1,tzinfo=timezone.utc)
        history=[dict(game="pick3",stream="Day",
                      at=(base+timedelta(days=i)).isoformat(),numbers=[2,3,4])
                 for i in range(20)]
        records=[dict(at=x["at"],uniform_control=dict(exact=0,
                    tickets=["314","888","246"],position_matches=0))
                 for x in history]
        result=analyze("pick3",records,history,seeds=5)
        self.assertEqual(result["replicate_count"],5)
        self.assertEqual(result["targets"],20)
        self.assertEqual(result["observed_original_control_straight_wins"],0)
        self.assertEqual(sum(result["replicate_exact_win_histogram"].values()),5)
    def test_rejects_duplicate_target(self):
        r=[dict(at="2025-01-01T00:00:00+00:00",
                uniform_control=dict(exact=0,tickets=["111","222","333"],position_matches=0))]*2
        with self.assertRaises(ValueError):analyze("pick3",r,[],seeds=2)

if __name__=="__main__":unittest.main()
