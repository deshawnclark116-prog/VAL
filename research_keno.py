"""Research-only Keno five-spot backtest on externally published results.

Keno picks 5 of 80; the draw contains 20 distinct numbers. Source is a
secondary public results page rather than verified official bulk history.
This module will fail closed if it cannot parse enough distinct draw IDs.

No changes to the live VAL generator, schedules or paper-pick ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from val import METHODS, GAMES, generate

SOURCE_URL="https://www.comparethelotto.com/us/results-virginia-keno?refresh=true"
TRAINING_DRAWS=30
PICKS_PER_METHOD=3
# Current official Keno-with-BULLS-EYE main-game $1 five-spot schedule,
# WITHOUT purchasing optional BULLS-EYE. Current chart explicitly pays $2
# for zero matches: https://www.valottery.com/data/draw-games/keno
# The older /en/ page omits that prize and is NOT the current paytable.
PRIZE_FIVE_SPOT={0:2, 1:0, 2:0, 3:2, 4:20, 5:450}


class ExtractText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.segments=[]
        self.skip=0

    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript"):
            self.skip += 1
        if tag in ("p","div","br","li","h1","h2","h3","h4"):
            self.segments.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script","style","noscript"):
            self.skip=max(0,self.skip-1)
        if tag in ("p","div","li","h1","h2","h3","h4"):
            self.segments.append(" ")

    def handle_data(self, data):
        if not self.skip: self.segments.append(data + " ")

    def text(self):
        return re.sub(r"\s+"," "," ".join(self.segments))


def parse_results(html):
    parser=ExtractText()
    parser.feed(html)
    s=parser.text()
    found={}
    seen=Counter()
    for match in re.finditer(r"\bDraw\s*#\s*(\d{3,10})\b",s,re.I):
        draw_id=int(match.group(1))
        leading=s[max(0,match.start()-95):match.start()]
        dates=re.findall(
            r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}(?:st|nd|rd|th)?\s+"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+\d{4}\b",leading,re.I)
        if not dates:continue
        snippet=s[match.end():match.end()+270]
        snippet=re.sub(r"^\s*NEW\b","",snippet,flags=re.I)
        numeric=re.findall(r"(?<![\dA-Za-z])\d{1,2}(?![\dA-Za-z])",snippet)
        if len(numeric)<20:continue
        nums=[int(x) for x in numeric[:20]]
        if len(set(nums))!=20 or any(not 1<=x<=80 for x in nums):
            continue
        date_string=re.sub(r"(st|nd|rd|th)\b","",dates[-1],flags=re.I)
        draw_date=datetime.strptime(date_string,"%a %d %B %Y").date().isoformat()
        row={"draw_id":draw_id,"date":draw_date,"numbers":sorted(nums)}
        if draw_id in found and found[draw_id]!=row:
            raise ValueError(f"Conflicting Keno draw ID {draw_id}")
        seen[draw_id]+=1
        found[draw_id]=row
    rows=sorted(found.values(),key=lambda x:x["draw_id"])
    if len(rows)<TRAINING_DRAWS+20:
        raise ValueError(f"Too few usable Keno draws: {len(rows)} (min 50)")
    if any(a["date"]>b["date"] for a,b in zip(rows,rows[1:])):
        raise ValueError("Draw IDs and dates do not sort chronologically")
    if any(a["date"]>datetime.now(timezone.utc).date().isoformat() for a in rows):
        raise ValueError("Future Keno record in source")
    gaps=sum(b["draw_id"]-a["draw_id"]-1 for a,b in zip(rows,rows[1:]))
    return rows, {"unique_draws":len(rows),"duplicate_listings":sum(n-1 for n in seen.values()),
                  "missing_draw_ids_between_first_and_last":gaps,
                  "first_draw_id":rows[0]["draw_id"],"last_draw_id":rows[-1]["draw_id"],
                  "first_date":rows[0]["date"],"last_date":rows[-1]["date"]}


def stable_rng(*pieces):
    digest=hashlib.sha256(":".join(map(str,pieces)).encode()).digest()
    return random.Random(int.from_bytes(digest[:8],"big"))


def exact_fair_match_probabilities(spots=5):
    denom=math.comb(80,spots)
    return {k:math.comb(20,k)*math.comb(60,spots-k)/denom for k in range(spots+1)}


def match_count(pick, draw):
    if len(pick)!=5 or len(set(pick))!=5 or any(not 1<=x<=80 for x in pick):
        raise ValueError("Invalid five-spot ticket")
    if len(draw)!=20 or len(set(draw))!=20 or any(not 1<=x<=80 for x in draw):
        raise ValueError("Invalid 20-number Keno draw")
    return len(set(pick)&set(draw))


def grade_method(rows, method, control=False, seed=20261115, train=TRAINING_DRAWS,
                 picks_per_method=PICKS_PER_METHOD):
    if method not in METHODS:raise ValueError(method)
    if len(rows)<train+1:raise ValueError("Not enough draws")
    if picks_per_method<1 or picks_per_method>20:raise ValueError("Bad count")
    tallies=Counter()
    split=Counter()
    year_stats={}
    major_hits=[]
    for i in range(train,len(rows)):
        target=rows[i]
        previous=rows[max(0,i-500):i]
        history=[{"numbers":a["numbers"],"bonus":None,"extra":None,
                  "stream":"Main","game":"keno"} for a in previous]
        rng=stable_rng(seed,method,i,"control" if control else "model")
        picks=generate("keno",[] if control else history,
                       "random" if control else method,picks_per_method,rng)
        if len(picks)!=picks_per_method:raise AssertionError("Incorrect pick count")
        for ticket in picks:
            k=match_count(ticket["numbers"],target["numbers"])
            tallies[k]+=1
            if k>=4:
                major_hits.append({
                    "draw_id":target["draw_id"],"date":target["date"],
                    "ticket":ticket["numbers"],"draw_numbers":target["numbers"],
                    "matches":k,
                })
            split["total_matches"]+=k
            split["returned_$1_tickets"]+=PRIZE_FIVE_SPOT[k]
            year=target["date"][:4]
            if year not in year_stats:year_stats[year]={"tickets":0,"total_matches":0,"gross_return":0}
            year_stats[year]["tickets"]+=1
            year_stats[year]["total_matches"]+=k
            year_stats[year]["gross_return"]+=PRIZE_FIVE_SPOT[k]
    tickets=sum(tallies.values())
    return {
        "tickets":tickets,"draws":len(rows)-train,"distribution_matches":{str(i):tallies[i] for i in range(6)},
        "total_matches":split["total_matches"],
        "avg_matches_per_ticket":round(split["total_matches"]/tickets,5),
        "full_five_match_tickets":tallies[5],
        "four_or_more_tickets":tallies[4]+tallies[5],
        "three_or_more_tickets":tallies[3]+tallies[4]+tallies[5],
        "gross_hypothetical_prize_dollars":split["returned_$1_tickets"],
        "hypothetical_ticket_cost_dollars":tickets,
        "hypothetical_net_dollars":split["returned_$1_tickets"]-tickets,
        "hypothetical_return_per_dollar":round(split["returned_$1_tickets"]/tickets,5),
        "major_match_audit":major_hits,
        "by_year":year_stats
    }


def evaluate(rows,train=TRAINING_DRAWS,picks_per_method=PICKS_PER_METHOD,
             seed=20261115):
    controls=grade_method(rows,"random",control=True,seed=seed,train=train,picks_per_method=picks_per_method)
    methods={m:grade_method(rows,m,seed=seed,train=train,picks_per_method=picks_per_method)
             for m in METHODS}
    fair=exact_fair_match_probabilities()
    expected_returns=sum(PRIZE_FIVE_SPOT[k]*p for k,p in fair.items())
    return {
        "training_draws":train,
        "heldout_draws":len(rows)-train,
        "tickets_per_method":(len(rows)-train)*picks_per_method,
        "ticket_spots":5,
        "winning_numbers_per_draw":20,
        "fair_expected_matches_per_ticket":1.25,
        "fair_match_distribution":{str(k):v for k,v in fair.items()},
        "fair_expected_gross_return_per_$1_play":round(expected_returns,6),
        "random_control":controls,"methods":methods,
    }


def markdown(report):
    test=report["test"]
    cover=report["coverage"]
    lines=[
        "# VAL Keno: real-results five-spot exploratory replay",
        "",
        f"Created: {report['generated_utc']}.",
        "",
        "**Secondary-source public Keno history** from "+report["source"]["url"]+".",
        "This is NOT official-archive-verified history; draw-ID gaps mean",
        "the observed results are NOT necessarily consecutive real draws.",
        "Do not represent it as independent proof or as live bets.",
        "",
        f"Parsed {cover['unique_draws']} distinct result IDs from {cover['first_date']}",
        f"to {cover['last_date']}. Missing draw IDs between first/last:",
        f"{cover['missing_draw_ids_between_first_and_last']}.",
        f"Methods trained on {test['training_draws']} previous recorded draws,",
        f"then made {PICKS_PER_METHOD} unique five-number tickets on each",
        f"of {test['heldout_draws']} later recorded draws.",
        "",
        "Only previous **available** rows train each test. No future data.",
        "Game: pick five numbers from 1–80; official outcome contains 20.",
        "Each ticket averages 1.25 matches by chance.",
        "Current published $1 five-spot MAIN-game pays $2 for 0 matches,",
        "$0 for 1-2 matches, $2 for 3, $20 for 4, $450 for 5;",
        "optional BULLS-EYE is not purchased or scored.",
        "No money was wagered.",
        "",
        "Prize schedule source: https://www.valottery.com/data/draw-games/keno.",
        "The older /en/ page omits the 0-match prize and is outdated.",
        "These dollar results are illustrative, not official settlement.",
        "",
        "| Method | Tickets | Avg matches | 3+ matches | 4+ matches | 5/5 | Gross hypothetical return per $1 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name,details in [("Random independent control",test["random_control"]),
                         *[(name,v) for name,v in test["methods"].items()]]:
        lines.append(f"| {name} | {details['tickets']} | {details['avg_matches_per_ticket']:.3f} | "
                     f"{details['three_or_more_tickets']} | {details['four_or_more_tickets']} | "
                     f"{details['full_five_match_tickets']} | "
                     f"${details['hypothetical_return_per_dollar']:.3f} |")
    lines+=["", "## Four- and five-match audit trail", ""]
    for name, details in [("random_control",test["random_control"]), *test["methods"].items()]:
        for hit in details["major_match_audit"]:
            lines.append(
                f"- {name}: draw #{hit['draw_id']} ({hit['date']}) "
                f"ticket {', '.join(map(str,hit['ticket']))}; "
                f"{hit['matches']}/5 matched; official-unverified source draw "
                f"{', '.join(map(str,hit['draw_numbers']))}"
            )
    lines+=["",
            f"Fair expected five-spot gross return per $1: "
            f"${test['fair_expected_gross_return_per_$1_play']:.3f}.",
            "Overall profit cannot be established from a short sample:",
            "rare top payouts dominate financial results, and selecting winners",
            "after viewing test data creates multiple-testing bias.",
            "",
            "VAL live bot schedules, prediction board, and ledgers remain unchanged.",
            "Before any serious conclusion, obtain much longer, complete",
            "official-verified chronological Keno history and repeat the analysis.",
            ""]
    return "\n".join(lines)


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-url",default=SOURCE_URL)
    parser.add_argument("--markdown",default="reports/research_keno.md")
    parser.add_argument("--json",default="reports/research_keno.json")
    args=parser.parse_args()
    req=urllib.request.Request(args.source_url,headers={
        "User-Agent":"Mozilla/5.0 (VAL Keno statistics research; informational; no bets)"
    })
    with urllib.request.urlopen(req,timeout=60) as res:
        raw=res.read(4_000_000)
    rows,quality=parse_results(raw.decode("utf-8-sig"))
    result={
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "version":"val_keno_five_spot_real_history_v1",
        "source":{"url":args.source_url,"sha256":hashlib.sha256(raw).hexdigest(),
                  "verified_official":False},
        "coverage":quality,"test":evaluate(rows),
    }
    for dest,body in [(args.markdown,markdown(result)+"\n"),
                      (args.json,json.dumps(result,indent=2)+"\n")]:
        path=Path(dest);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(body)
    print(json.dumps({"coverage":quality,"expected_return":result["test"]["fair_expected_gross_return_per_$1_play"],
                      "random_control":result["test"]["random_control"],
                      "methods":result["test"]["methods"]}),flush=True)
    print("Research-only Keno report saved.")


if __name__=="__main__":run()
