"""Virginia Pick 3/4/5 ANY ORDER (Box) ticket mathematics.

The user's target is a complete multiset match, not a count of digits
appearing in correct positions. Every digit multiplicity must agree.

Payouts are the Virginia Lottery's advertised $1 Any Order prizes,
WITHOUT Fireball, Combo, or 50/50. This is paper accounting only.
An all-identical ticket has one permutation and is not an Any Order
play type; it can instead be evaluated separately as a Straight.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from itertools import combinations_with_replacement, permutations

BOX_PRIZES_USD = {
    "pick3": {3:160, 6:80},
    "pick4": {4:1200, 6:800, 12:400, 24:200},
    "pick5": {5:10000, 10:5000, 20:2500, 30:1650, 60:800, 120:400},
}
BOX_STAKE_USD = 1


def digits_key(numbers):
    """Sorted multiset key: duplicates are retained, zeros are not lost."""
    return tuple(sorted(numbers))


def box_ways(numbers):
    counts=Counter(numbers)
    # Exact integer factorial ratio; repeated digits must be preserved.
    return math.factorial(len(numbers)) // math.prod(
        math.factorial(n) for n in counts.values())


def any_order_prize(game,numbers):
    return BOX_PRIZES_USD.get(game,{}).get(box_ways(numbers),0)


def fair_any_order_probability(game,numbers):
    if game not in BOX_PRIZES_USD:raise ValueError("Not a digit Box game")
    if any_order_prize(game,numbers)<=0:return 0.
    return box_ways(numbers)/10**len(numbers)


def is_any_order_win(game,numbers,winning_numbers):
    return bool(any_order_prize(game,numbers)) and digits_key(numbers)==digits_key(winning_numbers)


def distinct_permutations(numbers):
    """The permutations of an entire digit multiset (not partial hits)."""
    return sorted(set(permutations(numbers)))


def random_box_picks(game,count=3,rng=None):
    """Equal-cost random controls, each covering the maximum distinct orders.

    Under a fair independent digit draw, all-distinct digit Box tickets
    cover the most outcomes per $1 Any Order wager. Keys never overlap.
    """
    if game not in BOX_PRIZES_USD:raise ValueError("Not a digit Box game")
    if not 1<=count<=20:raise ValueError("Choose 1-20 Box tickets")
    rng=rng or random.SystemRandom()
    width=int(game[-1])
    selected=set()
    while len(selected)<count:
        chosen=tuple(sorted(rng.sample(range(10),width)))
        selected.add(chosen)
    return [dict(numbers=list(a),bonus=None,play_type="any_order",
                 box_ways=box_ways(a)) for a in sorted(selected)]


def box_score_batch(game,picks,draw):
    """Evaluate explicit hypothetical $1 Any Order tickets; no fake prizes."""
    if game not in BOX_PRIZES_USD:
        return dict(box_wins=0,box_tickets=0,box_payout_usd=0,
                    box_spend_usd=0,box_net_usd=0,
                    box_fair_expected_wins=0.,box_fair_at_least_one_prob=0.)
    winners=draw["numbers"]
    paid=spent=wins=tickets=0
    expected=0.
    unique={}
    for pick in picks:
        numbers=pick["numbers"]
        prize=any_order_prize(game,numbers)
        if prize==0:
            continue
        tickets+=1
        spent+=BOX_STAKE_USD
        ways=box_ways(numbers)
        expected+=ways/10**len(numbers)
        unique[digits_key(numbers)]=ways
        if digits_key(numbers)==digits_key(winners):
            paid+=prize
            wins+=1
    return dict(box_wins=wins,box_tickets=tickets,box_payout_usd=paid,
                box_spend_usd=spent,box_net_usd=paid-spent,
                box_fair_expected_wins=expected,
                box_fair_at_least_one_prob=sum(unique.values())/10**len(winners))
