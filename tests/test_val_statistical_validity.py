"""Falsification tests for VAL's exact complete Box validity gate."""
import math
import unittest
from research_val_statistical_validity import (
    binom_upper_tail, required_draws, exact_paired_equal_coverage,
    fair_union,historical_audit,prospective_audit,
)


class StatisticalValidityTests(unittest.TestCase):
    def test_binomial_survival_exact_tiny_distributions(self):
        self.assertAlmostEqual(binom_upper_tail(2,.2,1),.36)
        self.assertAlmostEqual(binom_upper_tail(2,.2,2),.04)
        self.assertAlmostEqual(binom_upper_tail(10,.5,8),56/1024)
        self.assertAlmostEqual(binom_upper_tail(3,.018,1),
                               1-(1-.018)**3)
        self.assertEqual(binom_upper_tail(0,.018,1),0.)
        self.assertEqual(binom_upper_tail(10,.018,11),0.)
        self.assertEqual(binom_upper_tail(10,.018,0),1.)

    def test_paired_proof_is_not_raw_two_independent_win_counts(self):
        result=exact_paired_equal_coverage(8,2)
        self.assertEqual(result["discordant"],10)
        self.assertAlmostEqual(result["one_sided_p"],56/1024)
        self.assertEqual(result["net_model_only_advantage"],6)
        self.assertEqual(
            exact_paired_equal_coverage(0,0)["one_sided_p"],1.)

    def test_unordered_ticket_union_blocks_fake_permutation_coverage(self):
        self.assertAlmostEqual(
            fair_union("pick3",[[0,1,2],[3,4,5],[6,7,8]]),.018)
        self.assertAlmostEqual(
            fair_union("pick4",[[0,1,2,3],[1,2,3,4],[4,5,6,7]]),.0072)
        self.assertAlmostEqual(
            fair_union("pick5",[[0,1,2,3,4],[1,2,3,4,5],[4,5,6,7,8]]),
            .0036)
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            fair_union("pick3",[[0,1,2],[2,0,1],[3,4,5]])
        with self.assertRaisesRegex(ValueError,"isn't"):
            fair_union("pick3",[[0,0,0],[2,3,4],[5,6,7]])

    def test_sample_sizes_reproduce_exact_one_sided_design(self):
        cases=[("pick3",.018,8491),("pick4",.0072,21466),
               ("pick5",.0036,43167)]
        for game,p0,expected_n in cases:
            x=required_draws(p0)
            self.assertEqual(x["draws"],expected_n,game)
            self.assertGreaterEqual(x["achieved_power"],.8)
            self.assertLessEqual(x["null_tail_at_threshold"],.05/3)
            self.assertAlmostEqual(x["alternative_hit_probability"],
                                   p0*1.25)

    def test_reused_historical_results_are_never_confirmatory(self):
        source={"games":{}}
        for g in ("pick3","pick4","pick5"):
            p={"pick3":.018,"pick4":.0072,"pick5":.0036}[g]
            source["games"][g]={"events":[
                dict(v2_win=1,random_win=0,v2_fair_prob=p,
                     random_fair_prob=p),
                dict(v2_win=0,random_win=1,v2_fair_prob=p,
                     random_fair_prob=p),
                dict(v2_win=1,random_win=1,v2_fair_prob=p,
                     random_fair_prob=p),
            ]}
        result=historical_audit(source)
        for game,x in result.items():
            self.assertFalse(x["confirmatory_valid"])
            self.assertEqual(x["model_only"],1)
            self.assertEqual(x["control_only"],1)
            self.assertEqual(x["both"],1)
            self.assertAlmostEqual(
                x["paired_exploratory_only"]["one_sided_p"],.75)
        # Unequal portfolios must not get an invalid 50/50 McNemar p-value.
        source["games"]["pick3"]["events"][0]["v2_fair_prob"]=.012
        bad=historical_audit(source)["pick3"]
        self.assertEqual(bad["coverage_mismatches"],1)
        self.assertIsNone(bad["paired_exploratory_only"])

    def test_prospective_freezing_and_result_grading_are_verified(self):
        model=[[0,1,2],[3,4,5],[6,7,8]]
        ctrl=[[0,2,3],[1,4,5],[2,7,9]]
        base=dict(
            id="test",
            created_utc="2026-11-20T21:00:00+00:00",
            target=dict(game="pick3",
                        date="2026-11-20",stream="Night",
                        wagers_close_utc="2026-11-21T03:45:00+00:00"),
            forecast=dict(model_tickets=model,
                          uniform_coverage_controls=ctrl,
                          model_fair_full_box_coverage=.018,
                          control_fair_full_box_coverage=.018),
            result=dict(official_numbers=[8,7,6],accuracy=dict(
                model_box_wins=1,control_box_wins=0)))
        source=dict(games={"pick3":[base],"pick4":[],"pick5":[]})
        audit=prospective_audit(source)["pick3"]
        self.assertEqual(audit["settled"],1)
        self.assertEqual(audit["model_only"],1)
        self.assertEqual(audit["invalid_records"],[])
        self.assertEqual(audit["paired_evidence"]["one_sided_p"],.5)
        base["created_utc"]="2026-11-21T04:00:00+00:00"
        bad=prospective_audit(source)["pick3"]
        self.assertEqual(len(bad["invalid_records"]),1)
        self.assertIsNone(bad["paired_evidence"])


if __name__=="__main__":
    unittest.main()
