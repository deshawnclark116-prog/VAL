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

Official source: **23,761 recorded draws** (1989-05-23T03:00:00+00:00 to 2026-11-20T04:00:00+00:00).
Fingerprint SHA-256: f3986c184c33eac21eefb98a4ba440c759e14ee9bd689c007f321be92a38a963
Calibration origins: 1080; later evaluation origins: **1320**.

| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |
| --- | ---: | --- |
| uniform | +0.000000 | [+0.000000, +0.000000] |
| legacy_ensemble | -0.029459 | [-0.042594, -0.017432] |
| long500 | -0.016068 | [-0.027192, -0.005041] |
| same_session | -0.020008 | [-0.031088, -0.009679] |
| multi_scale | -0.013888 | [-0.024014, -0.004073] |
| lag_transition | -0.005184 | [-0.013328, +0.002533] |

Calibration-only selection for immediate next draw: **uniform**.
Calibration-only selection across forecast offsets: **uniform** at offset 0.

| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1221/11880 (10.28%) | 1185/11880 (9.97%) | 6 | 5 |
| 1 | 1176/11880 (9.90%) | 1153/11880 (9.71%) | 4 | 1 |
| 2 | 1184/11880 (9.97%) | 1163/11880 (9.79%) | 2 | 3 |
| 3 | 1181/11880 (9.94%) | 1228/11880 (10.34%) | 3 | 5 |
| 5 | 1204/11880 (10.13%) | 1176/11880 (9.90%) | 3 | 2 |
| 7 | 1192/11880 (10.03%) | 1204/11880 (10.13%) | 5 | 5 |

## PICK4

Official source: **23,027 recorded draws** (1991-10-01T03:00:00+00:00 to 2026-11-20T04:00:00+00:00).
Fingerprint SHA-256: 6cffa1f92b4a2ec0ce534f5ec8701f44d82bd320d12dbd0b8c81c12396f8d170
Calibration origins: 1080; later evaluation origins: **1320**.

| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |
| --- | ---: | --- |
| uniform | +0.000000 | [+0.000000, +0.000000] |
| legacy_ensemble | -0.040833 | [-0.055755, -0.026584] |
| long500 | -0.024635 | [-0.037305, -0.013237] |
| same_session | -0.028947 | [-0.041684, -0.015803] |
| multi_scale | -0.020749 | [-0.030449, -0.010317] |
| lag_transition | -0.017069 | [-0.025962, -0.008538] |

Calibration-only selection for immediate next draw: **uniform**.
Calibration-only selection across forecast offsets: **uniform** at offset 0.

| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1600/15840 (10.10%) | 1647/15840 (10.40%) | 0 | 0 |
| 1 | 1571/15840 (9.92%) | 1522/15840 (9.61%) | 0 | 0 |
| 2 | 1602/15840 (10.11%) | 1564/15840 (9.87%) | 0 | 0 |
| 3 | 1583/15840 (9.99%) | 1653/15840 (10.44%) | 0 | 1 |
| 5 | 1551/15840 (9.79%) | 1607/15840 (10.15%) | 0 | 0 |
| 7 | 1559/15840 (9.84%) | 1578/15840 (9.96%) | 0 | 0 |

## PICK5

Official source: **2,528 recorded draws** (2023-06-05T17:59:00+00:00 to 2026-11-20T04:00:00+00:00).
Fingerprint SHA-256: 3a626fd4399076e95db43d955ecf5057a9817a4b6bf7a8b1ed6944642a0b127d
Calibration origins: 909; later evaluation origins: **1112**.

| Next-target probability model | Final mean log-score gain vs fair | 95% day-cluster interval |
| --- | ---: | --- |
| uniform | +0.000000 | [+0.000000, +0.000000] |
| legacy_ensemble | -0.048487 | [-0.068642, -0.032243] |
| long500 | -0.027853 | [-0.040234, -0.014791] |
| same_session | -0.035641 | [-0.050407, -0.019496] |
| multi_scale | -0.024132 | [-0.036369, -0.011915] |
| lag_transition | -0.022042 | [-0.033683, -0.009899] |

Calibration-only selection for immediate next draw: **uniform**.
Calibration-only selection across forecast offsets: **uniform** at offset 0.

| Target offset (draws after next) | Original ensemble position hits | Random-control hits | Ensemble exact wins | Random exact wins |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1618/16680 (9.70%) | 1696/16680 (10.17%) | 0 | 0 |
| 1 | 1674/16680 (10.04%) | 1687/16680 (10.11%) | 1 | 0 |
| 2 | 1654/16680 (9.92%) | 1647/16680 (9.87%) | 0 | 0 |
| 3 | 1671/16680 (10.02%) | 1693/16680 (10.15%) | 0 | 0 |
| 5 | 1563/16680 (9.37%) | 1693/16680 (10.15%) | 0 | 0 |
| 7 | 1644/16680 (9.86%) | 1696/16680 (10.17%) | 1 | 0 |

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

