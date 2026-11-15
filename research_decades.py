"""Decades-long Virginia Lottery audit from the official raw download archives.

Research only; deliberately bypasses VAL's production 2025 cutoff without
changing its real-world generator, scheduled workflow, or prediction ledger.

Tests descriptive departures from an iid uniform digit draw and evaluates
pre-specified walk-forward probabilistic forecasts. No retrospective picking
of lucky tickets is described as predictive evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

GAMES = {"pick3": (1050, 3), "pick4": (1040, 4), "pick5": (1035, 5)}
START_PERIODS = ("1989-01-01", "2010-01-01", "2020-01-01", "2025-01-01")
MIN_ROWS = {"pick3": 17000, "pick4": 15000, "pick5": 2000}
KNOWN_HEADER = {"Results for Pick 3", "Results for Pick 4", "Results for Pick 5"}
FOOTERS = {"All information is entered manually, and is subject to human error.",
           "Therefore, we can not guarantee the accuracy of this information."}


def parse_complete_archive(game, content):
    """Fail closed: every source row must be interpreted, with zero-padding kept."""
    if game not in GAMES: raise ValueError(game)
    width = GAMES[game][1]
    rows, seen = [], set()
    for lineno, raw in enumerate(content.splitlines(), 1):
        line = raw.strip()
        if not line or line in KNOWN_HEADER or line in FOOTERS: continue
        pieces = [v.strip() for v in line.split(";")]
        try:
            draw_date = datetime.strptime(pieces[0], "%m/%d/%Y").date()
        except (ValueError, IndexError) as exc:
            raise ValueError(f"{game} line {lineno} unknown header: {line[:100]}") from exc
        if draw_date > datetime.now(timezone.utc).date():
            raise ValueError(f"Future official draw in {game}: {draw_date}")
        i, found = 1, 0
        while i < len(pieces):
            match = re.fullmatch(r"(Day|Night):\s*(\d(?:,\d){"+str(width-1)+r"})", pieces[i])
            if not match:
                raise ValueError(f"{game} line {lineno} unexpected field: {pieces[i]!r}")
            stream = match.group(1)
            digits = [int(s) for s in match.group(2).split(",")]
            i += 1
            fireball = None
            if i < len(pieces) and pieces[i].startswith("Fireball:"):
                fm = re.fullmatch(r"Fireball:\s*(\d)", pieces[i])
                if not fm: raise ValueError(f"{game} line {lineno} invalid Fireball")
                fireball = int(fm.group(1))
                i += 1
            key = (draw_date.isoformat(), stream)
            if key in seen: raise ValueError(f"Duplicate official draw: {game} {key}")
            seen.add(key)
            rows.append({"date": draw_date.isoformat(), "stream": stream,
                         "numbers": digits, "fireball": fireball})
            found += 1
        if found == 0: raise ValueError(f"{game} line {lineno} contains no draw")
    rows.sort(key=lambda r: (r["date"], r["stream"] == "Night"))
    if len(rows) < MIN_ROWS[game]:
        raise ValueError(f"{game} unexpectedly short official history: {len(rows)}")
    return rows


def fetch_full(game):
    url = f"https://www.valottery.com/api/v1/downloadall?gameId={GAMES[game][0]}"
    req = urllib.request.Request(url, headers={"User-Agent": "VAL-decades-audit/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read(15_000_000)
    content = raw.decode("utf-8-sig")
    return parse_complete_archive(game, content), {
        "url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()
    }


def gammaincc(a, x):
    """Regularized upper incomplete gamma; Numerical Recipes series/CF."""
    if x < 0 or a <= 0: raise ValueError((a, x))
    if x == 0: return 1.0
    pref = math.exp(a * math.log(x) - x - math.lgamma(a))
    if x < a + 1:
        term = 1 / a
        summation = term
        for k in range(1, 2000):
            term *= x / (a + k)
            summation += term
            if abs(term) < abs(summation) * 1e-13: break
        return max(0.0, min(1.0, 1.0 - summation * pref))
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / max(abs(b), tiny) * (1 if b >= 0 else -1)
    h = d
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny: d = tiny
        c = b + an / c
        if abs(c) < tiny: c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-13: break
    return max(0.0, min(1.0, h * pref))


def chi_uniform(counts):
    n = sum(counts)
    if n < 100: return None
    expected = n / len(counts)
    chi = sum((x - expected) ** 2 / expected for x in counts)
    return {"n": n, "chi_square": round(chi, 5),
            "p": gammaincc((len(counts)-1)/2, chi/2),
            "counts": counts}


def same_digit_binomial(observed, trials, probability):
    if trials < 100 or not 0 < probability < 1: return None
    mu = trials * probability
    sigma = math.sqrt(trials * probability * (1 - probability))
    z = (observed - mu) / sigma
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"observed": observed, "trials": trials, "expected": round(mu, 3),
            "z": round(z, 5), "p": p}


def unequal_streams(rows, width):
    """Two-sample 2x10 chi-square, no assumption of equal sample counts."""
    day = [r for r in rows if r["stream"] == "Day"]
    night = [r for r in rows if r["stream"] == "Night"]
    if min(len(day), len(night)) < 100: return []
    comparisons = []
    for position in range(width):
        a = Counter(r["numbers"][position] for r in day)
        b = Counter(r["numbers"][position] for r in night)
        chi = 0.0
        for d in range(10):
            total = a[d] + b[d]
            if not total: continue
            expected_a = total * len(day) / (len(day)+len(night))
            expected_b = total - expected_a
            chi += (a[d] - expected_a)**2 / expected_a
            chi += (b[d] - expected_b)**2 / expected_b
        comparisons.append({
            "position": position + 1, "day_n": len(day), "night_n": len(night),
            "chi_square": round(chi, 5), "p": gammaincc(9 / 2, chi / 2)
        })
    return comparisons


def groups(game, rows):
    start = {"pick3": "1989-01-01", "pick4": "1991-01-01", "pick5": "2023-01-01"}[game]
    sets = {"all_available": rows,
            "before_2010": [x for x in rows if x["date"] < "2010-01-01"],
            "2010_to_2019": [x for x in rows if "2010-01-01" <= x["date"] < "2020-01-01"],
            "2020_to_2024": [x for x in rows if "2020-01-01" <= x["date"] < "2025-01-01"],
            "2025_onward": [x for x in rows if x["date"] >= "2025-01-01"]}
    return {k: v for k, v in sets.items() if len(v) >= 100}


def research_tests(game, rows):
    width = GAMES[game][1]
    out, hypotheses = {}, []
    for label, subset in groups(game, rows).items():
        n = len(subset)
        positions = []
        for pos in range(width):
            test = chi_uniform([sum(r["numbers"][pos] == d for r in subset) for d in range(10)])
            positions.append(test)
            hypotheses.append({"game":game,"period":label,"test":f"position_{pos+1}_uniform",**test})
        pooled = chi_uniform([sum(r["numbers"].count(d) for r in subset) for d in range(10)])
        hypotheses.append({"game":game,"period":label,"test":"pooled_digit_uniform",**pooled})
        streams = unequal_streams(subset, width)
        for s in streams:
            hypotheses.append({"game":game,"period":label,"test":f"day_night_position_{s['position']}",**s})
        transitions = width * (n - 1)
        repeats = sum(a == b for before, after in zip(subset, subset[1:])
                      for a, b in zip(before["numbers"], after["numbers"]))
        repeat_test = same_digit_binomial(repeats, transitions, 0.1)
        hypotheses.append({"game":game,"period":label,"test":"next_draw_same_position_repeat",
                           **repeat_test})
        unique = sum(len(set(r["numbers"])) == width for r in subset)
        unique_probability = math.prod((10-i)/10 for i in range(width))
        unique_test = same_digit_binomial(unique, n, unique_probability)
        hypotheses.append({"game":game,"period":label,"test":"all_unique_digit_count",
                           **unique_test})
        same_combination = sum(a["numbers"] == b["numbers"] for a,b in zip(subset, subset[1:]))
        combo_test = same_digit_binomial(same_combination, n-1, 10 ** (-width))
        hypotheses.append({"game":game,"period":label,"test":"consecutive_exact_duplicate",
                           **combo_test})
        fireballs = [r["fireball"] for r in subset if r["fireball"] is not None]
        fireball_test = chi_uniform([fireballs.count(d) for d in range(10)]) if len(fireballs)>=100 else None
        if fireball_test:
            hypotheses.append({"game":game,"period":label,"test":"fireball_uniform",**fireball_test})
        out[label] = {
            "draws": n,
            "first": subset[0]["date"], "last": subset[-1]["date"],
            "digit_positions": positions, "all_digits": pooled,
            "day_night_comparison": streams,
            "consecutive_same_position": repeat_test,
            "all_unique_digits": unique_test,
            "consecutive_exact_duplicate": combo_test,
            "fireball": fireball_test,
        }
    return out, hypotheses


def prospective_log_scores(game, history):
    """Strict walk-forward probabilities from already-defined models.

    100/500 previous draws and same-session previous 500, Laplace +2/digit.
    Scores are per REAL next draw, not per sampled lottery ticket.
    """
    width = GAMES[game][1]
    methods = ("last_100", "last_500", "last_500_same_session")
    stats = {k: defaultdict(list) for k in methods}
    for i in range(500, len(history)):
        target = history[i]
        for key in methods:
            prior = history[max(0,i-(100 if key=="last_100" else 500)):i]
            if key.endswith("same_session"):
                prior = [r for r in prior if r["stream"] == target["stream"]]
            if len(prior) < 25: continue
            score = 0.0
            for pos, digit in enumerate(target["numbers"]):
                observed = sum(r["numbers"][pos] == digit for r in prior)
                p = (observed + 2) / (len(prior) + 20)
                score += math.log(p * 10)
            year = int(target["date"][:4])
            era = ("before_2010" if year < 2010 else
                   "2010_to_2019" if year < 2020 else
                   "2020_to_2024" if year < 2025 else "2025_onward")
            stats[key]["full"].append(score)
            stats[key][era].append(score)
    result={}
    for name, eras in stats.items():
        result[name]={}
        for era, values in eras.items():
            if len(values) < 30:continue
            mean = statistics.mean(values)
            se = statistics.stdev(values) / math.sqrt(len(values))
            z = mean / se if se else 0.0
            result[name][era] = {"draws":len(values),
                                 "mean_log_score_advantage_per_draw":round(mean, 8),
                                 "confidence_interval_95": [round(mean-1.96*se,8),
                                                            round(mean+1.96*se,8)],
                                 "z":round(z,5),
                                 "two_sided_p":math.erfc(abs(z)/math.sqrt(2))}
    return result


def bonferroni(hypotheses):
    m = len(hypotheses)
    for h in hypotheses:
        h["adjusted_p_bonferroni"] = min(1, h["p"]*m)
        h["passes_fwer_0_05"] = h["adjusted_p_bonferroni"] < 0.05
    return sorted(hypotheses, key=lambda h: h["p"])


def summary_md(result):
    lines = [
        "# VAL full-history randomness and prediction audit",
        "",
        f"Generated (UTC): {result['generated_at']}",
        "",
        "**Important:** This expands the *research* archives only. VAL's live",
        "April 2025 historical cutoff, generated tickets, and prediction ledger",
        "were not changed. All official downloads may contain manually entered errors.",
        "",
        "## Archive coverage",
        "",
        "| Game | First available draw | Latest draw | Drawings | Year range | Days | Nights | FIREBALL-bearing |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for game, g in result["games"].items():
        x=g["coverage"]
        lines.append(f"| {game} | {x['first_date']} | {x['last_date']} | "
                     f"{x['draws']:,} | {x['first_year']}–{x['last_year']} | "
                     f"{x['streams'].get('Day',0):,} | {x['streams'].get('Night',0):,} | "
                     f"{x['fireball_draws']:,} |")
    lines.extend([
        "",
        "## Broad historical tests",
        "",
        f"Total prespecified comparisons: **{result['hypothesis_count']}**."
        " These are exploratory on historic data; family-wise Bonferroni",
        " correction controls for simultaneously searching many apparent patterns.",
        "",
        f"Raw p-values under 0.05: **{result['raw_small_p_count']}**."
        f" Family-wise-adjusted p-values under 0.05: **{result['adjusted_significant_count']}**.",
        "",
        "| Game | Period | Pattern checked | Raw p | Adjusted p |",
        "| --- | --- | --- | ---: | ---: |",
    ])
    for h in result["most_unusual_tests"][:20]:
        lines.append(f"| {h['game']} | {h['period']} | {h['test']} | "
                     f"{h['p']:.6g} | {h['adjusted_p_bonferroni']:.6g} |")
    lines += ["",
              "**Caution:** Even an adjusted finding is only a historical anomaly.",
              "It must recur in a separate, future period before it could justify",
              "any predictive claims. Draw equipment, ball sets, and operating",
              "procedures are not identified in this numerical archive.",
              "",
              "## Walk-forward probability forecasting (past years to later years)",
              "",
              "A perfect fair-draw model gives each digit probability 10%; its",
              "mean log-score *advantage* is exactly zero. Positive scores favor",
              "a history-based model; negative scores favor fair uniform.",
              "Forecasts were computed **only from earlier draws**.",
              "",
              "| Game | Model | Period | Real next draws | Log-score advantage per draw | 95% interval |",
              "| --- | --- | --- | ---: | ---: | --- |",
             ]
    for game,g in result["games"].items():
        for method, eras in g["walk_forward_log_scores"].items():
            for era, data in eras.items():
                if era not in ("full","2020_to_2024","2025_onward"):continue
                lo,hi=data["confidence_interval_95"]
                lines.append(f"| {game} | {method} | {era} | {data['draws']:,} | "
                             f"{data['mean_log_score_advantage_per_draw']:+.6f} | "
                             f"[{lo:+.6f}, {hi:+.6f}] |")
    lines.extend([
        "",
        "## Methodology and important limitations",
        "",
        "- Source is the Virginia Lottery's actual Download All for each game,",
        "  independently parsed without the April 2025 production cutoff.",
        "- Earlier years include only Night draws before Day drawings began.",
        "- FIREBALL is absent in older records and is never assumed to be zero.",
        "- Only pre-registered descriptive checks and three fixed rolling",
        "  forecast baselines are in this audit; no pattern-mining after a win.",
        "- Apparent number biases can be the result of chance or reporting errors.",
        "- The historical number archive lacks machine/ball-set identifiers,",
        "  so it cannot identify an equipment-specific mechanism or bias.",
        "- Stronger evidence would require disjoint prospective confirmation",
        "  plus machine/ball-set metadata, not merely more retrospective tuning.",
        "- All methods here are **research**, not documented financial advantage.",
        "",
        "Raw per-year coverage and all statistical comparisons:",
        "[research_decades.json](research_decades.json).",
        "",
    ])
    return "\n".join(lines)


def research():
    result = {"generated_at":datetime.now(timezone.utc).isoformat(),
              "version":"val_decades_randomness_audit_v1",
              "hypotheses":"Predefined digit uniformity, day/night, repeats, duplicate, FIREBALL",
              "games":{}}
    hypotheses=[]
    for game in GAMES:
        rows, source=fetch_full(game)
        counts=Counter(r["date"][:4] for r in rows)
        streams=Counter(r["stream"] for r in rows)
        summaries, hyp=research_tests(game,rows)
        hypotheses.extend(hyp)
        coverage={
            "draws":len(rows), "first_date":rows[0]["date"], "last_date":rows[-1]["date"],
            "first_year":min(counts), "last_year":max(counts), "per_year":dict(sorted(counts.items())),
            "streams":dict(streams),
            "fireball_draws":sum(r["fireball"] is not None for r in rows),
            "first_fireball_date": next((r["date"] for r in rows if r["fireball"] is not None), None),
            "source":source
        }
        forecasts=prospective_log_scores(game,rows)
        result["games"][game]={"coverage":coverage,"period_tests":summaries,
                               "walk_forward_log_scores":forecasts}
        print(json.dumps({"game":game,"draws":len(rows),"earliest":rows[0]["date"],
                          "latest":rows[-1]["date"],"forecast_full":
                          {k:v.get("full",{}).get("mean_log_score_advantage_per_draw") for k,v in forecasts.items()}}),
              flush=True)
    hypotheses=bonferroni(hypotheses)
    result["hypothesis_count"]=len(hypotheses)
    result["raw_small_p_count"]=sum(h["p"] < .05 for h in hypotheses)
    result["adjusted_significant_count"]=sum(h["passes_fwer_0_05"] for h in hypotheses)
    result["most_unusual_tests"]=hypotheses[:50]
    result["all_hypotheses"]=hypotheses
    out=Path("reports/research_decades.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    Path("reports/research_decades.md").write_text(summary_md(result)+"\n")
    print(json.dumps({"comparisons":len(hypotheses),
                      "significant_after_adjustment":result["adjusted_significant_count"],
                      "top":hypotheses[:3]}),flush=True)
    return result


if __name__ == "__main__":
    research()
