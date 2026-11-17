# VAL Keno — structural randomness investigation

Official archived records: **10,665**.
Exploratory discovery: 6,399 draws;
later chronological evaluation: 4,266 draws.
Period under validation: ['2026-11-04T05:02:00', '2026-11-16T09:45:30']

## Are there unusual patterns?

| Hypothesis | Tests | Discovery findings after correction | Validation findings after correction |
| --- | ---: | ---: | ---: |
| Unusual individual frequencies | 80 | 0 | 0 |
| Within-draw number pairs | 3,160 | 0 | 0 of 20 flagged pairs |
| Consecutive-draw number overlap | 6 lag distances | 0 | 0 |
| Individual reappearance next draw | 80 | 0 | 0 |
| Time-of-day number bias | 320 | 0 | 0 |

All family-wise corrections use Bonferroni at 5%. Pair-validation
correction is across the 20 previously flagged pairs.
These are approximate tests; same-draw number dependence
and overlapping serial comparisons make caution important.

## Can any signal improve ONE five-number ticket per drawing?

| Method | Tickets | Average matching balls | Perfect 5/5 | Gross/$1 | Net hypothetical $ | Adjusted hit-count p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| uniform_random | 4,266 | 1.2848 | 4 | 0.8945 | -450 | 0.07977 |
| original_ensemble | 4,266 | 1.2691 | 3 | 0.7647 | -1,004 | 0.9298 |
| frequency | 4,266 | 1.2454 | 5 | 0.9090 | -388 | 1 |
| lag_repeat | 4,266 | 1.2511 | 4 | 0.8218 | -760 | 1 |
| transition | 4,266 | 1.2431 | 2 | 0.6263 | -1,594 | 1 |

Mathematical null: 1.25 matches per five-number ticket,
approximately 0.7 dollars gross returned per dollar wagered.
Each method makes exactly one ticket per actual future historical draw.
Discovery-period statistics are frozen before validation.
The original VAL ensemble's first ticket is also evaluated.

## Probability calibration

For static frequency, prior-draw repetition and cross-draw
transition-matrix methods, lower Brier score is better.
A fair uniform model scores 0.1875 per draw.

| Method | Brier advantage vs fair | Approximate 95% interval |
| --- | ---: | ---: |
| frequency | -0.00001782 | [-0.00002987, -0.00000577] |
| lag_repeat | -0.00000075 | [-0.00000286, +0.00000135] |
| transition | -0.00000867 | [-0.00001610, -0.00000124] |

## Interpretation

A corrected anomaly by itself does not establish prediction:
we require consistent direction in the later time period and
out-of-sample win-rate/probability improvement.
The validation period is historical, and earlier VAL research
already inspected this archive. We cannot call it untouched.
No live picks were modified. No money was wagered.
Archive gaps are explicitly omitted from cross-draw lag tests.

Full numbered anomalies and per-model diagnostics:
[research_keno_dependencies.json](research_keno_dependencies.json).

