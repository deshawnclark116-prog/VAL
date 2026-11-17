import math
import random
import unittest
from research_keno_dependencies import (
    PAIR_NULL, LAGS, pair_discovery, lag_analysis, frequency_anomalies,
    fit_models, forecasts, top_five, two_sided_z, corrected, analyze
)

def fair_rows(n=540):
    rng=random.Random(9833)
    rows=[]
    for i in range(n):
        rows.append(dict(draw_id=i+1000,date="2026-11-01",
                         timestamp="2026-11-01T12:00:00",
                         numbers=sorted(rng.sample(range(1,81),20))))
    return rows

class KenoDependenciesTests(unittest.TestCase):
    def test_marginal_null_and_bonferroni(self):
        self.assertAlmostEqual(PAIR_NULL,380/6320)
        self.assertAlmostEqual(two_sided_z(0),1)
        self.assertEqual(corrected(.0001,1000),.1)
        self.assertEqual(corrected(.2,10),1)
    def test_distribution_forecasts_sum_to_20_and_bounded(self):
        rows=fair_rows(1350)
        fit=fit_models(rows[:1200])
        p=forecasts(fit,rows[1199],True)
        for name,vals in p.items():
            self.assertAlmostEqual(sum(vals),20,places=8)
            self.assertTrue(all(0<x<1 for x in vals))
            self.assertEqual(len(top_five(vals,1011,name)),5)
        # Skip missing draw IDs: no credit to lagged dependence.
        gap=forecasts(fit,rows[1199],False)
        self.assertEqual(gap["lag_repeat"],[.25]*80)
        self.assertEqual(gap["transition"],[.25]*80)
    def test_pair_and_lag_consider_only_prior_and_unique_ids(self):
        rows=fair_rows(130)
        result=pair_discovery(rows[:90],rows[90:])
        self.assertEqual(result["tests"],3160)
        self.assertEqual(len(result["top_discovery_20_with_validation"]),20)
        a=lag_analysis(rows)
        self.assertEqual([x["lag"] for x in a["lags"]],list(LAGS))
        self.assertEqual(a["lags"][0]["complete_pairs"],129)
        # Gap in draw IDs excludes nonconsecutive pairs.
        rows[70]["draw_id"]=5000
        a2=lag_analysis(rows)
        self.assertLess(a2["lags"][0]["complete_pairs"],129)
    def test_reproducible_separate_discovery_and_validation(self):
        rows=fair_rows(3700)
        r1=analyze(rows)
        r2=analyze(rows)
        self.assertEqual(r1,r2)
        self.assertEqual(r1["chronological_validation_draws"],1480)
        for name,score in r1["out_of_sample_one_ticket"]["prediction_models"].items():
            self.assertEqual(score["draws"],1480)
            self.assertEqual(sum(score["hit_distribution"].values()),1480)

if __name__=="__main__":unittest.main()
