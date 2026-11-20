# VAL Box v3 — complete Any Order formula vs original ensemble

Precommitted challenger: **digit_box_v3**.
Direct live-generator replay on real subsequent drawing outcomes.
Each candidate uses strictly earlier history. This is exploratory
because the historical period has been previously inspected.
PRIMARY METRIC: complete Any Order (Box) matches, with all digit
multiplicities preserved. All groups have three $1 paper Box tickets
per target (where legal). Payout/net use published non-FIREBALL
Any Order prizes; NO real wagers were made. Old legacy ensembles
may select repeated digits and thereby cover fewer permutations;
the v2 and fair controls both select nonoverlapping all-distinct
sets when no signal has passed its gate.

| Game | Draws | v2 full Box wins | Old Box wins | Fair Box wins | v2 Box net | Old Box net | Fair Box net | v2 exact order |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | 220 | 3 | 3 | 9 | $-420 | $-416 | $60 | 0 |
| pick4 | 220 | 1 | 0 | 2 | $-460 | $-659 | $-260 | 0 |
| pick5 | 121 | 0 | 0 | 0 | $-363 | $-363 | $-363 | 0 |

## PICK3

Official history draws: 23,761; evaluated 220 independent target origins.
Test dates: 2025-01-29T18:59:00+00:00 through 2026-11-17T18:59:00+00:00.
Conditionally active signal gates: 0/220.
Active expert counts: {}.
Fair-expected complete Box matches at the actual selected permutation classes: new_v2: 3.960, original_ensemble: 3.315, uniform_control: 3.960.

| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |
| --- | ---: | ---: | ---: |
| new_v2 | +0.000000 | +0.000000 | +0.000000 |
| original_ensemble | -0.021192 | -0.026935 | -0.015449 |
| uniform_control | +0.000000 | +0.000000 | +0.000000 |

v2 minus old ensemble: +0.021192 log units per drawing; day-cluster 95% interval: [-0.010931, +0.053315].


## PICK4

Official history draws: 23,027; evaluated 220 independent target origins.
Test dates: 2025-01-29T18:59:00+00:00 through 2026-11-17T18:59:00+00:00.
Conditionally active signal gates: 0/220.
Active expert counts: {}.
Fair-expected complete Box matches at the actual selected permutation classes: new_v2: 1.584, original_ensemble: 1.162, uniform_control: 1.584.

| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |
| --- | ---: | ---: | ---: |
| new_v2 | +0.000000 | +0.000000 | +0.000000 |
| original_ensemble | -0.031137 | -0.008357 | -0.053916 |
| uniform_control | +0.000000 | +0.000000 | +0.000000 |

v2 minus old ensemble: +0.031137 log units per drawing; day-cluster 95% interval: [-0.006839, +0.069112].


## PICK5

Official history draws: 2,528; evaluated 121 independent target origins.
Test dates: 2025-11-22T18:59:00+00:00 through 2026-11-17T18:59:00+00:00.
Conditionally active signal gates: 0/121.
Active expert counts: {}.
Fair-expected complete Box matches at the actual selected permutation classes: new_v2: 0.436, original_ensemble: 0.258, uniform_control: 0.436.

| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |
| --- | ---: | ---: | ---: |
| new_v2 | +0.000000 | +0.000000 | +0.000000 |
| original_ensemble | -0.022477 | -0.029304 | -0.015762 |
| uniform_control | +0.000000 | +0.000000 | +0.000000 |

v2 minus old ensemble: +0.022477 log units per drawing; day-cluster 95% interval: [-0.033446, +0.078399].

## Interpretation and promotion rule

The Box v3 formula is a genuine conditional joint model. Box likelihood
is computed by summing every distinct complete permutation, not
by separately matching individual digit positions. It only exposesa nonuniform advantage if a model passes the past-only statistical gate.
Otherwise it uses fair 10%-per-position distributions and diverse
independent nonoverlapping Box candidates. It is designed to reduce overconfidence,
not to fake a winning edge. A lower log loss can be a valid improvement
in forecasting honesty even when hit rates remain indistinguishable.

Only strictly future, immutable paper predictions can validate a
claim of a new predictive edge. No model is promoted merely by
retrospectively finding a lucky ticket.

Machine readable target-level comparison:
[research_digit_box_v3.json](research_digit_box_v3.json).

