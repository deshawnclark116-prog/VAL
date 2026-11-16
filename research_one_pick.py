"""VAL one-ticket walk-forward research across all available digit draw history.

Each method submits exactly ONE prediction per real held-out drawing.
Research only: no changes to VAL live picks, scheduled jobs, or ledger.

Scientific cautions:
- No draws after the target are consulted.
- Historical windows and model families are tested in parallel, and ALL are
  reported. Comparing many methods on seen years is exploratory.
- Uniform fair outcomes are the null. Every full ordered combination has equal
  chance; any-order coverage varies mechanically with repeated digits.
- A future unseen period is needed before promoting any challenger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_decades import GAMES, fetch_full
from research_10k import labels, fair_box_probability

WINDOWS = (30, 100, 500, 1000, 5000)
FAMILIES = ("position_hot", "position_cold", "pooled_hot", "session_hier")
POLICIES = ("top", "sample")
BASELINES = ("random", "random_distinct")
SEED = 20261115


def stable_rng(*strings):
    digest = hashlib.sha256(":".join(map(str, strings)).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def probs(weights):
    total = sum(weights)
    if total <= 0: raise AssertionError("Probability weights sum to zero")
    return [x / total for x in weights]


def fair_box_probability_digits(digits):
    count = math.factorial(len(digits))
    for n in Counter(digits).values():
        count //= math.factorial(n)
    return count / 10**len(digits)


def build_probabilities(family, matrix, global_counts, sessions, session, width,
                        count, stream_n):
    """Fixed hyperparameters, strong regularization toward fair probabilities."""
    if family not in FAMILIES: raise ValueError(family)
    out = []
    for pos in range(width):
        row = matrix[pos]
        if family == "position_hot":
            # Dirichlet prior 20 pseudo-draws per digit (200 total).
            distribution = probs([20 + row[d] for d in range(10)])
        elif family == "position_cold":
            # Anti-frequency. Weights deliberately only weakly different from fair.
            distribution = probs([1 / math.sqrt(20 + row[d]) for d in range(10)])
        elif family == "pooled_hot":
            # Pool all digit positions, with prior scaled by game width.
            distribution = probs([20 * width + global_counts[d] for d in range(10)])
        elif family == "session_hier":
            # Weak shrinkage of session-specific observations to pooled position
            # history; all units are positional digit counts.
            general = probs([20 + row[d] for d in range(10)])
            by_stream = sessions[session][pos]
            distribution = probs([40 * general[d] + by_stream[d] for d in range(10)])
        else:
            raise AssertionError(family)
        if min(distribution) <= 0 or abs(sum(distribution) - 1) > 1e-10:
            raise AssertionError("Non-normalized distribution")
        out.append(distribution)
    return out


class Rolling:
    def __init__(self, rows, width, size):
        self.width, self.size = width, size
        self.position = [[0] * 10 for _ in range(width)]
        self.global_counts = [0] * 10
        self.sessions = {
            "Day": [[0] * 10 for _ in range(width)],
            "Night": [[0] * 10 for _ in range(width)]
        }
        self.stream_count = {"Day": 0, "Night": 0}
        self.n = 0
        for row in rows[-size:]:
            self.add(row)

    def change(self, row, sign):
        self.n += sign
        self.stream_count[row["stream"]] += sign
        for i, digit in enumerate(row["numbers"]):
            self.position[i][digit] += sign
            self.global_counts[digit] += sign
            self.sessions[row["stream"]][i][digit] += sign
            if self.position[i][digit] < 0: raise AssertionError("Negative count")

    def add(self, row): self.change(row, 1)
    def remove(self, row): self.change(row, -1)

    def probabilities(self, family, session):
        return build_probabilities(
            family, self.position, self.global_counts, self.sessions, session,
            self.width, self.n, self.stream_count[session])


def choose_one(matrix, policy, rng):
    if policy == "sample":
        return [rng.choices(range(10), weights=p, k=1)[0] for p in matrix]
    if policy == "top":
        # Randomize ties using an independent, frozen seed (not target data).
        results = []
        for p in matrix:
            best = max(p)
            tied = [i for i, x in enumerate(p) if abs(x-best) < 1e-14]
            results.append(rng.choice(tied))
        return results
    raise ValueError(policy)


def target_period(day):
    if day < "2000-01-01": return "before_2000"
    if day < "2010-01-01": return "2000s"
    if day < "2020-01-01": return "2010s"
    if day < "2025-01-01": return "2020_to_2024"
    return "2025_onward"


def summarize_counts(row):
    n = row["n"]
    if not n: return None
    log_mean = row["log_gain_sum"] / n
    mean_squared = row["log_gain_sq_sum"] / n
    # Standard error of the draw-level average; no independent-ticket assumption.
    se = math.sqrt(max(0, mean_squared - log_mean**2)/(n-1)) if n > 1 else 0.0
    return {
        "draws_and_tickets":n,
        "straight":row["straight"],
        "any_order_including_straight":row["box"],
        "box_only":row["box"]-row["straight"],
        "fireball_any_order":row["firebox"],
        "expected_straight_if_fair":round(n / 10**row["width"],5),
        "expected_any_order_if_fair":round(row["box_expected"],4),
        "any_order_excess_over_fair_expected":round(row["box"]-row["box_expected"],4),
        "log_score_advantage_vs_fair_per_draw":round(log_mean,8),
        "approx_95pct_log_advantage_interval":[round(log_mean-1.96*se,8),round(log_mean+1.96*se,8)],
    }


def empty_counter(width):
    return {"width":width,"n":0,"straight":0,"box":0,"firebox":0,
            "box_expected":0.0,"log_gain_sum":0.0,"log_gain_sq_sum":0.0}


def add_grade(row, target, digits, log_gain):
    numbers = target["numbers"]
    if len(digits)!=len(numbers):raise AssertionError("Wrong width")
    straight = int(digits == numbers)
    any_order = int(sorted(digits)==sorted(numbers))
    firebox = 0
    fire = target["fireball"]
    if fire is not None:
        for i in range(len(numbers)):
            substituted = list(numbers)
            substituted[i] = fire
            firebox |= int(sorted(substituted) == sorted(digits))
    row["n"] += 1
    row["straight"] += straight
    row["box"] += any_order
    row["firebox"] += firebox
    row["box_expected"] += fair_box_probability_digits(digits)
    row["log_gain_sum"] += log_gain
    row["log_gain_sq_sum"] += log_gain*log_gain


def evaluate(game, history, windows=WINDOWS, seed=SEED, years=True):
    if game not in GAMES:raise ValueError(game)
    width=GAMES[game][1]
    windows=tuple(sorted(set(windows)))
    if min(windows)<20 or len(history) <= min(windows):raise ValueError("Not enough history")
    eligible_windows=[w for w in windows if len(history)>w]
    # Same eligible target drawings for ALL model/window candidates *within game*.
    common_start=max(eligible_windows)
    rolling={w:Rolling(history[:common_start][-w:],width,w) for w in eligible_windows}
    names=["random","random_distinct"]+[f"{f}_{p}_{w}" for w in eligible_windows for f in FAMILIES for p in POLICIES]
    rng={name:stable_rng(seed,game,name) for name in names}
    counts={name:empty_counter(width) for name in names}
    segmented={name:{} for name in names}
    annual={name:{} for name in names}
    position_cumulative_stats={}

    for i in range(common_start,len(history)):
        actual=history[i]
        period=target_period(actual["date"])
        yr=actual["date"][:4]
        # Evaluate exact ONE play for every fixed method per actual drawing.
        predictions={
            "random":[rng["random"].randrange(10) for _ in range(width)],
            "random_distinct":rng["random_distinct"].sample(range(10),width),
        }
        model_scores={"random":0.0,"random_distinct":0.0}
        for w, tracker in rolling.items():
            if tracker.n != w:raise AssertionError("Rolling-window training size drift")
            for family in FAMILIES:
                p=tracker.probabilities(family,actual["stream"])
                # Forecast scoring on true outcome, before any target information.
                advantage=sum(math.log(p[j][d]*10) for j,d in enumerate(actual["numbers"]))
                for policy in POLICIES:
                    name=f"{family}_{policy}_{w}"
                    predictions[name]=choose_one(p,policy,rng[name])
                    model_scores[name]=advantage

        for name,digits in predictions.items():
            add_grade(counts[name],actual,digits,model_scores[name])
            if period not in segmented[name]:segmented[name][period]=empty_counter(width)
            if yr not in annual[name]:annual[name][yr]=empty_counter(width)
            add_grade(segmented[name][period],actual,digits,model_scores[name])
            add_grade(annual[name][yr],actual,digits,model_scores[name])

        # NO leakage: only now is official drawn outcome permitted into windows.
        for w,tracker in rolling.items():
            tracker.add(actual)
            tracker.remove(history[i-w])
    out={}
    for name in names:
        out[name]={
            "all":summarize_counts(counts[name]),
            "by_period":{p:summarize_counts(r) for p,r in segmented[name].items()},
            "by_year":{yr:summarize_counts(r) for yr,r in annual[name].items()},
        }
    return {
        "game":game,"archive_draws":len(history),
        "walk_forward_draws":len(history)-common_start,
        "first_test_date":history[common_start]["date"],
        "last_test_date":history[-1]["date"],
        "history_windows_draws":list(eligible_windows),
        "first_test_min_training_draws":common_start,
        "models":out,
    }


def markdown(report):
    lines=[
        "# VAL: one prediction per drawing, historical walk-forward research",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "**Research only. No winning advantage has been demonstrated.**",
        "Every method generates **one** digit combination for every real future",
        "historical drawing on the same eligibility dates, with only strictly",
        "earlier results used in training. No live VAL picks have changed.",
        "",
        "Compared history windows: 30, 100, 500, 1,000, 5,000 prior draws",
        "(5,000 unavailable for Pick 5, whose archive is shorter).",
        "Methods: positional hot/cold, pooled hot, Day-versus-Night",
        "hierarchical frequencies. Each uses a single *top-scoring* ticket",
        "or a single random sample from the same probability model.",
        "Controls: unrestricted uniform random and random all-distinct digits.",
        "",
        "**Important Any Order distinction:** The all-distinct baseline covers",
        "more orderings than tickets with repeated digits. Its higher chance",
        "of an Any Order match is mathematical coverage, NOT prediction.",
        "Every method is compared with the expected number of Any Order hits",
        "for the exact digit compositions it actually chose.",
        "",
        "Straight counts exact order. Any Order includes Straight. FIREBALL",
        "Any Order is separate, and only applies after FIREBALL was introduced.",
        "Methods were chosen after inspecting earlier historical experiments;",
        "so even results on older years are **exploratory, not clean confirmation**.",
        "With dozens of comparisons a lucky leader is expected; no retrospective",
        "winner is promoted without an untouched future validation period.",
        "",
    ]
    for game,d in report["games"].items():
        lines += [f"## {game.title()}",
                  "",
                  f"History: {d['archive_draws']:,} draws. One-number test:",
                  f"**{d['walk_forward_draws']:,} actual drawings**,",
                  f"{d['first_test_date']} to {d['last_test_date']}.",
                  "",
                  "| Prediction method | Exact Straight | Any Order | Fair-expected Any Order | Fireball Any Order | Log-score gain vs fair |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for name,info in d["models"].items():
            x=info["all"]
            lines.append(f"| {name} | {x['straight']} | "
                         f"{x['any_order_including_straight']} | "
                         f"{x['expected_any_order_if_fair']:.1f} | "
                         f"{x['fireball_any_order']} | "
                         f"{x['log_score_advantage_vs_fair_per_draw']:+.5f} |")
        lines += ["",
                  "Log-score gain > 0 means the probabilistic model assigned",
                  "higher likelihood to actual ordered winners than uniform",
                  "probabilities. Both selection policies share identical log scores",
                  "because their underlying probability model is identical.",
                  ""]
    lines += ["## Research decision",
              "",
              "Keep the fair-uniform model as the null until a completely",
              "future, frozen-rule test shows reliable improvement in log",
              "probability with statistical uncertainty and multiple testing",
              "accounted for. Exact-hit and Any Order deviations must also",
              "outperform their relevant fair expected counts across years.",
              "",
              "Full per-year and per-period breakdown: [research_one_pick.json](research_one_pick.json).",
              "",
             ]
    return "\n".join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--json",default="reports/research_one_pick.json")
    parser.add_argument("--markdown",default="reports/research_one_pick.md")
    parser.add_argument("--seed",type=int,default=SEED)
    args=parser.parse_args()
    report={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "version":"val_one_pick_walkforward_v1",
        "note":"Exploratory historical test; one pick per real drawing, no prospective edge proven.",
        "seed":args.seed,"games":{},
    }
    for game in GAMES:
        data,source=fetch_full(game)
        windows=[w for w in WINDOWS if w<len(data)]
        out=evaluate(game,data,windows=windows,seed=args.seed)
        out["source"]={k:v for k,v in source.items() if k!="quality_audit"}
        out["source_quality"]=source["quality_audit"]
        report["games"][game]=out
        highlights=sorted(out["models"].items(),key=lambda t:t[1]["all"]["any_order_excess_over_fair_expected"],reverse=True)
        print(json.dumps({"game":game,"draws":out["walk_forward_draws"],
                          "most_any_order_excess":[{"method":n,
                          "straight":x["all"]["straight"],
                          "any_order":x["all"]["any_order_including_straight"],
                          "fair_expected":x["all"]["expected_any_order_if_fair"]}
                          for n,x in highlights[:3]],
                          "fair_logscore":out["models"]["random"]["all"]["log_score_advantage_vs_fair_per_draw"]}),flush=True)
    for path,body in [(args.json,json.dumps(report,indent=2)+"\n"),
                      (args.markdown,markdown(report)+"\n")]:
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(body)
    print("Saved VAL one-prediction-per-drawing study.")


if __name__ == "__main__":
    main()
