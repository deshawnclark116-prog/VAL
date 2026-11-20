"""Regression: VAL full Any Order is multiset coverage, not ticket rotations."""
import random
import unittest
from datetime import date,timedelta

from val_pooled_box_formula import (
    box_mass,top_box_portfolio,predicted_coverage,fair_coverage,
    pooled_probabilities,generate,
)
from val_box import distinct_permutations,box_ways
from research_prospective_pooled_box_v2 import prepare,update


def fixture(game="pick3",n=1100):
    rng=random.Random(932)
    width=int(game[-1])
    start=date(2024,1,1)
    return [
        dict(date=(start+timedelta(days=i//2)).isoformat(),
             stream="Day" if i%2==0 else "Night",
             numbers=[rng.randrange(10) for _ in range(width)],
             fireball=None)
        for i in range(n)
    ]


class PooledFullBoxFormulaTests(unittest.TestCase):
    def test_new_formula_covers_three_times_as_many_outcomes_at_fair_null(self):
        for game in ("pick3","pick4","pick5"):
            width=int(game[-1])
            uniform=[.1]*10
            portfolio=top_box_portfolio(game,uniform,3)
            combos=[tuple(sorted(x["numbers"])) for x in portfolio]
            self.assertEqual(len(set(combos)),3)
            self.assertTrue(all(box_ways(c)==__import__("math").factorial(width)
                                for c in combos))
            rotated=[{"numbers":list(range(width))[k:]+
                      list(range(width))[:k]} for k in range(3)]
            self.assertAlmostEqual(
                fair_coverage(game,portfolio),
                3*fair_coverage(game,rotated),places=12)
            self.assertAlmostEqual(
                fair_coverage(game,portfolio),
                3*__import__("math").factorial(width)/10**width,places=12)

    def test_box_probability_exactly_sums_distinct_orderings(self):
        prob=[.072]*9+[.352]
        for game in ("pick3","pick4","pick5"):
            width=int(game[-1])
            for c in (tuple(range(width)),(9,)*(width-1)+(8,)):
                truth=sum(__import__("math").prod(prob[d] for d in x)
                          for x in distinct_permutations(c))
                self.assertAlmostEqual(box_mass(c,prob),truth,places=12)

    def test_optimized_portfolio_beats_legacy_three_rotations_under_own_model(self):
        for game in ("pick3","pick4","pick5"):
            history=fixture(game)
            probability=pooled_probabilities(game,history)
            rank=sorted(range(10),key=lambda d:(-probability[d],d))
            width=int(game[-1])
            old=[{"numbers":[rank[(k+j)%3] for j in range(width)]}
                 for k in range(3)]
            new=top_box_portfolio(game,probability,3)
            self.assertGreater(
                predicted_coverage(game,new,probability),
                predicted_coverage(game,old,probability)+1e-8)

    def test_future_outcome_cannot_rewrite_frozen_picks(self):
        for game in ("pick3","pick4","pick5"):
            history=fixture(game)
            target={"date":"2026-11-20","stream":"Night","game":game}
            prior=prepare(game,target,history)
            rows=fixture(game)+[dict(date="2026-11-20",stream="Night",
                                       numbers=[9]*int(game[-1]),
                                       fireball=None)]
            later=prepare(game,target,rows)
            self.assertEqual(prior,later)
            self.assertEqual(len({tuple(sorted(x)) for x in
                                  prior["model_tickets"]}),3)
            self.assertEqual(len({tuple(sorted(x)) for x in
                                  prior["uniform_coverage_controls"]}),3)
            self.assertAlmostEqual(prior["model_fair_full_box_coverage"],
                                   prior["control_fair_full_box_coverage"],
                                   places=12)
            self.assertEqual(len(prior["model_tickets"]),3)

    def test_null_fallback_controls_are_unbiased_maximum_coverage(self):
        history=fixture()
        result=generate("pick3",history,rng=random.Random(5))
        self.assertGreater(result["model_box_mass"],0.)
        self.assertAlmostEqual(result["control_fair_coverage"],.018,places=12)
        self.assertEqual(len({tuple(sorted(a)) for a in
                              result["control_tickets"]}),3)


if __name__=="__main__":
    unittest.main()
