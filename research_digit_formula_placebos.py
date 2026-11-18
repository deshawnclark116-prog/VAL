"""Audit unusually lucky random controls in VAL formula research.

The fixed original random control showed three Pick 4 exact wins in only
220 tested draw targets: rare under an iid fair null. Rather than calling
this a model signal, regenerate 500 INDEPENDENT predeclared random controls
against the SAME complete official target list, inspect the distribution,
and compare to the exact binomial tail. Different salts are placebos, not
candidate models; they are NEVER selected for production.
"""
from __future__ import annotations
import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_10k import load_official_history
from val import GAMES,score_batch

INPUT=Path("reports/research_digit_formula_v2.json")
JSON_OUT=Path("reports/research_digit_formula_placebos.json")
MD_OUT=Path("reports/research_digit_formula_placebos.md")
SEEDS=500


def rng_for(game,target,salt):
    payload=f"VAL_null_audit_v1|{game}|{target}|{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:8],"big"))


def fair_tickets(game,target,salt,count=3):
    width=GAMES[game]["size"]
    rand=rng_for(game,target,salt)
    picked=[]; seen=set()
    while len(picked)<count:
        combo=tuple(rand.randrange(10) for _ in range(width))
        if combo not in seen:
            seen.add(combo)
            picked.append(dict(numbers=list(combo),bonus=None))
    return picked


def exact_tail(n,p,observed):
    if observed<=0:return 1.
    return sum(math.comb(n,k)*(p**k)*((1-p)**(n-k))
               for k in range(observed,n+1))


def analyze(game,records,history,seeds=SEEDS):
    # Only the original study's SAME pre-chosen target dates.
    by_at={row["at"]:row for row in history}
    stamps=[r["at"] for r in records]
    if len(set(stamps))!=len(stamps):
        raise ValueError("Repeated target in original comparison")
    try: actuals=[by_at[stamp] for stamp in stamps]
    except KeyError as exc:raise ValueError("Official archive changed target timestamps") from exc
    observed=sum(r["uniform_control"]["exact"] for r in records)
    count_per_target=len(records[0]["uniform_control"]["tickets"])
    if count_per_target!=3:raise ValueError("Expected precisely three controls")
    null_counts=[]
    null_position_hits=[]
    for salt in range(seeds):
        exact=matched=0
        for target in actuals:
            tickets=fair_tickets(game,target["at"],salt,3)
            result=score_batch(game,tickets,target)
            exact+=result["exact"]
            matched+=result["total_matches"]
        null_counts.append(exact)
        null_position_hits.append(matched)
    width=GAMES[game]["size"]
    fair_p=3/(10**width)
    result={
        "game":game,"targets":len(records),"tickets_per_target":3,
        "observed_original_control_straight_wins":observed,
        "fair_expected_wins":len(records)*fair_p,
        "exact_binomial_tail_one_control":exact_tail(len(records),fair_p,observed),
        "replicate_count":seeds,
        "mean_independent_control_wins":sum(null_counts)/seeds,
        "max_independent_control_wins":max(null_counts),
        "fraction_replications_at_least_original":sum(x>=observed for x in null_counts)/seeds,
        "replicate_exact_win_histogram":dict(sorted(Counter(null_counts).items())),
        "mean_control_position_hit_rate":
            sum(null_position_hits)/(seeds*len(records)*3*width),
        "original_control_position_hit_rate":
            sum(r["uniform_control"]["position_matches"] for r in records)/
            (len(records)*3*width),
    }
    return result


def summary(report):
    lines=[
        "# VAL v2 — random-control jackpot anomaly audit",
        "",
        "The fixed head-to-head replay produced unusually high Pick 4 exact",
        "winners for one deterministic random control. That is a rare",
        "multiple-testing hazard, **not** evidence the timestamp seed",
        "predicts a fair lottery. We replicated 500 *independent* random",
        "controls against the identical pre-selected target drawings.",
        "No seed is selected for live bets; this audit only measures the null.",
        "",
        "| Game | Target draws | Original control wins | Fair expected wins | Exact fair-tail P(>= observed) | 500-control average wins |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"
    ]
    for game,x in report["games"].items():
        lines.append("| "+game+" | "+str(x["targets"])+" | "+
          str(x["observed_original_control_straight_wins"])+" | "+
          format(x["fair_expected_wins"],".3f")+" | "+
          format(x["exact_binomial_tail_one_control"],".6g")+" | "+
          format(x["mean_independent_control_wins"],".3f")+" |")
    lines+=["","Each single-control fair tail assumes truly independent",
             "uniform draws and unique three-ticket selections. The original",
             "control seed was just one of many models, games, experiments and",
             "comparisons inspected, so its one-shot p-value does NOT establish",
             "predictive power. Multiple-testing adjustment and future",
             "precommitted replication are required.",
             "",
             "Raw results: [research_digit_formula_placebos.json](research_digit_formula_placebos.json).",
             ""]
    return "\n".join(lines)


def main():
    study=json.loads(INPUT.read_text())
    result={"version":"val_formula_placebo_null_audit_v1",
            "created_at":datetime.now(timezone.utc).isoformat(),
            "seed_count":SEEDS,
            "no_model_promotion":True,"games":{}}
    for game,g in study["games"].items():
        history=load_official_history(game)
        result["games"][game]=analyze(game,g["test_targets"],history)
        print(game,json.dumps(result["games"][game]),flush=True)
    JSON_OUT.parent.mkdir(parents=True,exist_ok=True)
    JSON_OUT.write_text(json.dumps(result,indent=2)+"\n")
    MD_OUT.write_text(summary(result)+"\n")

if __name__=="__main__":main()
