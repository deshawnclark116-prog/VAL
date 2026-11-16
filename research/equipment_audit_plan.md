# VAL equipment and pretest investigation
Research status: November 15, 2026. Exploratory; no predictive edge established.

## Why this investigation exists
A leak-free audit of 49,286 official Pick 3/4/5 results and 161 broad randomness checks found zero deviations that survived multiple-test correction. Rolling 100/500-draw historical forecasting scored worse than uniform odds. Data-only lottery-frequency methods have no demonstrated edge, so the only new defensible line of investigation is whether documented physical drawing conditions predict anything out of sample.

## Source-verified evidence
- Official drawing security page: https://www.valottery.com/playingmatters/security
  - Lottery says drawing officials randomly select machine and ball sets, perform pretest draws, and record their actions in a drawing master control form.
  - That form is said to include equipment used, pretest numbers, official numbers, and closing time for wagers.
  - The published page refers to *evening* selection; this does not independently establish identical procedures for every game's Day/Night drawing.
  - The page does not provide a searchable historical master-control-form dataset or confirm that equipment selections/pretest outcomes are publicly disclosed **before sales close**.
- Official Lottery FOIA portal: https://www.valottery.com/foiarequest
  - Public records request email: publicrecords@valottery.com.
  - Agency requires the requester's name and physical address, warns of possible search charges, and accepts cost-estimate requests.
  - FOIA requests seek **existing records**, not a newly prepared analysis or answers.
- Historical corroboration (NOT a claim about current procedures): June 1998 WDBJ coverage of machine/ball selection, auditing, and ball weighing. https://scholar.lib.vt.edu/VA-news/WDBJ-7/script_archives/98/0698/060398/060398.11.htm
- Virginia Lottery digit game sales close 1:53 p.m. for Day, 10:45 p.m. ET for Night. See https://www.valottery.com/data/draw-games/pick5.

## Important limitations
1. If particular machines have different underlying biases but their identities are random and unavailable **before** the relevant bet deadline, that association is not an actionable pre-draw signal.
2. Equipment usage alone does not establish physical bias or predictive value. No allegation of misconduct is justified.
3. Pretest numbers may simply be independent random samples. Historical associations need much stronger validation than a retrospective apparent correlation.
4. Requesting records does not guarantee availability, disclosure, retention, or affordable search costs.
5. Avoid treating event draw-time, form-completion time, or post-draw public upload time as if the information was known before purchase.

## Narrow first records request — draft only (NOT SENT)
To: publicrecords@valottery.com
Subject: Virginia FOIA request — Pick 3/4/5 drawing control and pretest records, October 1–14, 2026

I am requesting electronic copies of the following existing Virginia Lottery records under the Virginia Freedom of Information Act:

1. Drawing Master Control Forms, pre-draw test logs or the equivalent record documenting each Pick 3, Pick 4, and Pick 5 Day and Night drawing from October 1 through October 14, 2026, inclusive. Please include, where recorded, the machine/ball-set identifiers, any identifier per digit position or chamber, pretest outcomes, substitute equipment, official drawn numbers and draw time. I am seeking the existing records, not a new report.
2. Written drawing procedures effective during that period for the selection and testing of machines and ball sets, including documentation of substitutions or failed pretests.
3. If an existing spreadsheet/database/export already holds equipment IDs, ball-set identifiers, pretest results and official outcomes indexed by draw, please identify the readily available existing record format and retention period. I am interested in a longer historical series, but please do not begin a large extraction without providing a cost estimate.

Please provide the records electronically in their existing format where possible. Before incurring charges, please send an itemized estimate and obtain my approval. I would appreciate any reasonably segregable portions if some content is withheld and the statutory basis for any redactions.

Thank you.

[Requester name and physical address required by Virginia Lottery; intentionally omitted from repository]

## Optional second request to clean historical data
Official Pick 3 downloadable archive has conflicting published Night outcomes for:
- 2008-10-30: 649 and 867;
- 2008-11-09: 374 and 492.
The VAL decades audit quarantines both records rather than selecting one. Request surviving master forms, historical correction logs, or official adjudications for those dates if archived.

## Planned ingestion fields (not asserted to exist in all records)
`game, draw_date, session, official_digits, fireball, machine_id, ball_set_id_by_position, pretest_draw_id, pretest_digits, selected_at, selection_publication_time, wager_close_at, source_file, source_hash, record_quality, correction_log`.

## Preregistered evaluation before reviewing supplied data
- Validate source rows and equipment IDs against public official results, track revisions and missing fields.
- Separate eras and game changes; do not pool positions or hardware setups casually.
- Test per-machine and per-ball-set conditional deviations using shrinkage, minimum samples, and family-wise error control.
- Compare pretest frequency against expected fair variation; do not promote pretest patterns to forecasts from historical coincidence.
- Enforce strict time availability: a predictor may only use variables known before wager close.
- Split earlier equipment periods for research and later genuinely untouched periods for confirmation, then prospectively log all future predictions.
- Compare against fixed uniform baseline (10% probability per digit per position) and random ticket controls.
- Never describe sample pretest anomalies as evidence of fraud, manipulation, or guaranteed profit.

## Decision gate
Promote only if a frozen, preregistered machine-conditional model demonstrably improves forecast log score and target-draw outcomes on untouched later data, including costs and complete uncertainty. If machine IDs cannot be known before sale cutoff, at most publish a retrospective scientific audit, not a ticket-selection method.