"""Popular player "adding" methods for Pick 3/4/5, tracked as paper experiments.

These are well-known player systems, NOT models with any demonstrated edge.
They are recorded so the luck check can score them honestly against random
picks on every future drawing. Each method uses only completed past results.

For a k-digit game the "tic-tac-toe" grid stacks the last k winning numbers
(oldest on top, newest at the bottom), giving a k-by-k grid. "Keep the last
digit" means adding the digits and keeping the ones place (17 -> 7).
"""
from __future__ import annotations

from val_box import box_ways

PREFIX = "player_"
METHODS = {
    "player_ttt_columns": "Tic-tac-toe: add each column",
    "player_ttt_rows": "Tic-tac-toe: add each row",
    "player_ttt_diagonals": "Tic-tac-toe: add each diagonal",
    "player_add_last_two": "Add the last two results",
    "player_mirror": "Mirror the last result (add 5)",
}


def grid(history, width):
    if len(history) < width:
        raise ValueError(f"Need at least {width} completed results")
    return [list(r["numbers"]) for r in history[-width:]]


def player_pick(method, history, width):
    """Digits produced by one player method from past completed results."""
    g = grid(history, width)
    k = width
    if method == "player_ttt_columns":
        digits = [sum(g[r][c] for r in range(k)) % 10 for c in range(k)]
    elif method == "player_ttt_rows":
        digits = [sum(g[r]) % 10 for r in range(k)]
    elif method == "player_ttt_diagonals":
        # k wrapped diagonals: start at top-row column c and step down-right.
        digits = [sum(g[r][(c + r) % k] for r in range(k)) % 10 for c in range(k)]
    elif method == "player_add_last_two":
        digits = [(a + b) % 10 for a, b in zip(g[-2], g[-1])]
    elif method == "player_mirror":
        digits = [(d + 5) % 10 for d in g[-1]]
    else:
        raise ValueError("Unknown player method")
    return dict(numbers=digits, bonus=None, play_type="any_order",
                box_ways=box_ways(digits), rank=1, role="primary")


def is_player_method(entry):
    return str(entry.get("method", "")).startswith(PREFIX)
