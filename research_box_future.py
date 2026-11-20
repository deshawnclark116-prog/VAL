"""Immutable, pre-draw paper test for VAL's Box evidence challenger.

This is a SHADOW experiment, never production picks or real wagers.
Predictions are appended only before the official sales cutoff. Each target
is forever associated with its originally generated model and random
tickets. Later official results grade those frozen tickets without
refitting or replacing them.

The model's historical investigation has already inspected 2024-2026
data. Consequently, only newly committed future results count as
prospective evidence of advantage; historical activation is NOT proof.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

from research_decades import fetch_full
from research_prospective import earlier, legal_target
from val import ET, draw_schedule
from val_box import box_score_batch, random_box_picks
from val_box_challenger import BoxEvidence, GAMES, LOG_GATE, VERSION

START_DATE = "2024-01-01"  # immutable evidence-origin date, NOT a sliding reset
LEDGER = Path("reports/prospective_box_evidence.json")
SUMMARY = Path("reports/prospective_box_evidence.md")


def seeded_rng(game, target, label):
    raw = "|".join([VERSION, game, target["date"], target["stream"], label])
    seed = int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")
    return random.Random(seed)


def forecast_for(game, target, history):
    """Replay fixed-origin prior history and freeze the next-draw distribution."""
    prior = [r for r in history
             if r["date"] >= START_DATE and earlier(r, target)]
    if len(prior) < 200:
        raise ValueError("Insufficient fixed-origin prior history")
    model = BoxEvidence(game)
    for row in prior:
        model.observe(row)
    name, selected = model.prediction(target["stream"])
    selected_again, picks = model.picks(
        target["stream"], seeded_rng(game, target, "challenger"), count=3)
    if name != selected_again:
        raise AssertionError("Selection changed before drawing")
    control = random_box_picks(
        game, 3, seeded_rng(game, target, "control"))
    return {
        "model_version": VERSION,
        "evidence_start": START_DATE,
        "past_draws": len(prior),
        "latest_training_draw": {
            "date": prior[-1]["date"], "stream": prior[-1]["stream"],
            "numbers": prior[-1]["numbers"]},
        "selected_expert": name,
        "gate_threshold_log": LOG_GATE,
        "log_evidence": {k: round(v, 7) for k, v in model.log_e.items()},
        "selected_joint_forecast": selected,
        "candidate_tickets": [p["numbers"] for p in picks],
        "random_control_tickets": [p["numbers"] for p in control],
    }


def grade(game, frozen, actual):
    """Use the SAVED pre-draw probability and tickets; never retrain."""
    model_picks = [{"numbers": v} for v in frozen["candidate_tickets"]]
    random_picks = [{"numbers": v} for v in frozen["random_control_tickets"]]
    a = box_score_batch(game, model_picks, actual)
    b = box_score_batch(game, random_picks, actual)
    if frozen["selected_joint_forecast"] is None:
        log_gain = 0.
    else:
        p = BoxEvidence.probability(
            frozen["selected_joint_forecast"], actual["numbers"])
        log_gain = math.log(p / (.1 ** int(game[-1])))
    return {
        "model_box_wins": a["box_wins"],
        "random_box_wins": b["box_wins"],
        "model_paper_net_usd": a["box_net_usd"],
        "random_paper_net_usd": b["box_net_usd"],
        "model_fair_expected_box_wins": a["box_fair_expected_wins"],
        "random_fair_expected_box_wins": b["box_fair_expected_wins"],
        "model_log_gain_vs_fair": log_gain,
    }


def most_recent_completed(game, now):
    schedule = [d for d in draw_schedule(game, now)
                if datetime.fromisoformat(d["at"]) <= now]
    if not schedule:
        return None
    last = max(schedule, key=lambda r: r["at"])
    local = datetime.fromisoformat(last["at"]).astimezone(ET)
    return local.date().isoformat(), last["stream"]


def update(game, history, entries, now, require_latest=True):
    if now.tzinfo is None:
        raise ValueError("Timezone-aware now required")
    lookup = {(r["date"], r["stream"]): r for r in history}
    if len(lookup) != len(history):
        raise ValueError("Duplicate or conflicting official results")
    records = [dict(r) for r in entries]
    stats = {"created": 0, "settled": 0, "pending": 0,
             "official_revisions": 0, "withheld": None}
    for record in records:
        key = (record["target"]["date"], record["target"]["stream"])
        actual = lookup.get(key)
        if actual is None:
            if record["result"] is None:
                stats["pending"] += 1
            continue
        if record["result"] is None:
            record["result"] = {
                "official_numbers": list(actual["numbers"]),
                "graded_utc": now.astimezone(timezone.utc).isoformat(),
                "accuracy": grade(game, record["forecast"], actual),
            }
            stats["settled"] += 1
        elif record["result"]["official_numbers"] != actual["numbers"]:
            record["source_revision_warning"] = True
            stats["official_revisions"] += 1

    target = legal_target(game, now)
    if target is None:
        stats["withheld"] = "sales already closed for next draw"
        return records, stats
    target_key = (target["date"], target["stream"])
    if target_key in lookup:
        raise ValueError("Target result already published before prediction")
    if any((r["target"]["date"], r["target"]["stream"]) == target_key
           for r in records):
        return records, stats
    if require_latest:
        last_key = most_recent_completed(game, now)
        if last_key and last_key not in lookup:
            stats["withheld"] = "last completed official drawing not available"
            return records, stats

    snapshot = forecast_for(game, target, history)
    created = now.astimezone(timezone.utc).isoformat()
    if created >= target["wagers_close_utc"]:
        raise AssertionError("Refusing post-cutoff prediction")
    records.append({
        "id": hashlib.sha256(
            (VERSION + game + target["date"] + target["stream"]).encode()
            ).hexdigest()[:20],
        "created_utc": created,
        "target": target,
        "forecast": snapshot,
        "result": None,
    })
    stats["created"] += 1
    stats["pending"] += 1
    return records, stats


def render(data):
    lines = [
        "# VAL Box evidence — immutable FUTURE paper predictions",
        "",
        "This is a separate shadow experiment; the live Box v3 system is unchanged.",
        "Forecasts are saved before each named draw and never retroactively retargeted.",
        "A full Any Order hit requires all digits including repetitions.",
        "**No real wagers or validated live edge are claimed.**",
        "",
        "| Game | Settled draws | Model Box wins | Random Box wins | Model paper net | Random paper net | Prospectively active | Mean log gain |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    details = []
    for game, rows in data["games"].items():
        finished = [r for r in rows if r["result"] is not None]
        model = [r["result"]["accuracy"] for r in finished]
        gains = [m["model_log_gain_vs_fair"] for m in model]
        lines.append(
            f'| {game} | {len(finished)} | '
            f'{sum(x["model_box_wins"] for x in model)} | '
            f'{sum(x["random_box_wins"] for x in model)} | '
            f'${sum(x["model_paper_net_usd"] for x in model)} | '
            f'${sum(x["random_paper_net_usd"] for x in model)} | '
            f'{sum(r["forecast"]["selected_expert"] is not None for r in finished)} | '
            f'{sum(gains)/len(gains) if gains else 0.:+.6f} |'
        )
        for row in rows[-1:]:
            if row["result"] is None:
                f = row["forecast"]
                details += ["",
                            f'Latest frozen {game}: {row["target"]["date"]} '
                            f'{row["target"]["stream"]}; saved {row["created_utc"]}.',
                            f'Model active: {f["selected_expert"] or "No — fair baseline"}; '
                            f'Box tickets: {f["candidate_tickets"]}; '
                            f'controls: {f["random_control_tickets"]}.']
    lines += details
    lines += [
        "", "## Promotion rule", "",
        "Only new subsequent drawings that were unknown when the model was",
        "specified can serve as the final test. Comparison uses equal-cost",
        "random Box tickets and genuine complete-digit outcomes. Apparent",
        "historical signal activation is not counted as prospective evidence.",
        "", "[Frozen records](prospective_box_evidence.json).", "",
    ]
    return "\n".join(lines)


def cycle(now, ledger=LEDGER, summary=SUMMARY):
    data = json.loads(ledger.read_text()) if ledger.exists() else {
        "version": VERSION,
        "created_utc": now.astimezone(timezone.utc).isoformat(),
        "fixed_evidence_start": START_DATE,
        "games": {g: [] for g in GAMES},
    }
    if (data["version"] != VERSION or
            data["fixed_evidence_start"] != START_DATE):
        raise ValueError("Unexpected frozen study parameters")
    status = {}
    for game in GAMES:
        history, metadata = fetch_full(game)
        revised, change = update(game, history, data["games"][game], now)
        data["games"][game] = revised
        status[game] = change
        print(json.dumps({"game": game, "source_draws": len(history),
                          "changes": change}), flush=True)
    data["last_run_utc"] = now.astimezone(timezone.utc).isoformat()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(data, indent=2) + "\n")
    summary.write_text(render(data) + "\n")
    return status


if __name__ == "__main__":
    cycle(datetime.now(timezone.utc))
