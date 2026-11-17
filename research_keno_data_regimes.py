"""Provenance and regime audit for frozen VA Keno history.

Data quality and draw-technology provenance come BEFORE prediction work.
This script never predicts, changes picks, or purchases tickets.
All upgrade and platform date statements are attributed to cited public
sources; a game update does not by itself establish an RNG replacement.
"""
from __future__ import annotations

import gzip
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SOURCE=Path("reports/keno_official_history.json.gz")
JSON_OUT=Path("reports/keno_data_regimes.json")
MD_OUT=Path("reports/keno_data_regimes.md")
UPGRADE_CUTOFF="2026-11-16T01:00:00"
REFERENCES={
    "VA_KENO_START":"https://rga.lis.virginia.gov/Published/2024/RD107/PDF",
    "VA_TRUSTED_DRAW_LAUNCH":"https://publications.world-lotteries.org/blog-posts/szrek2solutions-electronic-draw-solution-launched-by-brightstar-lottery-for-virginia-lottery",
    "VENDOR_TECHNICAL_DESCRIPTION":"https://szrek.com/products/trusted-draw/",
    "VENDOR_INTEGRITY_SYSTEM":"https://szrek.com/products/trusted-audit/",
    "VA_DRAWING_UPDATE":"https://www.valottery.com/",
    "VA_KENO_PUBLIC_GAME":"https://www.valottery.com/en/data/draw-games/keno",
}


def analyze(rows):
    if not rows:
        raise ValueError("No archived draws")
    ids=[r["draw_id"] for r in rows]
    if ids!=sorted(set(ids)):
        raise ValueError("Archive draw IDs must be sorted and unique")
    times=[r["timestamp"] for r in rows]
    if times!=sorted(times):
        raise ValueError("Archive timestamps are not chronological")
    for row in rows:
        nums=row["numbers"]
        if len(nums)!=20 or len(set(nums))!=20:
            raise ValueError("Not a valid 20-number Keno drawing")
    day=Counter(r["date"] for r in rows)
    before=[r for r in rows if r["timestamp"]<UPGRADE_CUTOFF]
    after=[r for r in rows if r["timestamp"]>=UPGRADE_CUTOFF]
    missing=sum(max(0,b-a-1) for a,b in zip(ids,ids[1:]))
    by_gap=[dict(previous_id=a,next_id=b,missing=b-a-1)
            for a,b in zip(ids,ids[1:]) if b-a>1]
    bonus_before=sum(r.get("bullseye") is not None for r in before)
    bonus_after=sum(r.get("bullseye") is not None for r in after)
    return {
        "version":"val_keno_history_lineage_v1",
        "official_api_archive_file":str(SOURCE),
        "archive_draws":len(rows),
        "first_draw":dict(draw_id=rows[0]["draw_id"],timestamp=times[0]),
        "last_draw":dict(draw_id=rows[-1]["draw_id"],timestamp=times[-1]),
        "archive_calendar_days":len(day),
        "daily_counts":dict(sorted(day.items())),
        "missing_draw_ids":missing,
        "draw_id_gaps":by_gap,
        "known_documented_events":[
            {"event":"Original Virginia Keno rollout", "period":"2020-08",
             "confidence":"Virginia Lottery financial report (primary)" },
            {"event":"Trusted Draw RNG deployment public announcement",
             "period":"2026-02", "confidence":"Vendor press release published March 4, 2026; exact go-live date not established"},
            {"event":"Lottery announced drawing unavailability for an update",
             "period":UPGRADE_CUTOFF,
             "confidence":"Official Lottery announcement; does NOT establish RNG replacement"}
        ],
        "segments":{
            "before_announced_nov16_2026_update":{
                "count":len(before),
                "first":None if not before else before[0]["timestamp"],
                "last":None if not before else before[-1]["timestamp"],
                "bullseye_non_null":bonus_before},
            "on_or_after_announced_nov16_2026_update":{
                "count":len(after),
                "first":None if not after else after[0]["timestamp"],
                "last":None if not after else after[-1]["timestamp"],
                "bullseye_non_null":bonus_after}
        },
        "raw_number_order_lost_in_archive":True,
        "number_order_warning":"Ingestion normalize() calls sorted(nums), so archived number order cannot support an output-order analysis; raw field semantics were not independently verified.",
        "source_limitations":[
            "About one month of archived draws, despite Keno being offered since August 2020.",
            "Older historical records have NOT yet been recovered or verified.",
            "Exact Virginia deployment timestamp for Trusted Draw NOT verified.",
            "The November 16, 2026 Lottery software/drawing update is known; its effect on RNG internals is NOT established.",
            "The source's time-zone handling and system processing gaps need explicit validation before regime-boundary inference.",
            "No internal RNG seed, hardware logs, or auditable draw proofs exist in this archived JSON.",
            "Vendor claims about audit integrity are not independently tested here.",
        ],
        "sources":REFERENCES,
    }


