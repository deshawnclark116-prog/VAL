"""Mathematical, temporal and causal-feature tests for VAL contextual v1."""
import math
import random
import unittest
from datetime import date,timedelta

from val_contextual_regime_box import (
    ContextualBox, _features, _date, full_box_mass, forecast_full_box,
    VERSION, ALL_EXPERTS,
)
from val_box import digits_key,box_ways


class ContextualTests(unittest.TestCase):
    def target(self,day="2026-11-20",stream="Night",eid=None,
               published="2026-11-20T16:00:00+00:00",
               observed="2026-11-20T16:01:00+00:00",pretests=None):
        row=dict(date=day,stream=stream,
                 wagers_close_utc="2026-11-21T03:45:00+00:00")
        if eid is not None:
            row["observables"]={"equipment_id":dict(
                value=eid,source_url="synthetic-test://public-observation",
                published_at_utc=published,observed_at_utc=observed)}
        if pretests is not None:
            row.setdefault("observables",{})["pretests"]=dict(
                value=pretests,
                source_url="synthetic-test://public-pretest",
                published_at_utc=published,observed_at_utc=observed)
        return row

    def test_full_multiset_mass_includes_every_permutation(self):
        for game in ("pick3","pick4","pick5"):
            w=int(game[-1])
            bias=[[.09]*9+[.19] for _ in range(w)]
            for key in ((9,)*w,tuple(range(w)),(0,)*(w-1)+(9,)):
                fair=box_ways(key)*math.prod(bias[0][d] for d in key)
                self.assertAlmostEqual(full_box_mass(game,bias,key),fair,12)

    def test_target_utc_night_is_mapped_to_draw_location_weekday(self):
        target={"at":"2026-11-21T04:00:00+00:00",
                "stream":"Night"}
        self.assertEqual(_date(target).isoformat(),"2026-11-20")

    def test_frozen_probs_normalized_and_all_candidate_sets_distinct(self):
        for game in ("pick3","pick4","pick5"):
            m=ContextualBox(game)
            target=self.target()
            frozen=m.forecast(target)
            self.assertEqual(frozen["observed_before"],0)
            self.assertAlmostEqual(sum(frozen["weights"].values()),1.,12)
            selected=m.choose(frozen)
            self.assertEqual(len(selected["picks"]),3)
            self.assertEqual(len({digits_key(x) for x in selected["picks"]}),3)
            self.assertAlmostEqual(
                selected["fair_full_box_probability"],
                3*math.factorial(int(game[-1]))/10**int(game[-1]),
                12)
            self.assertAlmostEqual(
                m.score(frozen,[0]*int(game[-1]))["log_gain"],0.,12)

    def test_no_hidden_machine_or_target_draw_in_features(self):
        m=ContextualBox("pick3")
        t=self.target()
        t["machine"]=0
        t["pretests"]=[[9,9,9]]
        t["numbers"]=[8,8,8]
        ready=m.forecast(t)
        self.assertEqual(ready["eligible_features"],())
        bad=dict(t,numbers=[0,0,0],machine=1)
        self.assertEqual(m.forecast(bad),ready)
        self.assertEqual(m.choose(ready),m.choose(m.forecast(bad)))

    def test_late_or_unproven_equipment_does_not_leak(self):
        baseline=ContextualBox("pick3").forecast(self.target())
        cases=[
            self.target(eid="X",published="2026-11-21T04:00:00+00:00"),
            self.target(eid="X",observed="2026-11-21T04:01:00+00:00"),
        ]
        for row in cases:
            self.assertEqual(_features(row),{})
            self.assertEqual(ContextualBox("pick3").forecast(row),baseline)
        no_source=self.target(eid="X")
        no_source["observables"]["equipment_id"]["source_url"]=""
        self.assertEqual(_features(no_source),{})
        no_cutoff=self.target(eid="X")
        no_cutoff.pop("wagers_close_utc")
        self.assertEqual(_features(no_cutoff),{})
        valid=self.target(eid="X",pretests=[[1,2,3],[4,5,6]])
        self.assertEqual(set(_features(valid)),{"equipment_id","pretests"})

    def test_published_equipment_can_change_prediction_and_missing_cannot(self):
        m=ContextualBox("pick3",long_window=500,short_window=100)
        rng=random.Random(103)
        start=date(2025,1,1)
        for i in range(500):
            day=(start+timedelta(days=i)).isoformat()
            equipment="A" if i%2==0 else "B"
            t=self.target(day=day,eid=equipment)
            if equipment=="A":
                winner=[7 if rng.random()<.70 else rng.randrange(10)
                        for _ in range(3)]
            else:
                winner=[2 if rng.random()<.70 else rng.randrange(10)
                        for _ in range(3)]
            frozen=m.forecast(t)
            m.observe(t,winner,frozen)
        a=m.forecast(self.target(eid="A"))
        b=m.forecast(self.target(eid="B"))
        hidden=m.forecast(self.target())
        self.assertIn("equipment",a["models"])
        self.assertIn("equipment",b["models"])
        self.assertNotIn("equipment",hidden["models"])
        self.assertGreater(a["models"]["equipment"][0][7],
                           b["models"]["equipment"][0][7])
        self.assertGreater(b["models"]["equipment"][0][2],
                           a["models"]["equipment"][0][2])

    def test_calendar_is_observed_exogenous_context(self):
        m=ContextualBox("pick3",long_window=500,short_window=100)
        day=date(2025,1,1)
        for i in range(350):
            t=self.target(day=(day+timedelta(days=i)).isoformat(),
                          stream="Day" if i%2==0 else "Night")
            winner=[1,1,1] if i%2==0 else [6,6,6]
            frozen=m.forecast(t)
            m.observe(t,winner,frozen)
        a=m.forecast(self.target(day="2026-11-20",stream="Day"))
        b=m.forecast(self.target(day="2026-11-20",stream="Night"))
        self.assertGreater(a["models"]["calendar"][0][1],
                           b["models"]["calendar"][0][1])

    def test_forecast_must_be_frozen_before_observation(self):
        m=ContextualBox("pick3")
        t=self.target()
        f=m.forecast(t)
        m.observe(t,[1,2,3],f)
        with self.assertRaisesRegex(ValueError,"not frozen"):
            m.observe(t,[9,9,9],f)


if __name__=="__main__":
    unittest.main()
