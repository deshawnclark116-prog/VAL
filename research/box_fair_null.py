"""Exact fair-null probabilities for full Any Order (Box) outcomes.

Research-only: no changes to deployed digit_box_v4 or frozen ledgers.
"""
from collections import Counter
from itertools import combinations_with_replacement
from math import factorial, prod


def canonical_box(digits, length):
    """A complete multiset, retaining repeated digits and leading zeros."""
    s = str(digits)
    if len(s) != length or any(ch not in "0123456789" for ch in s):
        raise ValueError("Expected exactly length decimal digits")
    return "".join(sorted(s))


def fair_box_probability(box):
    """Probability of a complete Any Order hit under iid uniform digits."""
    length = len(box)
    if length not in (3, 4, 5) or any(c not in "0123456789" for c in box):
        raise ValueError("Pick 3/4/5 decimal box required")
    counts = Counter(box)
    return factorial(length) / prod(factorial(n) for n in counts.values()) / (10 ** length)


def portfolio_fair_probability(tickets, length):
    """Exact one-draw probability of at least one Box hit; deduplicates tickets."""
    boxes = {canonical_box(ticket, length) for ticket in tickets}
    return sum(fair_box_probability(box) for box in boxes)


def fair_box_distribution(length):
    """Complete fair distribution, INCLUDING all-identical outcomes."""
    if length not in (3, 4, 5):
        raise ValueError("Only Pick 3/4/5 supported")
    return {
        "".join(t): fair_box_probability("".join(t))
        for t in combinations_with_replacement("0123456789", length)
    }
