# VA Keno data-provenance and RNG-regime audit

## Confirmed public facts

- Virginia Lottery's published history records the launch of Keno in August **2020**.
- Szrek2Solutions and Brightstar announced deployment of the **Trusted Draw**
  electronic RNG platform for Virginia Keno and Cash Pop in February **2026**.
  The exact start date for Virginia Keno is **not verified**.
- Szrek's public technical documentation describes RNG seeds formed from
  hardware-protected digital signatures, with independent draw-audit proofs.
  These are **vendor statements**, not a firsthand inspection of Virginia's implementation.
- Virginia Lottery posted that Keno drawings would be unavailable starting
  **1 a.m. Nov. 16, 2026** during an update, resuming afterward.
  **We cannot conclude this update replaced or modified the RNG.**

## What our actual archived source contains

| Metric | Observed |
| --- | ---: |
| Archived official draws | 10,665 |
| Calendar days represented | 31 |
| Earliest timestamp | 2026-10-17T00:02:00 |
| Latest timestamp | 2026-11-16T09:45:30 |
| Missing draw IDs | 6 |
| Rows before Nov. 16 01:00 cutoff | 10568 |
| Rows on/after cutoff | 97 |
| Non-null Bullseye values before cutoff | 0 |
| Non-null Bullseye values on/after cutoff | 92 |

## Consequences for VAL modeling

1. We have not trained on five years of Keno history; we have approximately
   a month. Claims of exhausting all learnable historical information are not justified.
2. Do not automatically combine different eras of a draw generator into
   the same stationarity assumption; changes must be documented and tested.
3. Preserve raw source payloads and reported number order on ingestion.
   The existing pipeline SORTS every winning 20-number list, so potential
   as-reported ordering information is permanently absent from this archive.
   We do NOT yet know whether the API preserved true generation order.
4. The reported platform uses digital-signature-derived RNG seeds inside
   certified hardware. A purely historical number-frequency model does
   not reveal protected seed material; any exploitable statistical
   hypothesis requires independently reproducible evidence.
5. For research quality, first obtain a verified longer, consistent
   historical archive and test actual change points; then lock a
   prospective prediction model with audit trails and random controls.
6. Maintain clear distinctions among **game rule change**,
   **drawing system maintenance**, and **confirmed RNG implementation change**.

## Source links

- VA_KENO_START: https://rga.lis.virginia.gov/Published/2024/RD107/PDF
- VA_TRUSTED_DRAW_LAUNCH: https://publications.world-lotteries.org/blog-posts/szrek2solutions-electronic-draw-solution-launched-by-brightstar-lottery-for-virginia-lottery
- VENDOR_TECHNICAL_DESCRIPTION: https://szrek.com/products/trusted-draw/
- VENDOR_INTEGRITY_SYSTEM: https://szrek.com/products/trusted-audit/
- VA_DRAWING_UPDATE: https://www.valottery.com/
- VA_KENO_PUBLIC_GAME: https://www.valottery.com/en/data/draw-games/keno

Automatically generated from the frozen official archive.
No money spent, no real wagers or modifications to production predictions.

