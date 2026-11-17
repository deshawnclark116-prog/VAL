"""Keno: one five-number ticket per draw, exact frozen official source replay.

Uses the FIRST of each model's three original tickets, selected before
the actual outcome. Also regrades all three and requires exact equivalence
with the earlier 3-ticket published report (draws, matches, payouts).
Research only; does not touch VAL live predictions or schedules.
"""
from __future__ import annotations
import argparse,gzip,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from research_keno_official import Counters,predict,WARMUP
from research_keno import PRIZE_FIVE_SPOT,exact_fair_match_probabilities,match_count,stable_rng
from val import METHODS

MODELS=("control",)+METHODS
ARCHIVE=Path("reports/keno_official_history.json.gz")
THREE_REPORT=Path("reports/research_keno_official.json")
OUTPUT=Path("reports/research_keno_one_ticket.json")
MARKDOWN=Path("reports/research_keno_one_ticket.md")


def empty():
    return dict(dist=Counter(),gross=0,halves=[Counter(),Counter()],five_audit=[])


def grade(state,draw,ticket,half):
    k=match_count(ticket,draw["numbers"])
    cash=PRIZE_FIVE_SPOT[k]
    state["dist"][k]+=1
    state["gross"]+=cash
    s=state["halves"][half]
    s["n"]+=1
    s["gross"]+=cash
    s["five"]+=int(k==5)
    if k==5:
        state["five_audit"].append(dict(draw_id=draw["draw_id"],date=draw["date"],
                                        ticket=ticket,winning_numbers=draw["numbers"]))


def describe(state):
    n=sum(state["dist"].values())
    return dict(tickets=n,by_matches={str(k):state["dist"][k] for k in range(6)},
                five_of_five=state["dist"][5],four_of_five=state["dist"][4],
                three_or_more=sum(state["dist"][k] for k in (3,4,5)),
                avg_matches=round(sum(k*v for k,v in state["dist"].items())/n,6),
                gross_usd=state["gross"],net_usd=state["gross"]-n,
                gross_per_dollar=round(state["gross"]/n,6),
                early=dict(state["halves"][0]),late=dict(state["halves"][1]),
                five_match_audit=state["five_audit"])


def replay(rows,warmup=WARMUP):
    if len(rows)<warmup+50:
        raise ValueError("Insufficient Keno history")
    scores={m:{"one":empty(),"three":empty()} for m in MODELS}
    mid=warmup+(len(rows)-warmup)//2
    rolling=Counters(rows,warmup)
    for i in range(warmup,len(rows)):
        draw=rows[i]
        half=int(i>=mid)
        for m in MODELS:
            method="random" if m=="control" else m
            chosen=predict(rolling.weights(method),stable_rng(20261117,m,draw["draw_id"]))
            if len(chosen)!=3:
                raise AssertionError("Three original picks required")
            grade(scores[m]["one"],draw,chosen[0],half)
            for ticket in chosen:
                grade(scores[m]["three"],draw,ticket,half)
        rolling.step(rows,i)
        if (i-warmup+1)%2000==0:
            print("Graded "+str(i-warmup+1)+" historical draws",flush=True)
    fair=exact_fair_match_probabilities()
    results={m:{"one":describe(scores[m]["one"]),
                "three":describe(scores[m]["three"])} for m in MODELS}
    return dict(draws=len(rows)-warmup,source_draws=len(rows),
                first_test_draw_id=rows[warmup]["draw_id"],
                last_test_draw_id=rows[-1]["draw_id"],
                warmup=warmup,spot_count=5,
                expected_five_hits_per_method_one_ticket=(len(rows)-warmup)*fair[5],
                fair_expected_avg_matches=1.25,
                fair_gross_return_per_dollar=sum(PRIZE_FIVE_SPOT[k]*fair[k] for k in range(6)),
                models=results)


def check_against_previous(current,prior):
    if current["draws"]!=prior["results"]["draws"]:
        raise AssertionError("Frozen source draw count changed")
    for m,comparison in current["models"].items():
        now=comparison["three"]
        old=prior["results"]["methods"][m]
        for a,b in (("tickets","tickets"),("five","five_of_five"),
                    ("gross","gross_usd"),("net","net_usd")):
            if old[a]!=now[b]:
                raise AssertionError("Replayed three-ticket baseline differs for "+m+": "+a)
        for k in range(6):
            if old["distribution"][str(k)]!=now["by_matches"][str(k)]:
                raise AssertionError("Three-ticket hit counts differ for "+m)
        if comparison["one"]["tickets"]*3!=now["tickets"]:
            raise AssertionError("Incorrect single-ticket count")
    return True


