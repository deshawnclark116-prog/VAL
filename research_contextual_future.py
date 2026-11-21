"""Immutable prospective real-world trial for VAL's contextual Box engine.

All candidates are calculated from ONLY earlier official results and frozen
before the named drawing and wager cutoff. Real external equipment/pretest
inputs require independently verified, timestamped pre-wager sources. None
are currently wired in; no artificial simulator IDs are ever inserted here.
The old v4 live production predictions are never modified.

This creates no bets; the outcome is a paper full Any Order win only.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime,timezone
from pathlib import Path

from research_prospective import legal_target, earlier
from research_prospective_pooled_box_v2 import load_fresh_official_history
from val_contextual_regime_box import ContextualBox,VERSION,GAMES
from val_box import box_score_batch, digits_key,box_ways, random_box_picks

LEDGER=Path("reports/prospective_contextual_box_v1.json")
REPORT=Path("reports/prospective_contextual_box_v1.md")
MODEL_DRAWS=2400


def seeded(*parts):
    raw="|".join(map(str,(VERSION,)+parts)).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8],"big"))


def frozen_forecast(game,target,official_history):
    if game not in GAMES or target["game"]!=game:
        raise ValueError("Incorrect target game")
    past=sorted((row for row in official_history if earlier(row,target)),
                key=lambda row:(row["date"],
                    0 if row["stream"]=="Day" else 1))
    if len(past)<600:
        raise ValueError("Insufficient verified earlier drawing history")
    engine=ContextualBox(game)
    for row in past[-MODEL_DRAWS:]:
        historical=dict(date=row["date"],stream=row["stream"])
        frozen=engine.forecast(historical)
        engine.observe(historical,row["numbers"],frozen)
    target_context=dict(date=target["date"],stream=target["stream"],
                        wagers_close_utc=target["wagers_close_utc"])
    frozen=engine.forecast(target_context)
    portfolio=engine.choose(frozen,3)
    controls=[x["numbers"] for x in random_box_picks(
        game,3,seeded(game,target["date"],target["stream"],"control"))]
    if frozen["eligible_features"]:
        # Feature sources must be specifically verified and wired in here
        # before calling anything available to real pre-wager users.
        raise AssertionError("No authorized real-world external feed")
    return dict(version=VERSION,trained_previous=len(past),
                training_latest_date=past[-1]["date"],
                training_latest_session=past[-1]["stream"],
                prepared_joint_model=frozen,
                candidate_tickets=portfolio["picks"],
                random_control_tickets=controls,
                predicted_full_box_probability=(
                    portfolio["predicted_full_box_probability"]),
                model_fair_full_box_probability=(
                    portfolio["fair_full_box_probability"]),
                control_fair_full_box_probability=sum(
                    box_ways(t) for t in controls)/10**int(game[-1]))


def settle(game,frozen,outcome):
    target=outcome["numbers"]
    model=box_score_batch(game,[
        dict(numbers=x) for x in frozen["candidate_tickets"]],outcome)
    control=box_score_batch(game,[
        dict(numbers=x) for x in frozen["random_control_tickets"]],outcome)
    model_snapshot=frozen["prepared_joint_model"]
    weights=model_snapshot["weights"]
    mixture=sum(weight*math.prod(
        matrix[i][d] for i,d in enumerate(target))
        for name,weight in weights.items()
        for matrix in (model_snapshot["models"][name],))
    gain=math.log(mixture/(.1**int(game[-1])))
    return dict(model_full_box_wins=model["box_wins"],
                random_full_box_wins=control["box_wins"],
                model_paper_net_usd=model["box_net_usd"],
                random_paper_net_usd=control["box_net_usd"],
                proper_joint_log_gain_vs_fair=gain)


def update(game,rows,records,now):
    if now.tzinfo is None:
        raise ValueError("Timestamp must be timezone aware")
    official={(r["date"],r["stream"]):r for r in rows}
    if len(official)!=len(rows):
        raise ValueError("Contradictory official drawing archive")
    history=[dict(x) for x in records]
    counts=dict(created=0,graded=0,pending=0,source_revision_warnings=0,
                withheld=None)
    for row in history:
        key=(row["target"]["date"],row["target"]["stream"])
        actual=official.get(key)
        if actual is not None and row["result"] is None:
            row["result"]=dict(
                official_numbers=list(actual["numbers"]),
                settlement_utc=now.astimezone(timezone.utc).isoformat(),
                stats=settle(game,row["forecast"],actual))
            counts["graded"]+=1
        elif actual is not None and row["result"]["official_numbers"]!=actual["numbers"]:
            row["source_revision_warning"]=True
            counts["source_revision_warnings"]+=1
        if row["result"] is None:
            counts["pending"]+=1

    target=legal_target(game,now)
    if target is None:
        counts["withheld"]="No drawing available before wager cutoff"
        return history,counts
    target_key=(target["date"],target["stream"])
    if target_key in official:
        raise ValueError("Refusing to predict a result already available")
    if any((r["target"]["date"],r["target"]["stream"])==target_key
           for r in history):
        return history,counts
    frozen=frozen_forecast(game,target,rows)
    created=now.astimezone(timezone.utc).isoformat()
    if created>=target["wagers_close_utc"]:
        raise AssertionError("Forecast not frozen before wager close")
    history.append(dict(
        id=hashlib.sha256((VERSION+game+target["date"]+
                           target["stream"]).encode()).hexdigest()[:20],
        created_utc=created,target=target,forecast=frozen,result=None))
    counts["created"]+=1
    counts["pending"]+=1
    return history,counts


def audit(game,rows):
    seen=set()
    for item in rows:
        target=item["target"]
        key=(target["date"],target["stream"])
        if key in seen:
            raise ValueError("Same target was forecast twice")
        seen.add(key)
        if target["game"]!=game:
            raise ValueError("Wrong game in immutable record")
        if datetime.fromisoformat(item["created_utc"])>=datetime.fromisoformat(
                target["wagers_close_utc"]):
            raise ValueError("Late prediction in saved ledger")
        f=item["forecast"]
        if f["version"]!=VERSION:
            raise ValueError("Forecast source version mismatch")
        if f["prepared_joint_model"]["eligible_features"]:
            raise ValueError("Unverified equipment source used")
        if f["training_latest_date"]>target["date"]:
            raise ValueError("Future training observation")
        if (f["training_latest_date"]==target["date"] and
            (target["stream"]!="Night" or
             f["training_latest_session"]!="Day")):
            raise ValueError("Same-target training leak")
        model=f["candidate_tickets"]
        controls=f["random_control_tickets"]
        for picks in (model,controls):
            if len(picks)!=3 or len({digits_key(p) for p in picks})!=3:
                raise ValueError("Three distinct complete Box tickets required")
        if item["result"] is not None:
            official=dict(numbers=item["result"]["official_numbers"])
            expected=settle(game,f,official)
            for k in expected:
                if abs(expected[k]-item["result"]["stats"][k])>1e-11:
                    raise ValueError("Incorrect historical frozen grading")
    return True


def display(registry):
    text=[
        "# VAL contextual Box v1 — frozen future drawing predictions",
        "",
        "Research trial; live digit_box_v4 unchanged.",
        "The experiment uses live official earlier results and observed",
        "session/date context. No equipment/pretest feed is connected.",
        "Each forecast is saved before its wager closing time.",
        "Three separate complete ANY ORDER multisets per game;",
        "partial digit or position matches are never scored as hits.",
        "",
        "| Game | Actual future draws graded | New complete Box wins | Fair random complete Box wins | Proper mean full-outcome log gain |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for game,records in registry["games"].items():
        scored=[r["result"]["stats"] for r in records if r["result"]]
        text.append(f'| {game} | {len(scored)} | '
                    f'{sum(x["model_full_box_wins"] for x in scored)} | '
                    f'{sum(x["random_full_box_wins"] for x in scored)} | '
                    f'{sum(x["proper_joint_log_gain_vs_fair"] for x in scored)/len(scored) if scored else 0:+.6f} |')
        for r in records[-1:]:
            if r["result"] is None:
                text.append(
                    f'\nFrozen {game} {r["target"]["date"]} '
                    f'{r["target"]["stream"]} at {r["created_utc"]}: '
                    f'{r["forecast"]["candidate_tickets"]} '
                    f'(controls {r["forecast"]["random_control_tickets"]})')
    text.extend([
        "",
        "These predictions cannot be retroactively rewritten;",
        "only new future official results settle the previously frozen",
        "targets. Research-only, not betting advice.",
        "",
        "[Immutable JSON predictions](prospective_contextual_box_v1.json).",""
    ])
    return "\n".join(text)


def cycle(now,ledger=LEDGER,report=REPORT):
    data=json.loads(ledger.read_text()) if ledger.exists() else dict(
        version=VERSION,created_utc=now.astimezone(timezone.utc).isoformat(),
        games={g:[] for g in GAMES})
    if data["version"]!=VERSION:
        raise ValueError("Prospective version mismatch")
    for game in GAMES:
        rows,metadata=load_fresh_official_history(game,now)
        updated,state=update(game,rows,data["games"][game],now)
        audit(game,updated)
        data["games"][game]=updated
        print("FUTURE",game,state,"official",len(rows),flush=True)
    data["last_run_utc"]=now.astimezone(timezone.utc).isoformat()
    ledger.parent.mkdir(parents=True,exist_ok=True)
    ledger.write_text(json.dumps(data,indent=2)+"\n")
    report.write_text(display(data)+"\n")


if __name__=="__main__":
    cycle(datetime.now(timezone.utc))
