"""Real-drawing full Any Order benchmark for pooled full-Box v2.

Strict chronological replay: for each target, all selected digit probabilities
come only from earlier official draws. Three independent Box tickets per model
and per fair random control. The historic v1 rotations remain the frozen
original comparator; never retroactively edit their prospective ledger.

Real history has been examined in prior VAL research. THIS IS EXPLORATORY.
Even a small p-value here is not legitimate untouched validation.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

from research_decades import fetch_full
from val_box import box_score_batch, digits_key, box_ways
from val_pooled_box_formula import generate, GAMES

VERSION="real_full_box_v2_vs_v1_and_fair"
OUT=Path("reports/research_pooled_box_v2_real.json")
MD=Path("reports/research_pooled_box_v2_real.md")
PERIODS=("2025","2026")
SEED=20261120


def seeded(game,target):
    raw="|".join(map(str,(VERSION,SEED,game,target["date"],
                          target["stream"]))).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8],"big"))


def v1_rotations(probs,width):
    """Reproduce original v1's three ordered top-digit rotations."""
    ranked=sorted(range(10),key=lambda d:(-probs[d],d))
    return [[ranked[(k+j)%3] for j in range(width)] for k in range(3)]


def unique_box_prob(game,tickets):
    """Union of complete disjoint multiset outcomes, NOT sum of rotations."""
    width=int(game[-1])
    unique={digits_key(t) for t in tickets}
    return sum(box_ways(combo) for combo in unique)/10**width


def bernoulli_upper_tail(ps,observed):
    """Exact Poisson-binomial P(X>=observed) under independent fair draws."""
    if observed<=0:
        return 1.
    below=[0.]*observed
    below[0]=1.
    for p in ps:
        if not 0<=p<=1:
            raise ValueError("Invalid fair outcome probability")
        for j in range(observed-1,-1,-1):
            below[j]=(below[j]*(1-p)+
                      (below[j-1]*p if j>0 else 0.))
    return max(0.,min(1.,1.-sum(below)))


def mean_paired_ci(events,period,replicates=1200):
    """Resample whole calendar dates (Day/Night together) to avoid pseudo-n."""
    by_day=defaultdict(list)
    for x in events:
        if x["period"]==period:
            by_day[x["date"]].append(x["v2_win"]-x["random_win"])
    days=list(by_day)
    if not days:
        return [None,None]
    group=[sum(by_day[d]) for d in days]
    rng=random.Random(20261120+len(days))
    sims=[]
    for _ in range(replicates):
        sims.append(sum(group[rng.randrange(len(group))]
                        for _ in days))
    sims.sort()
    return [sims[int(.025*replicates)],sims[int(.975*replicates)]]


def aggregate(game,events):
    out={}
    for period in PERIODS+("combined",):
        selected=[x for x in events if x["period"]==period or period=="combined"]
        n=len(selected)
        if not n:
            continue
        scores={}
        for name in ("v2","v1","random"):
            won=sum(x[name+"_win"] for x in selected)
            fair_ps=[x[name+"_fair_prob"] for x in selected]
            estimated=sum(fair_ps)
            scores[name]=dict(
                full_box_wins=won,rate=won/n,
                fair_expected_hits=estimated,
                fair_at_least_one_rate=estimated/n,
                upper_tail_probability_fair=bernoulli_upper_tail(fair_ps,won),
                mean_unique_box_sets=sum(x[name+"_unique"] for x in selected)/n,
            )
        gained=sum(x["mean_joint_log_gain"] for x in selected)/n
        out[period]=dict(target_draws=n,
                         games=game,by_formula=scores,
                         v2_minus_random_hits=(
                             scores["v2"]["full_box_wins"]-
                             scores["random"]["full_box_wins"]),
                         v2_vs_random_bootstrap_95pct_hit_difference=(
                             mean_paired_ci(selected,period) if period!="combined"
                             else mean_paired_ci(selected,"2025")),
                         mean_pooled_digit_joint_log_gain_vs_fair=gained)
        if period=="combined":
            # Compute the combined-day CI without silently treating draws
            # from separate years as independent calendar sessions.
            out[period]["v2_vs_random_bootstrap_95pct_hit_difference"]=(
                bootstrap_all(selected))
    return out


def bootstrap_all(events,replicates=1200):
    by_day=defaultdict(int)
    for row in events:
        by_day[row["date"]]+=row["v2_win"]-row["random_win"]
    blocks=list(by_day.values())
    rng=random.Random(1182026)
    sims=[sum(blocks[rng.randrange(len(blocks))]
              for _ in blocks) for _ in range(replicates)]
    sims.sort()
    return [sims[int(.025*replicates)],sims[int(.975*replicates)]]


