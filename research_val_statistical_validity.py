"""VAL: falsifiable power and paired-evidence gate for complete Any Order wins.

This program does NOT create or optimize a new formula. It prevents false
claims of improvement from code tests, synthetic results, tiny samples, or
rotation-based ticket duplication.

- Exact one-sided binomial sample-size design under fair independent draws.
- Familywise alpha=.05/3 for three predeclared Pick 3/4/5 game claims.
- Real historical paired model-vs-control full Box wins using exact McNemar
  conditional test *only when both portfolios have identical fair coverage*.
- Prospective ledger checks verify frozen pre-cutoff predictions, three
  distinct Box outcome sets, and correct target-specific grading.
- Rejects/masks statistics if the equal-coverage assumption does not hold.
- Reports previously inspected historical outcomes as exploratory, NEVER as
  confirmatory evidence, even when a retrospective p-value is low.

A properly random independent lottery cannot be forecast from its past draws.
No model promotion is performed by this script.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

from val_box import box_ways,digits_key,any_order_prize

GAMES=("pick3","pick4","pick5")
NUM_TICKETS=3
FAMILY_ALPHA=.05
RELATIVE_LIFT=1.25
DESIGN_POWER=.80
DRAWS_PER_YEAR_ASSUMED=730
REAL=Path("reports/research_pooled_box_v2_real.json")
FUTURE=Path("reports/prospective_pooled_full_box_v2.json")
JSON_OUT=Path("reports/val_statistical_validity.json")
MD_OUT=Path("reports/val_statistical_validity.md")


def binom_upper_tail(n,p,k):
    """P(Binomial(n,p)>=k), exact in distribution (floating point).

    Start at P(X=k) via log-gamma and recurse upward; avoids underflow
    from computing P(X=0) for large n. Stop only after mass is negligible
    beyond the mode.
    """
    if not isinstance(n,int) or n<0 or not 0<=p<=1:
        raise ValueError("Invalid binomial")
    if k<=0:
        return 1.
    if k>n or p==0:
        return 0.
    if p==1:
        return 1.
    log_pdf=(math.lgamma(n+1)-math.lgamma(k+1)-
             math.lgamma(n-k+1)+k*math.log(p)+
             (n-k)*math.log1p(-p))
    term=math.exp(log_pdf)
    total=term
    ratio=p/(1-p)
    j=k
    mode=int((n+1)*p)
    while j<n:
        term*=(n-j)/(j+1)*ratio
        j+=1
        total+=term
        if j>mode and term<total*1e-15:
            break
    return max(0.,min(1.,total))


def required_draws(fair_p,relative_lift=RELATIVE_LIFT,
                   alpha=FAMILY_ALPHA/len(GAMES),
                   target_power=DESIGN_POWER,max_draws=100000):
    """First n reaching exact binomial power with a fixed one-sided test.

    Null critical successes k never decreases as the draw count increases.
    Unlike naive binary search over sample sizes, sequential scanning
    is safe against discrete sawtooth power between k increments.
    """
    p1=fair_p*relative_lift
    if not 0<fair_p<p1<1 or not 0<alpha<1 or not 0<target_power<1:
        raise ValueError("Invalid power design")
    critical=1
    for n in range(1,max_draws+1):
        while critical<=n and binom_upper_tail(n,fair_p,critical)>alpha:
            critical+=1
        realized_power=binom_upper_tail(n,p1,critical)
        if realized_power>=target_power:
            return dict(draws=n,critical_full_box_hits=critical,
                        fair_null_hit_probability=fair_p,
                        alternative_hit_probability=p1,
                        null_tail_at_threshold=binom_upper_tail(
                            n,fair_p,critical),
                        achieved_power=realized_power,
                        years_at_730_draws_per_year=n/DRAWS_PER_YEAR_ASSUMED)
    raise ValueError("Design exceeds max_draws")


def exact_paired_equal_coverage(model_only,control_only):
    """One-sided exact conditional discordance test when fair coverage equal.

    Under a truly independent fair draw, before observing each target,
    model-only and control-only probabilities are identical if both
    portfolios have equal fair outcome mass. Pair overlap is allowed.
    Historical model selection still invalidates confirmatory use.
    """
    n=model_only+control_only
    return dict(model_only=model_only,control_only=control_only,
                discordant=n,
                one_sided_p=binom_upper_tail(n,.5,model_only),
                net_model_only_advantage=model_only-control_only)


def fair_union(game,tickets):
    width=int(game[-1])
    if len(tickets)!=NUM_TICKETS:
        raise ValueError("Not exactly three tickets")
    keys=[]
    for ticket in tickets:
        if len(ticket)!=width or any(
                type(x) is not int or not 0<=x<=9 for x in ticket):
            raise ValueError("Invalid digits")
        if any_order_prize(game,ticket)<=0:
            raise ValueError("Ticket isn't an Any Order Box play")
        keys.append(digits_key(ticket))
    if len(set(keys))!=NUM_TICKETS:
        raise ValueError("Duplicate complete Any Order outcome")
    return sum(box_ways(k) for k in keys)/10**width


def historical_audit(source):
    out={}
    for game in GAMES:
        events=source["games"][game]["events"]
        details={"targets":len(events),"model_full_box_wins":0,
                 "control_full_box_wins":0,"both":0,"neither":0,
                 "model_only":0,"control_only":0,
                 "coverage_mismatches":0}
        for e in events:
            model=bool(e["v2_win"])
            control=bool(e["random_win"])
            details["model_full_box_wins"]+=model
            details["control_full_box_wins"]+=control
            details["both"]+=model and control
            details["neither"]+=not model and not control
            details["model_only"]+=model and not control
            details["control_only"]+=control and not model
            if abs(e["v2_fair_prob"]-e["random_fair_prob"])>1e-12:
                details["coverage_mismatches"]+=1
        if not details["coverage_mismatches"]:
            details["paired_exploratory_only"]=exact_paired_equal_coverage(
                details["model_only"],details["control_only"])
        else:
            details["paired_exploratory_only"]=None
        details["confirmatory_valid"]=False
        details["reason"]="2025/2026 history was previously inspected; no untouched validation."
        out[game]=details
    return out


def prospective_audit(source):
    out={}
    for game in GAMES:
        records=source["games"][game]
        stats=dict(frozen=len(records),settled=0,unsettled=0,
                   invalid_records=[],equal_coverage=True,
                   model_only=0,control_only=0,both=0,neither=0)
        for rec in records:
            target=rec["target"]
            f=rec["forecast"]
            try:
                made=datetime.fromisoformat(rec["created_utc"])
                deadline=datetime.fromisoformat(target["wagers_close_utc"])
                if made>=deadline:
                    raise ValueError("Prediction created after sales cutoff")
                if target["game"]!=game:
                    raise ValueError("Frozen wrong-game target")
                p_model=fair_union(game,f["model_tickets"])
                p_control=fair_union(game,f["uniform_coverage_controls"])
                if abs(p_model-f["model_fair_full_box_coverage"])>1e-12:
                    raise ValueError("Stored model fair coverage differs")
                if abs(p_control-f["control_fair_full_box_coverage"])>1e-12:
                    raise ValueError("Stored control fair coverage differs")
                if abs(p_model-p_control)>1e-12:
                    stats["equal_coverage"]=False
                if rec["result"] is None:
                    stats["unsettled"]+=1
                    continue
                actual=rec["result"]["official_numbers"]
                if len(actual)!=int(game[-1]):
                    raise ValueError("Wrong result width")
                result_model=int(digits_key(actual) in
                    {digits_key(x) for x in f["model_tickets"]})
                result_control=int(digits_key(actual) in
                    {digits_key(x) for x in f["uniform_coverage_controls"]})
                scored=rec["result"]["accuracy"]
                if (result_model!=int(scored["model_box_wins"]) or
                    result_control!=int(scored["control_box_wins"])):
                    raise ValueError("Frozen Box grade doesn't match official outcome")
                stats["settled"]+=1
                stats["model_only"]+=result_model and not result_control
                stats["control_only"]+=result_control and not result_model
                stats["both"]+=result_model and result_control
                stats["neither"]+=not result_model and not result_control
            except (ValueError,KeyError,TypeError) as exc:
                stats["invalid_records"].append(dict(
                    id=rec.get("id"),reason=str(exc)))
        if (stats["settled"] and stats["equal_coverage"]
            and not stats["invalid_records"]):
            stats["paired_evidence"]=exact_paired_equal_coverage(
                stats["model_only"],stats["control_only"])
        else:
            stats["paired_evidence"]=None
        stats["eligible_for_model_promotion"]=False
        out[game]=stats
    return out


def markdown(result):
    lines=[
        "# VAL: independent-evidence and statistical-power reality check",
        "",
        "**The experiment's objective is complete Any Order winning digit",
        "multisets from exactly three different Box tickets per drawing.**",
        "A matching subset, one correct position, or three rotations of",
        "the same digits are not three independent wins.",
        "",
        "## What it takes to distinguish a 25% relative improvement",
        "",
        "Assumptions: genuinely independent fair digits; a **single fixed**",
        "model with a real 25% relative advantage in complete Box hit",
        "probability; exact one-sided binomial test, familywise 5% false",
        "positive budget across three games (alpha = 1.67% per game);",
        "80% power. Three distinct all-different Box tickets per draw.",
        "**This is optimistic:** demonstrating superiority over an",
        "additional noisy random-control sample can require even more.",
        "",
        "| Game | Fair P(any complete Box win) | Hypothetical +25% | Required NEW independent draws | Approx. years, twice daily |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for game,x in result["power"].items():
        lines.append(
            f'| {game} | {100*x["fair_null_hit_probability"]:.3f}% | '
            f'{100*x["alternative_hit_probability"]:.3f}% | '
            f'{x["draws"]:,} | {x["years_at_730_draws_per_year"]:.1f} |')
    lines.extend([
        "",
        "Those years are a statistical detection calculation, not",
        "a forecast of how long VAL should run, and are NOT evidence",
        "that any actual predictive advantage exists. With no true",
        "exploitable nonrandomness, no amount of historical tweaking",
        "creates a repeatable predictive advantage.",
        "",
        "## Full-Box model-vs-random paired audit on real archived draws",
        "",
        "A paired discordance test measures model-only versus",
        "control-only full wins. Under a fair null and **equal fair",
        "coverage**, the two types of discordant result are equally",
        "likely, including when the portfolios overlap. If fair",
        "coverage differs, that assumption is invalid and no paired",
        "p-value is claimed. All these archives were previously",
        "inspected; retrospective p-values are **exploratory only**.",
        "",
        "| Game | Targets | Model wins | Random wins | Model-only | Random-only | Exploratory one-sided paired p |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for game,x in result["real_historical"].items():
        evidence=x["paired_exploratory_only"]
        p=(f'{evidence["one_sided_p"]:.5f}' if evidence else "not valid")
        lines.append(
            f'| {game} | {x["targets"]} | '
            f'{x["model_full_box_wins"]} | '
            f'{x["control_full_box_wins"]} | '
            f'{x["model_only"]} | {x["control_only"]} | {p} |')
    lines.extend([
        "",
        "## Immutable pre-draw evidence status",
        "",
        "| Game | Frozen forecasts | Completed official results | Unequal coverage? | Auditable? |",
        "| --- | ---: | ---: | --- | --- |",
    ])
    for game,x in result["prospective"].items():
        lines.append(
            f'| {game} | {x["frozen"]} | {x["settled"]} | '
            f'{"yes" if not x["equal_coverage"] else "no"} | '
            f'{"no" if x["invalid_records"] else "yes"} |')
    lines.extend([
        "",
        "## Decision",
        "",
        "No model promotion: historical comparisons are reused and",
        "the prospective record has not established an advantage.",
        "The technically correct next signal is a new, legally available",
        "pre-draw explanatory variable or genuinely unseen future",
        "calibrated probability improvement, not another post-hoc",
        "tune of these same digit-frequency formulas.",
        "",
        "Unproven models remain research-only. The live VAL decision",
        "system is untouched by this audit.",
        "",
        "[Machine-readable evidence and exact test parameters]",
        "(val_statistical_validity.json).","",
    ])
    return "\n".join(lines)


def main():
    source=json.loads(REAL.read_text())
    future=json.loads(FUTURE.read_text())
    power={}
    for game in GAMES:
        width=int(game[-1])
        fair_p=NUM_TICKETS*math.factorial(width)/10**width
        power[game]=required_draws(fair_p)
        print("POWER",game,
              power[game]["draws"],
              round(power[game]["years_at_730_draws_per_year"],2),
              flush=True)
    result=dict(version="val_complete_box_validity_v1",
                updated_utc=datetime.now(timezone.utc).isoformat(),
                scientific_claim="no real predictive lift established",
                familywise_alpha=FAMILY_ALPHA,
                target_power=DESIGN_POWER,
                assumed_relative_lift=RELATIVE_LIFT,
                source_historical_previously_inspected=True,
                power=power,
                real_historical=historical_audit(source),
                prospective=prospective_audit(future))
    for game,metrics in result["real_historical"].items():
        print("PAIRED",game,
              metrics["model_only"],metrics["control_only"],
              metrics["paired_exploratory_only"],flush=True)
    for game,metrics in result["prospective"].items():
        print("FUTURE",game,"frozen",metrics["frozen"],
              "settled",metrics["settled"],
              "errors",len(metrics["invalid_records"]),flush=True)
    # A prospective experiment is not auditable if the frozen target,
    # prediction time, ticket identity, or grade is internally inconsistent.
    # Fail the workflow rather than publishing a misleading success.
    invalid={game:info["invalid_records"]
             for game,info in result["prospective"].items()
             if info["invalid_records"]}
    if invalid:
        raise RuntimeError("Prospective full Box evidence failed integrity checks: "
                           +json.dumps(invalid))
    JSON_OUT.parent.mkdir(parents=True,exist_ok=True)
    JSON_OUT.write_text(json.dumps(result,indent=2)+"\n")
    MD_OUT.write_text(markdown(result)+"\n")
    print("SAVED",JSON_OUT,MD_OUT,flush=True)


if __name__=="__main__":
    main()
