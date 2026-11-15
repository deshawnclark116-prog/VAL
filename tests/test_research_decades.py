import math
import unittest

from research_decades import (
    bonferroni, chi_uniform, gammaincc, parse_complete_archive,
    prospective_log_scores, same_digit_binomial,
)


class FullHistoryAuditTests(unittest.TestCase):
    def test_gamma_distribution(self):
        self.assertAlmostEqual(gammaincc(0.5, 0.5), math.erfc(math.sqrt(.5)), places=10)
        self.assertAlmostEqual(gammaincc(1.0, 1.0), math.exp(-1), places=10)
        self.assertAlmostEqual(gammaincc(2.0, 3.0), math.exp(-3) * (1+3), places=10)

    def test_uniform_digits(self):
        p=chi_uniform([100]*10)
        self.assertAlmostEqual(p["p"],1,places=10)
        self.assertEqual(p["counts"],[100]*10)
        self.assertGreater(chi_uniform([1000]+[0]*9)["chi_square"],8000)

    def test_duplicate_and_missing_fireball_zero(self):
        sample = ("Results for Pick 3\n"
                  "05/22/1989; Night: 9,1,4\n"
                  "11/13/2026; Day: 0,0,2; Fireball: 0; Night: 1,0,1; Fireball: 9\n"
                  "All information is entered manually, and is subject to human error.\n"
                  "Therefore, we can not guarantee the accuracy of this information.\n")
        # Full production parser intentionally rejects archives this short.
        from unittest.mock import patch
        with patch("research_decades.MIN_ROWS",{"pick3":3}):
            rows=parse_complete_archive("pick3",sample)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["date"],"1989-05-22")
        self.assertIsNone(rows[0]["fireball"])
        self.assertEqual(rows[1]["numbers"],[0,0,2])
        self.assertEqual(rows[1]["fireball"],0)
        self.assertEqual(rows[2]["numbers"],[1,0,1])

    def test_reject_unknown_source_line(self):
        from unittest.mock import patch
        with patch("research_decades.MIN_ROWS",{"pick3":1}):
            with self.assertRaises(ValueError):
                parse_complete_archive("pick3","Results for Pick 3\n1/1/1999; Bonus: 5\n")

    def test_exact_p_adjustment(self):
        hyps=bonferroni([{"p":.001},{"p":.015},{"p":.9}])
        self.assertEqual(hyps[0]["adjusted_p_bonferroni"],.003)
        self.assertTrue(hyps[0]["passes_fwer_0_05"])

    def test_walkforward_is_leak_free(self):
        rows = [{"date":f"{1989+i//340:04d}-{i%28+1:02d}-10",
                 "stream": "Day" if i%2 == 0 else "Night",
                 "numbers": [i%10,(i//3)%10,(i//7)%10],
                 "fireball":None} for i in range(560)]
        before=prospective_log_scores("pick3",rows)
        copy=[dict(r) for r in rows]
        copy[-1]["numbers"]=[9,9,9]
        after=prospective_log_scores("pick3",copy)
        self.assertNotEqual(before["last_100"]["full"]["mean_log_score_advantage_per_draw"],
                            after["last_100"]["full"]["mean_log_score_advantage_per_draw"])

    def test_consecutive_test_expected(self):
        z=same_digit_binomial(100,1000,.1)
        self.assertAlmostEqual(z["expected"],100)
        self.assertAlmostEqual(z["p"],1)


if __name__=="__main__":unittest.main()
