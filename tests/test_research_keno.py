import random
import unittest
from research_keno import (
    parse_results,match_count,exact_fair_match_probabilities,grade_method,
    evaluate
)


class KenoResearchTests(unittest.TestCase):
    def test_parse_realistic_date_draw_and_duplicate(self):
        seq=" ".join(map(str,[1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39]))
        records=[]
        for i in range(55):
            records.append(f"<p>Mon 16th November 2026 • Draw #{807300+i}</p>"
                           f"<ul><li>{seq.replace(' ','</li><li>')}</li></ul>")
        records.append(records[-1])
        parsed,quality=parse_results("<html><body>"+ "".join(records)+"</body></html>")
        self.assertEqual(len(parsed),55)
        self.assertEqual(quality["duplicate_listings"],1)
        self.assertEqual(parsed[0]["draw_id"],807300)
        self.assertEqual(parsed[-1]["numbers"][-1],39)

    def test_fair_keno_matches(self):
        p=exact_fair_match_probabilities()
        self.assertAlmostEqual(sum(p.values()),1)
        self.assertAlmostEqual(sum(k*prob for k,prob in p.items()),1.25)
        self.assertLess(p[5],.001)
        # Current Keno with BULLS-EYE main-game five-spot also pays for 0 hits.
        from research_keno import PRIZE_FIVE_SPOT
        self.assertEqual(PRIZE_FIVE_SPOT[0],2)
        self.assertAlmostEqual(sum(p[k]*PRIZE_FIVE_SPOT[k] for k in range(6)),1.1543,places=3)
        self.assertEqual(match_count([1,2,3,4,5],list(range(1,21))),5)
        self.assertEqual(match_count([1,2,3,4,5],list(range(60,80))),0)

    def test_bad_draw_rejected(self):
        with self.assertRaises(ValueError):
            match_count([1,1,2,3,4],list(range(1,21)))
        with self.assertRaises(ValueError):
            match_count([1,2,3,4,5],[1]*20)

    def test_methods_with_no_leakage_and_baseline(self):
        rng=random.Random(919)
        rows=[
            {"draw_id":30000+i,"date":f"2026-10-{1+i//5:02d}",
             "numbers":sorted(rng.sample(range(1,81),20))}
            for i in range(65)
        ]
        one=evaluate(rows,train=30,picks_per_method=3,seed=92)
        self.assertEqual(one,evaluate(rows,train=30,picks_per_method=3,seed=92))
        self.assertEqual(one["random_control"]["tickets"],105)
        for name,method in one["methods"].items():
            self.assertEqual(method["tickets"],105)
            self.assertEqual(sum(method["distribution_matches"].values()),105)
            self.assertEqual(method["three_or_more_tickets"],
                             sum(method["distribution_matches"][str(k)] for k in (3,4,5)))
        # Future outcomes must not rewrite earlier targets; regrade the same
        # first historical window by limiting to the first 50 draws.
        sample=evaluate(rows[:50],train=30,picks_per_method=3,seed=92)
        alternate=rows[:50]+[dict(rows[50],numbers=sorted(rng.sample(range(1,81),20)))]
        new=evaluate(alternate,train=30,picks_per_method=3,seed=92)
        for name in sample["methods"]:
            self.assertEqual(
                sum(sample["methods"][name]["distribution_matches"].values()),60)
            self.assertEqual(sum(new["methods"][name]["distribution_matches"].values()),63)


if __name__=="__main__":unittest.main()
