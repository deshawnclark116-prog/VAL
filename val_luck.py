"""Plain-language "luck check" for the prospective Pick 3/4/5 scoreboard.

For each formula version it answers three questions about the ORIGINAL first
saved ticket of every settled batch (alternatives never count):

1. How many complete Any Order (Box) wins would a fair pick expect by now?
2. How likely is it to get at least this many wins by pure luck?  The chance
   is adjusted for the number of formulas being watched at once (Bonferroni),
   because watching many formulas makes one lucky-looking streak likely.
3. Roughly how many settled picks are needed before the scoreboard could
   tell a formula that truly doubles the fair win rate apart from luck
   (one-sided 5% test, 80% power, normal approximation to a Poisson count)?

Counting starts at the first saved batch of each formula ("tracking since"),
so wins can never be credited to a formula retroactively.
"""
from __future__ import annotations

import math
from datetime import datetime

from val import ET
from val_box import fair_any_order_probability, is_any_order_win

DIGIT_GAMES = ("pick3", "pick4", "pick5")
# ((z_alpha + z_beta * sqrt(2)) ** 2) for a one-sided 5% test with 80% power
# against a doubled win rate: n ~= DOUBLING_CONSTANT / fair_probability.
DOUBLING_CONSTANT = (1.6449 + 0.8416 * math.sqrt(2)) ** 2
SIGNIFICANCE = 0.05


def chance_at_least(probabilities, wins):
    """Exact P(at least `wins` successes) for independent tickets (Poisson-binomial)."""
    if wins <= 0:
        return 1.0
    dist = [1.0]
    for p in probabilities:
        nxt = [0.0] * (len(dist) + 1)
        for k, mass in enumerate(dist):
            nxt[k] += mass * (1 - p)
            nxt[k + 1] += mass * p
        dist = nxt
    return min(1.0, max(0.0, sum(dist[wins:])))


def picks_needed(mean_probability):
    """Settled picks needed to reliably tell a doubled win rate from luck."""
    if mean_probability <= 0:
        return None
    return math.ceil(DOUBLING_CONSTANT / mean_probability)


def one_in(chance):
    """Readable odds, e.g. 0.002 -> 'about 1 in 500'."""
    if chance >= 0.5:
        return "very likely"
    n = 1 / chance if chance > 0 else float("inf")
    if n == float("inf") or n >= 1e7:
        return "less than 1 in 10 million"
    digits = max(0, len(str(int(n))) - 2)
    rounded = int(round(n, -digits))
    return f"about 1 in {rounded:,}"


def verdict(row):
    if row["wins"] == 0:
        return f"No wins yet. Normal: random picks would expect only {row['fair_expected']:.3f} wins by now."
    if row["all_fallback"]:
        return "Luck by design: these were random fallback picks, not formula predictions."
    if row["adjusted_chance"] >= SIGNIFICANCE:
        return "Looks like ordinary luck."
    if row["needed"] and row["settled"] < row["needed"]:
        return "Unusual, but far too few picks to tell. Keep watching."
    return "Unusual over enough picks. Worth a closer look, but still not proof."


def luck_check(records):
    """Rows per (game, formula version) for settled Pick 3/4/5 batches."""
    grouped = {}
    for entry in records:
        game = entry.get("game")
        if game not in DIGIT_GAMES or entry.get("result") is None:
            continue
        if not entry.get("picks") or not entry.get("baseline"):
            continue
        meta = entry.get("model_meta") or {}
        version = meta.get("formula_version") or entry.get("method") or "unknown"
        item = grouped.setdefault((game, version), dict(
            game=game, version=version, since=None, settled=0, wins=0,
            control_wins=0, probabilities=[], all_fallback=True))
        draw = entry["result"]["draw"]["numbers"]
        pick = entry["picks"][0]["numbers"]
        control = entry["baseline"][0]["numbers"]
        item["settled"] += 1
        item["probabilities"].append(fair_any_order_probability(game, pick))
        item["wins"] += is_any_order_win(game, pick, draw)
        item["control_wins"] += is_any_order_win(game, control, draw)
        if meta.get("signal_gate_passed") is not False:
            item["all_fallback"] = False
        created = entry.get("created")
        if created and (item["since"] is None or created < item["since"]):
            item["since"] = created
    rows = [grouped[k] for k in sorted(grouped)]
    watched = max(1, len(rows))
    for row in rows:
        probs = row.pop("probabilities")
        row["fair_expected"] = sum(probs)
        row["luck_chance"] = chance_at_least(probs, row["wins"])
        row["adjusted_chance"] = min(1.0, row["luck_chance"] * watched)
        row["needed"] = picks_needed(sum(probs) / len(probs))
        row["formulas_watched"] = watched
        row["verdict"] = verdict(row)
    return rows


def luck_report(rows, game_names, labels=None):
    """Markdown section for latest.md."""
    watched = rows[0]["formulas_watched"] if rows else 0
    lines = [
        "## Luck check — is anything beating random?", "",
        "In plain terms: lottery wins happen by luck all the time. This table asks, for each formula, "
        "*how surprising would these wins be if the picks were completely random?* "
        f"Because {watched} formula/game combinations are being watched at once, the luck chance is "
        "adjusted upward: when you watch many, one is bound to look lucky. "
        "Counting starts the day each formula's first pick was saved, so old wins are never credited "
        "to a newer formula. Only the original first ticket of each batch counts.", "",
        "\"Picks needed\" is roughly how many settled picks it takes before a formula that truly "
        "doubled the fair win rate could be told apart from luck. Until a formula reaches that number, "
        "a few wins mean very little.", "",
        "| Game | Formula | Tracking since (ET) | Settled picks | Wins | Random-pick wins | "
        "Fair expected wins | Chance by luck (adjusted) | Picks needed | Verdict |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        since = (datetime.fromisoformat(row["since"]).astimezone(ET).date().isoformat()
                 if row["since"] else "—")
        name = (labels or {}).get(row["version"]) or f"`{row['version']}`"
        needed = f"{row['needed']:,}" if row["needed"] else "—"
        chance = "—" if row["wins"] == 0 else one_in(row["adjusted_chance"])
        lines.append(
            f"| {game_names[row['game']]} | {name} | {since} | {row['settled']} | "
            f"{row['wins']} | {row['control_wins']} | {row['fair_expected']:.3f} | {chance} | "
            f"{needed} | {row['verdict']} |")
    if not rows:
        lines.append("| — | — | — | 0 | 0 | 0 | 0 | — | — | No settled picks yet. |")
    return lines
