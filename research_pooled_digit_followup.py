"""Independent follow-up of VAL v3's pooled-digit accuracy lead.

This hypothesis was selected after looking at the 2025-26 v3 results and
is exploratory across the *entire historical archive*. Do not promote from
this test. It replays ONE formula with strictly earlier rolling 5,000-draw
counts, with fixed prior 200 * game_width per digit, and publishes year and
Day/Night breakdowns with sample-size-aware estimates. The frozen
prospective study is required to prove anything in future.
"""
from __future__ import annotations
import json
import math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

from val import ET,GAMES
from research_10k import load_official_history

GAMES_TEST=("pick3","pick4","pick5")
WINDOW=5000
PRIOR_PER_POSITION=200.
MIN_TRAIN=500
JSON_OUT=Path("reports/research_pooled_digit_followup.json")
MD_OUT=Path("reports/research_pooled_digit_followup.md")


def probabilities(counts,width):
    pseudo=PRIOR_PER_POSITION*width+1.
    denom=sum(counts)+10*pseudo
    return [(c+pseudo)/denom for c in counts]


def evaluate(game,rows):
    width=GAMES[game]["size"]
    if len(rows)<MIN_TRAIN+300:raise ValueError("Too few draws")
    count=[0]*10
    metrics=defaultdict(lambda:{"draws":0,"positions":0,"first":0,"top3":0,
                                 "exact":0,"log_gain":0.,"days":set()})
    for i,row in enumerate(rows):
        if i>=MIN_TRAIN:
            p=probabilities(count,width)
            rank=sorted(range(10),key=lambda d:(-p[d],d))
            winner=row["numbers"]
            local=datetime.fromisoformat(row["at"]).astimezone(ET)
            day=local.date().isoformat()
            # Each fixed target contributes to each relevant partition.
            keys=["all","year_"+str(local.year),"stream_"+row["stream"]]
            if local.year>=2025:
                keys+=["recent_"+row["stream"],"recent"]
            if local.year>=2026:
                keys+=["2026_"+row["stream"]]
            h1=sum(d==rank[0] for d in winner)
            h3=sum(d in rank[:3] for d in winner)
            lr=sum(math.log(p[d]*10) for d in winner)
            exact=int(all(d==rank[0] for d in winner))
            for key in keys:
                m=metrics[key]
                m["draws"]+=1
                m["positions"]+=width
                m["first"]+=h1
                m["top3"]+=h3
                m["exact"]+=exact
                m["log_gain"]+=lr
                m["days"].add(day)
        # The observed current draw enters history ONLY after its evaluation.
        for d in row["numbers"]:
            count[d]+=1
        if i>=WINDOW:
            for d in rows[i-WINDOW]["numbers"]:
                count[d]-=1
        if any(c<0 for c in count):raise AssertionError("Negative rolling count")
        if i%10000==0 and i>0:
            print(game,"rolling draws",i,"of",len(rows),flush=True)
    results={}
    for name,s in metrics.items():
        n=s["positions"];rate=s["first"]/n
        se=math.sqrt(.1*.9/n)
        z=(s["first"]-.1*n)/math.sqrt(.1*.9*n)
        results[name]={
            "draws":s["draws"],"calendar_days":len(s["days"]),
            "positions":n,"top1_hits":s["first"],
            "top1_rate":rate,
            "top1_95pct_normal_interval":[rate-1.96*se,rate+1.96*se],
            "chance_expected_top1":.1*n,
            "top1_z_vs_fair":z,
            "approx_one_sided_p":.5*math.erfc(z/math.sqrt(2)),
            "top3_hits":s["top3"],"top3_rate":s["top3"]/n,
            "chance_expected_top3_rate":.3,
            "full_exact_hits":s["exact"],
            "chance_expected_exact":s["draws"]/(10**width),
            "mean_log_gain_vs_fair":s["log_gain"]/s["draws"]
        }
    return {"game":game,"history_draws":len(rows),
            "first_draw":rows[0]["at"],"latest_draw":rows[-1]["at"],
            "formula":"rolling pooled digit probabilities with 5,000 draws; 200 pseudo observations per position per digit",
            "exploratory_selected_after_v3_results":True,
            "results":results}


def render(j):
    lines=[
        "# VAL pooled-digit candidate: year/session robustness audit",
        "",
        "**This candidate was identified after inspecting historical data.**",
        "The results are exploratory and cannot establish a new edge.",
        "The exact same formula was replayed through all available years",
        "without seeing each target draw until after its prediction.",
        "The 5,000-draw rolling window and 200-per-position digit prior",
        "were held fixed throughout.",
        "",
        "Fair chance for the top selected digit in any specified position",
        "is 10%. A full Straight win requires the entire ordered result;",
        "position hits alone are not prizes.",
        "",
        "| Game | Period | Draws | Top-1 hit rate | Top-3 coverage | Mean log gain vs fair | Exact winners |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |"
    ]
    for game,x in j["games"].items():
        labels=("all","year_2023","year_2024","year_2025","year_2026",
                "stream_Day","stream_Night","recent_Day","recent_Night",
                "2026_Day","2026_Night")
        for label in labels:
            if label not in x["results"]:continue
            v=x["results"][label]
            lines.append("| "+game+" | "+label+" | "+str(v["draws"])+" | "+
                f'{100*v["top1_rate"]:.2f}%'+ " | "+
                f'{100*v["top3_rate"]:.2f}%'+ " | "+
                f'{v["mean_log_gain_vs_fair"]:+.6f}'+" | "+
                str(v["full_exact_hits"])+" |")
    lines+=["","## Decision","",
            "No favorable row is grounds for promotion; the model was",
            "chosen after other VAL backtests had been inspected. A real",
            "test is an immutable forecast ledger covering every future",
            "drawing with its saved prediction, fair odds and controls.",
            "",
            "[Raw period-level results](research_pooled_digit_followup.json).",""]
    return "\n".join(lines)


def main():
    report={"version":"pooled_digit_postselection_audit_v1",
            "generated_utc":datetime.now(timezone.utc).isoformat(),
            "selected_after_prior_research":True,
            "no_model_promotion":True,"games":{}}
    for game in GAMES_TEST:
        rows=load_official_history(game)
        report["games"][game]=evaluate(game,rows)
        print(game,json.dumps({
            k:{m:round(v,6) if isinstance(v,float) else v
               for m,v in s.items() if m in ("draws","top1_rate","mean_log_gain_vs_fair")}
            for k,s in report["games"][game]["results"].items()
            if k in ("year_2025","year_2026","recent_Day","recent_Night")}),flush=True)
    JSON_OUT.parent.mkdir(parents=True,exist_ok=True)
    JSON_OUT.write_text(json.dumps(report,indent=2)+"\n")
    MD_OUT.write_text(render(report)+"\n")


if __name__=="__main__":main()
