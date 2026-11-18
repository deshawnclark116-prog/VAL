# VAL Pick 3/4/5 — restored history and cross-draw forecast challenge

Source: official Virginia Lottery full-history download. Models are
constructed using only results strictly before the forecast origin.
The same ensemble and independently drawn random-control tickets
are compared against the next recorded drawing and later drawings.
A model is frozen using the earlier calendar segment before checking
a later segment. Historical source was previously inspected, so
these are NOT untouched prospective results.

One correct-position digit is worth no prize on a Straight-only wager;
position-hit rates are diagnostic, not financial returns.

## PICK3

Official source: **23,757 recorded draws** (1989-05-23T03:00:00+00:00 to 2026-11-18T04:00:00+00:00).
Fingerprint SHA-256: f4c510af80baf6950fdbae5b72a9e0efa7cef47aed2554c85444910bbe536743
Calibration origins: 1080; later evaluation origins: **1320**.

| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |
| --- | ---: | --- |
| uniform | +0.000000 | [+0.000000, +0.000000] |
| legacy_ensemble | -0.029433 | [-0.041764, -0.015827] |
| long500 | -0.015955 | [-0.026210, -0.005952] |
| same_session | -0.019595 | [-0.031015, -0.007819] |
| multi_scale | -0.013703 | [-0.023973, -0.004589] |
| lag_transition | -0.005575 | [-0.013389, +0.002576] |

Calibration-only selection for immediate next draw: **uniform**.
Calibration-only selection across forecast offsets: **uniform** at offset 0.

| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1226/11880 (10.32%) | 1189/11880 (10.01%) | 6 | 5 |
| 1 | 1173/11880 (9.87%) | 1155/11880 (9.72%) | 4 | 1 |
| 2 | 1189/11880 (10.01%) | 1160/11880 (9.76%) | 2 | 3 |
| 3 | 1179/11880 (9.92%) | 1227/11880 (10.33%) | 3 | 5 |
| 5 | 1201/11880 (10.11%) | 1172/11880 (9.87%) | 3 | 2 |
| 7 | 1194/11880 (10.05%) | 1202/11880 (10.12%) | 5 | 5 |

## PICK4

Official source: **23,023 recorded draws** (1991-10-01T03:00:00+00:00 to 2026-11-18T04:00:00+00:00).
Fingerprint SHA-256: 5d5b53ff80f2afc667aef2c444c6a898470e3c7f3a094a2631114e72d72091db
Calibration origins: 1080; later evaluation origins: **1320**.

| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |
| --- | ---: | --- |
| uniform | +0.000000 | [+0.000000, +0.000000] |
| legacy_ensemble | -0.040652 | [-0.055104, -0.026146] |
| long500 | -0.024172 | [-0.036823, -0.011438] |
| same_session | -0.028702 | [-0.041470, -0.015779] |
| multi_scale | -0.020452 | [-0.031337, -0.009772] |
| lag_transition | -0.016973 | [-0.025421, -0.008126] |

Calibration-only selection for immediate next draw: **uniform**.
Calibration-only selection across forecast offsets: **uniform** at offset 0.

| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1601/15840 (10.11%) | 1645/15840 (10.39%) | 0 | 0 |
| 1 | 1573/15840 (9.93%) | 1528/15840 (9.65%) | 0 | 0 |
| 2 | 1600/15840 (10.10%) | 1562/15840 (9.86%) | 0 | 0 |
| 3 | 1583/15840 (9.99%) | 1658/15840 (10.47%) | 0 | 1 |
| 5 | 1553/15840 (9.80%) | 1606/15840 (10.14%) | 0 | 0 |
| 7 | 1562/15840 (9.86%) | 1582/15840 (9.99%) | 0 | 0 |

## PICK5

Official source: **2,524 recorded draws** (2023-06-05T17:59:00+00:00 to 2026-11-18T04:00:00+00:00).
Fingerprint SHA-256: 9e8b0e4a77757a71fb06451b86385f7e36e81f3d0153fccd415cbeb4bbe0eec9
Calibration origins: 907; later evaluation origins: **1110**.

| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |
| --- | ---: | --- |
| uniform | +0.000000 | [+0.000000, +0.000000] |
| legacy_ensemble | -0.048117 | [-0.066539, -0.028976] |
| long500 | -0.027729 | [-0.043133, -0.014363] |
| same_session | -0.035419 | [-0.050375, -0.021430] |
| multi_scale | -0.023904 | [-0.036959, -0.011898] |
| lag_transition | -0.021405 | [-0.031357, -0.010149] |

Calibration-only selection for immediate next draw: **uniform**.
Calibration-only selection across forecast offsets: **uniform** at offset 0.

| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1615/16650 (9.70%) | 1693/16650 (10.17%) | 0 | 0 |
| 1 | 1671/16650 (10.04%) | 1680/16650 (10.09%) | 1 | 0 |
| 2 | 1651/16650 (9.92%) | 1642/16650 (9.86%) | 0 | 0 |
| 3 | 1671/16650 (10.04%) | 1687/16650 (10.13%) | 0 | 0 |
| 5 | 1558/16650 (9.36%) | 1687/16650 (10.13%) | 0 | 0 |
| 7 | 1644/16650 (9.87%) | 1695/16650 (10.18%) | 1 | 0 |

## Decision rule

Do not change production tickets merely because an earlier forecast
looked good against another date. An exploitable horizon must survive
independent future forecasts with model parameters and horizons
committed ahead of those results, outperform fair probabilities
with positive lower confidence bound, and demonstrate meaningful
payout improvement. Multiple horizons and games mean multiple
hypotheses, requiring correction for selection.

**This report does not assert that any prediction edge exists.**
Original prospective ledger and live pick scheduling are unchanged
apart from the separately committed history-retention fix.

Machine-readable detail: [research_digit_horizons.json](research_digit_horizons.json).

