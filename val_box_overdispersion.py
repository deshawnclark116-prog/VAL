"""Research-only exchangeable Dirichlet-multinomial complete-Box challenger.

Unlike iid digit products, this allows within-draw repetition dependence.
Concentration is fixed *before* testing, not optimized on target outcomes.
No synthetic success constitutes evidence of a real Virginia lottery edge.
"""
from collections import Counter
from itertools import combinations_with_replacement
from math import exp, lgamma, log, factorial
from val_box import any_order_prize, box_ways

VERSION = "box_dirichlet_multinomial_v1"

def box_probability(combo, digit_probs, concentration):
    """Exact probability of the unordered complete multiset under DM."""
    if concentration <= 0 or len(digit_probs) != 10 or any(p <= 0 for p in digit_probs):
        raise ValueError("Invalid positive Dirichlet parameters")
    if abs(sum(digit_probs)-1) > 1e-9:
        raise ValueError("Digit probabilities must sum to one")
    n=len(combo)
    if n not in (3,4,5) or any(type(d) is not int or d<0 or d>9 for d in combo):
        raise ValueError("Invalid complete digit combination")
    counts=Counter(combo)
    logp=lgamma(concentration)-lgamma(concentration+n)+log(box_ways(combo))
    for d,k in counts.items():
        logp += lgamma(concentration*digit_probs[d]+k)-lgamma(concentration*digit_probs[d])
    return exp(logp)

def ranked_boxes(game, digit_probs, concentration, count=3):
    if game not in ("pick3","pick4","pick5") or not 1 <= count <= 5:
        raise ValueError("Invalid game/count")
    width=int(game[-1])
    ranked=[(box_probability(combo,digit_probs,concentration),combo)
            for combo in combinations_with_replacement(range(10),width)
            if any_order_prize(game,combo)]
    ranked.sort(key=lambda item:(-item[0],item[1]))
    return [dict(numbers=list(combo),box_probability=p,formula_version=VERSION,
                 concentration=concentration,play_type="any_order")
            for p,combo in ranked[:count]]

def distribution_log_gain(actual, digit_probs, concentration):
    """Proper ordered-outcome score against fair iid, not Box win counting."""
    from math import log
    combo=tuple(actual)
    return log(box_probability(combo,digit_probs,concentration) /
               box_ways(combo)) + len(combo)*log(10)

def posterior_digit_probs(previous, width, pseudocount=100):
    """Strictly prior draws; strong shrinkage prevents noisy hot-digit fits."""
    counts=[0]*10
    for row in previous:
        digits=row["numbers"]
        if len(digits)!=width or any(type(d) is not int or not 0<=d<=9 for d in digits):
            raise ValueError("Invalid earlier draw")
        for d in digits:counts[d]+=1
    total=sum(counts)+10*pseudocount
    return tuple((v+pseudocount)/total for v in counts)
