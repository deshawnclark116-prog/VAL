# VAL full-history randomness and prediction audit

Generated (UTC): 2026-11-15T23:54:59.519865+00:00

**Important:** This expands the *research* archives only. VAL's live
April 2025 historical cutoff, generated tickets, and prediction ledger
were not changed. All official downloads may contain manually entered errors.

## Archive coverage

| Game | First available draw | Latest draw | Drawings | Year range | Days | Nights | FIREBALL-bearing |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| pick3 | 1989-05-22 | 2026-11-14 | 23,751 | 1989–2026 | 10,988 | 12,763 | 4,044 |
| pick4 | 1991-09-30 | 2026-11-14 | 23,017 | 1991–2026 | 10,988 | 12,029 | 4,044 |
| pick5 | 2023-06-05 | 2026-11-14 | 2,518 | 2023–2026 | 1,259 | 1,259 | 2,518 |

## Source quality

- pick3: excluded 2 contradictory date/session record(s); collapsed 0 exact duplicate(s).
  - 2008-10-30 Night: 649, 867 (source disagreement)
  - 2008-11-09 Night: 374, 492 (source disagreement)
- pick4: excluded 0 contradictory date/session record(s); collapsed 0 exact duplicate(s).
- pick5: excluded 0 contradictory date/session record(s); collapsed 0 exact duplicate(s).

## Broad historical tests

Total prespecified comparisons: **161**. These are exploratory on historic data; family-wise Bonferroni
 correction controls for simultaneously searching many apparent patterns.

Raw p-values under 0.05: **5**. Family-wise-adjusted p-values under 0.05: **0**.

| Game | Period | Pattern checked | Raw p | Adjusted p |
| --- | --- | --- | ---: | ---: |
| pick3 | 2020_to_2024 | day_night_position_1 | 0.0041032 | 0.660615 |
| pick4 | 2025_onward | day_night_position_1 | 0.0194875 | 1 |
| pick3 | 2025_onward | position_3_uniform | 0.0216526 | 1 |
| pick3 | before_2010 | consecutive_exact_duplicate | 0.0249748 | 1 |
| pick4 | before_2010 | next_draw_same_position_repeat | 0.0378905 | 1 |
| pick5 | 2025_onward | day_night_position_3 | 0.0500281 | 1 |
| pick3 | 2020_to_2024 | consecutive_exact_duplicate | 0.0517319 | 1 |
| pick5 | 2020_to_2024 | fireball_uniform | 0.052778 | 1 |
| pick3 | 2025_onward | pooled_digit_uniform | 0.0685928 | 1 |
| pick3 | 2010_to_2019 | day_night_position_1 | 0.0693905 | 1 |
| pick5 | 2025_onward | position_2_uniform | 0.0902546 | 1 |
| pick4 | all_available | position_4_uniform | 0.106417 | 1 |
| pick5 | all_available | fireball_uniform | 0.106805 | 1 |
| pick4 | all_available | next_draw_same_position_repeat | 0.120328 | 1 |
| pick4 | all_available | position_3_uniform | 0.127449 | 1 |
| pick5 | 2025_onward | fireball_uniform | 0.130355 | 1 |
| pick3 | before_2010 | position_1_uniform | 0.151492 | 1 |
| pick4 | before_2010 | day_night_position_1 | 0.158533 | 1 |
| pick3 | 2010_to_2019 | all_unique_digit_count | 0.160285 | 1 |
| pick4 | 2010_to_2019 | day_night_position_1 | 0.162525 | 1 |

**Caution:** Even an adjusted finding is only a historical anomaly.
It must recur in a separate, future period before it could justify
any predictive claims. Draw equipment, ball sets, and operating
procedures are not identified in this numerical archive.

## Walk-forward probability forecasting (past years to later years)

A perfect fair-draw model gives each digit probability 10%; its
mean log-score *advantage* is exactly zero. Positive scores favor
a history-based model; negative scores favor fair uniform.
Forecasts were computed **only from earlier draws**.

