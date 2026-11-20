"""Research formula: pooled digit probabilities -> optimal complete Box sets.

Never select the same unordered multiset in multiple positions. A rotation
of the same digits is NOT another Any Order opportunity. This is the
mathematically optimal coverage for a portfolio of equal-cost, independent
complete Box outcomes under the explicitly estimated iid-digit model.
It is a RESEARCH formula; the calibrated live engine remains unchanged.
"""
from __future__ import annotations

from itertools import combinations_with_replacement
import math

from research_pooled_digit_followup import probabilities, WINDOW
from val_box import any_order_prize, box_ways, digits_key, random_box_picks

VERSION="pooled_full_box_v2"
GAMES=("pick3","pick4","pick5")


def pooled_probabilities(game,prior):
    if game not in GAMES:
        raise ValueError("Unsupported Box game")
    if len(prior)<500:
        raise ValueError("At least 500 earlier draws required")
    width=int(game[-1])
    counts=[0]*10
    for row in prior[-WINDOW:]:
        numbers=row["numbers"]
        if len(numbers)!=width or any(type(d)!=int or not 0<=d<=9 for d in numbers):
            raise ValueError("Invalid prior digit draw")
        for d in numbers:
            counts[d]+=1
    return probabilities(counts,width)


def box_mass(combination,prob):
    if len(prob)!=10:
        raise ValueError("Ten probabilities required")
    return box_ways(combination)*math.prod(prob[d] for d in combination)


def top_box_portfolio(game,prob,count=3):
    """Maximize sum of probabilities of distinct Box ticket outcome sets.

    These Box events cannot overlap, hence greedy highest-mass is globally
    optimal at fixed count under this model. No simulation is needed to
    determine the exact top combinations.
    """
    if game not in GAMES or len(prob)!=10 or not 1<=count<=5:
        raise ValueError("Invalid Box formula arguments")
    if any(not math.isfinite(p) or p<=0 for p in prob) or (
            abs(sum(prob)-1)>1e-9):
        raise ValueError("Invalid probability simplex")
    width=int(game[-1])
    ranked=[
        (box_mass(combo,prob),combo)
        for combo in combinations_with_replacement(range(10),width)
        if any_order_prize(game,combo)>0
    ]
    ranked.sort(key=lambda x:(-x[0],x[1]))
    return [dict(numbers=list(combo),play_type="any_order",rank=k+1,
                 model_box_probability=p,box_ways=box_ways(combo),
                 formula_version=VERSION)
            for k,(p,combo) in enumerate(ranked[:count])]


def predicted_coverage(game,picks,prob):
    if game not in GAMES:
        raise ValueError(game)
    unique={digits_key(p["numbers"]) for p in picks
            if any_order_prize(game,p["numbers"])>0}
    return sum(box_mass(combo,prob) for combo in unique)


def fair_coverage(game,picks):
    width=int(game[-1])
    return predicted_coverage(game,picks,[.1]*10)


def generate(game,prior,count=3,rng=None):
    prob=pooled_probabilities(game,prior)
    model=top_box_portfolio(game,prob,count)
    controls=random_box_picks(game,count,rng)
    return dict(probabilities=prob,
                model_tickets=[p["numbers"] for p in model],
                control_tickets=[p["numbers"] for p in controls],
                model_box_mass=predicted_coverage(game,model,prob),
                control_box_mass=predicted_coverage(game,controls,prob),
                model_fair_coverage=fair_coverage(game,model),
                control_fair_coverage=fair_coverage(game,controls))