def report(x):
    p=x["segments"]["before_announced_nov16_2026_update"]
    q=x["segments"]["on_or_after_announced_nov16_2026_update"]
    lines=[
        "# VA Keno data-provenance and RNG-regime audit",
        "",
        "## Confirmed public facts",
        "",
        "- Virginia Lottery's published history records the launch of Keno in August **2020**.",
        "- Szrek2Solutions and Brightstar announced deployment of the **Trusted Draw**",
        "  electronic RNG platform for Virginia Keno and Cash Pop in February **2026**.",
        "  The exact start date for Virginia Keno is **not verified**.",
        "- Szrek's public technical documentation describes RNG seeds formed from",
        "  hardware-protected digital signatures, with independent draw-audit proofs.",
        "  These are **vendor statements**, not a firsthand inspection of Virginia's implementation.",
        "- Virginia Lottery posted that Keno drawings would be unavailable starting",
        "  **1 a.m. Nov. 16, 2026** during an update, resuming afterward.",
        "  **We cannot conclude this update replaced or modified the RNG.**",
        "",
        "## What our actual archived source contains",
        "",
        "| Metric | Observed |",
        "| --- | ---: |",
        "| Archived official draws | "+format(x["archive_draws"],",")+" |",
        "| Calendar days represented | "+format(x["archive_calendar_days"],",")+" |",
        "| Earliest timestamp | "+x["first_draw"]["timestamp"]+" |",
        "| Latest timestamp | "+x["last_draw"]["timestamp"]+" |",
        "| Missing draw IDs | "+str(x["missing_draw_ids"])+" |",
        "| Rows before Nov. 16 01:00 cutoff | "+str(p["count"])+" |",
        "| Rows on/after cutoff | "+str(q["count"])+" |",
        "| Non-null Bullseye values before cutoff | "+str(p["bullseye_non_null"])+" |",
        "| Non-null Bullseye values on/after cutoff | "+str(q["bullseye_non_null"])+" |",
        "",
        "## Consequences for VAL modeling",
        "",
        "1. We have not trained on five years of Keno history; we have approximately",
        "   a month. Claims of exhausting all learnable historical information are not justified.",
        "2. Do not automatically combine different eras of a draw generator into",
        "   the same stationarity assumption; changes must be documented and tested.",
        "3. Preserve raw source payloads and reported number order on ingestion.",
        "   The existing pipeline SORTS every winning 20-number list, so potential",
        "   as-reported ordering information is permanently absent from this archive.",
        "   We do NOT yet know whether the API preserved true generation order.",
        "4. The reported platform uses digital-signature-derived RNG seeds inside",
        "   certified hardware. A purely historical number-frequency model does",
        "   not reveal protected seed material; any exploitable statistical",
        "   hypothesis requires independently reproducible evidence.",
        "5. For research quality, first obtain a verified longer, consistent",
        "   historical archive and test actual change points; then lock a",
        "   prospective prediction model with audit trails and random controls.",
        "6. Maintain clear distinctions among **game rule change**,",
        "   **drawing system maintenance**, and **confirmed RNG implementation change**.",
        "",
        "## Source links",
        "",
    ]
    for k,v in x["sources"].items():
        lines.append("- "+k+": "+v)
    lines+=["",
        "Automatically generated from the frozen official archive.",
        "No money spent, no real wagers or modifications to production predictions.",
        ""
    ]
    return "\n".join(lines)


def main():
    with gzip.open(SOURCE,"rt",encoding="utf-8") as f:
        rows=json.load(f)
    data=analyze(rows)
    data["generated_utc"]=datetime.now(timezone.utc).isoformat()
    JSON_OUT.write_text(json.dumps(data,indent=2)+"\n")
    MD_OUT.write_text(report(data)+"\n")
    print(json.dumps({k:data[k] for k in
          ("archive_draws","archive_calendar_days","missing_draw_ids","segments")},indent=2),flush=True)


if __name__=="__main__":
    main()