| Game | Model | Period | Real next draws | Log-score advantage per draw | 95% interval |
| --- | --- | --- | ---: | ---: | --- |
| pick3 | last_100 | full | 23,251 | -0.101096 | [-0.106889, -0.095303] |
| pick3 | last_100 | 2020_to_2024 | 3,654 | -0.093004 | [-0.107939, -0.078069] |
| pick3 | last_100 | 2025_onward | 1,366 | -0.089354 | [-0.113123, -0.065585] |
| pick3 | last_500 | full | 23,251 | -0.026549 | [-0.029383, -0.023715] |
| pick3 | last_500 | 2020_to_2024 | 3,654 | -0.027625 | [-0.034469, -0.020781] |
| pick3 | last_500 | 2025_onward | 1,366 | -0.022853 | [-0.035045, -0.010662] |
| pick3 | last_500_same_session | full | 23,226 | -0.048308 | [-0.052178, -0.044439] |
| pick3 | last_500_same_session | 2020_to_2024 | 3,654 | -0.045941 | [-0.055964, -0.035919] |
| pick3 | last_500_same_session | 2025_onward | 1,366 | -0.042631 | [-0.059555, -0.025706] |
| pick4 | last_100 | full | 22,517 | -0.133103 | [-0.139900, -0.126306] |
| pick4 | last_100 | 2020_to_2024 | 3,654 | -0.134571 | [-0.151618, -0.117525] |
| pick4 | last_100 | 2025_onward | 1,366 | -0.137780 | [-0.165294, -0.110265] |
| pick4 | last_500 | full | 22,517 | -0.033724 | [-0.037141, -0.030306] |
| pick4 | last_500 | 2020_to_2024 | 3,654 | -0.036839 | [-0.045016, -0.028662] |
| pick4 | last_500 | 2025_onward | 1,366 | -0.031172 | [-0.044664, -0.017680] |
| pick4 | last_500_same_session | full | 22,492 | -0.063553 | [-0.068231, -0.058875] |
| pick4 | last_500_same_session | 2020_to_2024 | 3,654 | -0.063920 | [-0.075626, -0.052214] |
| pick4 | last_500_same_session | 2025_onward | 1,366 | -0.062832 | [-0.082285, -0.043378] |
| pick5 | last_100 | full | 2,018 | -0.176736 | [-0.201699, -0.151773] |
| pick5 | last_100 | 2020_to_2024 | 652 | -0.175180 | [-0.220449, -0.129910] |
| pick5 | last_100 | 2025_onward | 1,366 | -0.177479 | [-0.207375, -0.147583] |
| pick5 | last_500 | full | 2,018 | -0.042948 | [-0.055113, -0.030783] |
| pick5 | last_500 | 2020_to_2024 | 652 | -0.042913 | [-0.065130, -0.020696] |
| pick5 | last_500 | 2025_onward | 1,366 | -0.042965 | [-0.057480, -0.028450] |
| pick5 | last_500_same_session | full | 2,018 | -0.081387 | [-0.098466, -0.064307] |
| pick5 | last_500_same_session | 2020_to_2024 | 652 | -0.085670 | [-0.116458, -0.054882] |
| pick5 | last_500_same_session | 2025_onward | 1,366 | -0.079342 | [-0.099860, -0.058825] |

## Methodology and important limitations

- Source is the Virginia Lottery's actual Download All for each game,
  independently parsed without the April 2025 production cutoff.
- Earlier years include only Night draws before Day drawings began.
- FIREBALL is absent in older records and is never assumed to be zero.
- Only pre-registered descriptive checks and three fixed rolling
  forecast baselines are in this audit; no pattern-mining after a win.
- Apparent number biases can be the result of chance or reporting errors.
- The historical number archive lacks machine/ball-set identifiers,
  so it cannot identify an equipment-specific mechanism or bias.
- Stronger evidence would require disjoint prospective confirmation
  plus machine/ball-set metadata, not merely more retrospective tuning.
- All methods here are **research**, not documented financial advantage.

Raw per-year coverage and all statistical comparisons:
[research_decades.json](research_decades.json).