def to_md(comparison):
    rows=[
        "# VAL Keno: ONE five-number prediction per official drawing","",
        "Same frozen official archive and exact RNG/model state as prior 3-ticket replay.",
        "Each single prediction is the FIRST of the original three tickets.",
        "No looking at the result to select the best ticket; no live wagers.","",
        "Official drawings tested: **"+format(comparison["draws"],",")+"**.",
        "Each method spends one hypothetical dollar per drawing.","",
        "| Model | 5/5 | 4/5 | Avg balls matched | Gross per dollar (one) | Net (one) | Gross per dollar (three) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    ]
    for m,a in comparison["models"].items():
        one=a["one"];three=a["three"]
        rows.append("| "+m+" | "+str(one["five_of_five"])+" | "+str(one["four_of_five"])+" | "+
                    format(one["avg_matches"],".4f")+" | "+
                    format(one["gross_per_dollar"],".4f")+" | "+
                    format(one["net_usd"],"+,")+" | "+
                    format(three["gross_per_dollar"],".4f")+" |")
    rows+=["","## Early vs later period — single ticket","",
           "| Model | Early return per dollar | Late return per dollar | Early 5/5 | Late 5/5 |",
           "| --- | ---: | ---: | ---: | ---: |"]
    for m,a in comparison["models"].items():
        x,y=a["one"]["early"],a["one"]["late"]
        rows.append("| "+m+" | "+format(x["gross"]/x["n"],".4f")+" | "+
                    format(y["gross"]/y["n"],".4f")+" | "+
                    str(x["five"])+" | "+str(y["five"])+" |")
    rows+=["",
        "## Statistical interpretation","",
        "The fair average is 1.25 of five numbers matched per play; an",
        "ordinary five-spot ticket has a chance of about 1 in 1,550 of 5/5.",
        "Random expectation for these drawings: "+
        format(comparison["expected_five_hits_per_method_one_ticket"],".2f")+
        " perfect tickets per method.",
        "The official Keno Director's Order 134 (2026), Section H, page 8,",
        "specifies main-game prizes on a 1-dollar 5-spot ticket:",
        "0–2 matches pay nothing, 3 matches pay 2 dollars,",
        "4 pay 20 dollars, 5 pay 450 dollars.",
        "Fair expected gross return per dollar: "+
        format(comparison["fair_gross_return_per_dollar"],".4f")+
        " (i.e., negative expected return).",
        "",
        "The original three-ticket report's entire outcome distribution,",
        "cost, gross winnings and 5/5 counts are reproduced exactly.",
        "Historical testing across several methods remains exploratory:",
        "the highest observed method is not an independently proven edge.",
        "No real bets, no live code changes.",
        "",
        "Details and individual 5/5 tickets in",
        "[research_keno_one_ticket.json](research_keno_one_ticket.json).",""]
    return "\n".join(rows)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",default=str(ARCHIVE))
    p.add_argument("--prior",default=str(THREE_REPORT))
    a=p.parse_args()
    with gzip.open(a.archive,"rt",encoding="utf-8") as f:
        rows=json.load(f)
    ids=[r["draw_id"] for r in rows]
    if ids!=sorted(set(ids)):
        raise ValueError("Cached official results are not unique and chronological")
    for r in rows:
        x=r["numbers"]
        if len(x)!=20 or len(set(x))!=20:
            raise ValueError("Malformed official draw")
    prior=json.loads(Path(a.prior).read_text())
    comparison=replay(rows)
    verified=check_against_previous(comparison,prior)
    output=dict(version="val_keno_frozen_one_ticket_v1",
                generated_utc=datetime.now(timezone.utc).isoformat(),
                three_ticket_prior_verified=verified,
                official_archive=a.archive,
                comparison=comparison)
    OUTPUT.write_text(json.dumps(output,indent=2)+"\n")
    MARKDOWN.write_text(to_md(comparison)+"\n")
    for name,a in comparison["models"].items():
        print(json.dumps(dict(model=name,one=a["one"]["gross_per_dollar"],
                              three=a["three"]["gross_per_dollar"],
                              five=a["one"]["five_of_five"],
                              net=a["one"]["net_usd"])),flush=True)
    print("Three-ticket baseline reproduced exactly.",flush=True)


if __name__=="__main__":main()