def evaluate(game,rows):
    if game not in GAMES:
        raise ValueError(game)
    rows=sorted(rows,key=lambda r:(
        r["date"],0 if r["stream"]=="Day" else 1))
    if len({(r["date"],r["stream"]) for r in rows})!=len(rows):
        raise ValueError("Conflicting/duplicate official target rows")
    if len(rows)<500:
        raise ValueError("Insufficient training history")
    events=[]
    for index,target in enumerate(rows):
        period=target["date"][:4]
        if period not in PERIODS or index<500:
            continue
        # This is the actual paper research formula, not a hand-waved
        # marginal proxy. It must forecast before the target is revealed.
        prior=rows[:index]
        model=generate(game,prior,3,seeded(game,target))
        v1=v1_rotations(model["probabilities"],int(game[-1]))
        three={"v2":model["model_tickets"],
               "v1":v1,
               "random":model["control_tickets"]}
        actual=digits_key(target["numbers"])
        record=dict(date=target["date"],stream=target["stream"],period=period,
                    actual=list(target["numbers"]))
        for name,tickets in three.items():
            keys=[digits_key(t) for t in tickets]
            record[name+"_win"]=int(actual in keys)
            record[name+"_unique"]=len(set(keys))
            record[name+"_fair_prob"]=unique_box_prob(game,tickets)
            # End-to-end verification with exact settled ticket definition.
            settled=box_score_batch(
                game,[{"numbers":list(t)} for t in tickets],target)
            if bool(settled["box_wins"])!=bool(record[name+"_win"]):
                raise AssertionError("Inconsistent full Box win grading")
            if abs(record[name+"_fair_prob"]-
                   settled["box_fair_at_least_one_prob"])>1e-12:
                raise AssertionError("Rotated ticket union coverage mismeasured")
        record["mean_joint_log_gain"]=sum(
            math.log(model["probabilities"][digit]/.1)
            for digit in target["numbers"])
        events.append(record)
        if len(events)%400==0:
            print("PROGRESS",game,len(events),flush=True)
    return dict(game=game,metrics=aggregate(game,events),
                total_scored_targets=len(events),events=events)


def markdown(result):
    text=[
        "# VAL pooled-digit full Any Order accuracy: actual historical drawings",
        "",
        "**This is real lottery history, NOT a simulated drawing machine.**",
        "The 2025/2026 periods have already been inspected in other VAL",
        "research, so this is a retrospective, exploratory test, NOT fresh",
        "independent proof of an edge. Every candidate is based on earlier",
        "official outcomes. No hidden future results or training leakage.",
        "",
        "The metric is the probability of **at least one complete Box hit**",
        "from three tickets. Three ticket rotations of the same multiset",
        "count as ONE opportunity. Random controls use three distinct",
        "all-distinct digit sets. All tickets are paper-only.",
        "",
        "| Game | Period | Real targets | Corrected v2 Box | Old rotations v1 Box | Fair random Box | v2 fair expected | random fair expected | v2 minus random | Paired 95% CI on hit difference |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for game,report in result["games"].items():
        for period,row in report["metrics"].items():
            m=row["by_formula"]
            ci=row["v2_vs_random_bootstrap_95pct_hit_difference"]
            text.append(
                f'| {game} | {period} | {row["target_draws"]} | '
                f'{m["v2"]["full_box_wins"]} | '
                f'{m["v1"]["full_box_wins"]} | '
                f'{m["random"]["full_box_wins"]} | '
                f'{m["v2"]["fair_expected_hits"]:.2f} | '
                f'{m["random"]["fair_expected_hits"]:.2f} | '
                f'{row["v2_minus_random_hits"]:+d} | '
                f'[{ci[0]}, {ci[1]}] |')
    text += [
        "",
        "## Interpretation and promotion rule",
        "",
        "The original v1 pool rotated the same top-3 digits. In Pick 3",
        "that buys one Box set three times; the corrected v2 portfolio",
        "uses three distinct Box sets. This improves fair any-order",
        "coverage per *three distinct predictions*, but does NOT show",
        "that the digit probabilities contain information about the next",
        "random drawing. Expected paper payout and chance of at least one",
        "hit are different objectives; no profitability is inferred.",
        "",
        "A formula predictive edge would need repeated excess complete",
        "Box winners above equally priced maximum-coverage fair controls,",
        "with uncertainty under the iid-fair hypothesis and strictly",
        "future, frozen predictions whose outcomes were never used to",
        "choose the formula. Historical comparative wins do not establish",
        "that standard.",
        "",
        "[Target-by-target full Box results](research_pooled_box_v2_real.json).",""
    ]
    return "\n".join(text)


def main():
    data=dict(version=VERSION,generated_utc=datetime.now(timezone.utc).isoformat(),
              official_archive_previously_inspected=True,
              real_not_synthetic=True,prospective=False,
              baseline="three distinct all-distinct fair Box tickets",
              games={})
    for game in GAMES:
        rows,source=fetch_full(game)
        print("OFFICIAL",game,len(rows),flush=True)
        data["games"][game]=evaluate(game,rows)
        summary=data["games"][game]["metrics"]["combined"]
        print("REAL",game,summary["target_draws"],
              {name:[item["full_box_wins"],round(item["fair_expected_hits"],3)]
               for name,item in summary["by_formula"].items()},
              "paired_ci",
              summary["v2_vs_random_bootstrap_95pct_hit_difference"],flush=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,indent=2)+"\n")
    MD.write_text(markdown(data)+"\n")
    print("SAVED",OUT,MD,flush=True)


if __name__=="__main__":
    main()
