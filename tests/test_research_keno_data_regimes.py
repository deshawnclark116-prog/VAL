import unittest
from research_keno_data_regimes import analyze

def rec(i,stamp,bonus=None):
    return {"draw_id":i,"timestamp":stamp,"date":stamp[:10],
            "numbers":list(range(1,21)),"bullseye":bonus}

class KenoDataRegimesTests(unittest.TestCase):
    def test_updating_game_not_assumed_new_rng(self):
        rows=[
            rec(41,"2026-11-16T00:54:00"),
            rec(42,"2026-11-16T00:58:00"),
            rec(43,"2026-11-16T09:46:00",13)
        ]
        v=analyze(rows)
        self.assertEqual(v["segments"]["before_announced_nov16_2026_update"]["count"],2)
        self.assertEqual(v["segments"]["on_or_after_announced_nov16_2026_update"]["count"],1)
        self.assertEqual(v["segments"]["on_or_after_announced_nov16_2026_update"]["bullseye_non_null"],1)
        self.assertIn("NOT established",v["source_limitations"][3])
    def test_draw_gaps_and_validation(self):
        rows=[rec(7,"2026-11-15T23:56:00"),rec(10,"2026-11-15T23:59:00")]
        v=analyze(rows)
        self.assertEqual(v["missing_draw_ids"],2)
        self.assertEqual(v["draw_id_gaps"][0]["missing"],2)
        with self.assertRaises(ValueError):
            analyze(rows[::-1])
        bad=[rec(7,"2026-11-15T23:56:00"),rec(8,"2026-11-15T23:59:00")]
        bad[1]["numbers"]=[1]*20
        with self.assertRaises(ValueError):
            analyze(bad)

if __name__=="__main__":unittest.main()
