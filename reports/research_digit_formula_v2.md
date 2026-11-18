# VAL v2 — actual formula vs original ensemble

Precommitted challenger: **digit_conditional_v2**.
Direct live-generator replay on real subsequent drawing outcomes.
Each candidate uses strictly earlier history. This is exploratory
because the historical period has been previously inspected.
All groups have three tickets per target. Exact = full Straight match.
Position matches are diagnostics; a single position match on its own
does NOT constitute a prize.

| Game | Test draws | v2 matched positions | Old ensemble | Uniform controls | v2 exact | Old exact | Uniform exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | 220 | 9.80% | 8.74% | 10.51% | 1 | 0 | 2 |
| pick4 | 220 | 10.49% | 9.58% | 9.32% | 0 | 0 | 3 |
| pick5 | 120 | 9.78% | 11.94% | 10.61% | 0 | 0 | 0 |

## PICK3

Official history draws: 23,757; evaluated 220 independent target origins.
Test dates: 2025-01-27T18:59:00+00:00 through 2026-11-15T18:59:00+00:00.
Conditionally active signal gates: 0/220.
Active expert counts: {}.

| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |
| --- | ---: | ---: | ---: |
| new_v2 | +0.000000 | +0.000000 | +0.000000 |
| original_ensemble | -0.024709 | -0.024597 | -0.024820 |
| uniform_control | +0.000000 | +0.000000 | +0.000000 |

v2 minus old ensemble: +0.024709 log units per drawing; day-cluster 95% interval: [-0.006900, +0.056318].


## PICK4

Official history draws: 23,023; evaluated 220 independent target origins.
Test dates: 2025-01-27T18:59:00+00:00 through 2026-11-15T18:59:00+00:00.
Conditionally active signal gates: 0/220.
Active expert counts: {}.

| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |
| --- | ---: | ---: | ---: |
| new_v2 | +0.000000 | +0.000000 | +0.000000 |
| original_ensemble | -0.029966 | -0.043242 | -0.016690 |
| uniform_control | +0.000000 | +0.000000 | +0.000000 |

v2 minus old ensemble: +0.029966 log units per drawing; day-cluster 95% interval: [-0.006523, +0.066456].


## PICK5

Official history draws: 2,524; evaluated 120 independent target origins.
Test dates: 2025-11-23T18:59:00+00:00 through 2026-11-15T18:59:00+00:00.
Conditionally active signal gates: 0/120.
Active expert counts: {}.

| Formula | Mean next-draw log gain vs 10%-per-digit fair | First half | Second half |
| --- | ---: | ---: | ---: |
| new_v2 | +0.000000 | +0.000000 | +0.000000 |
| original_ensemble | -0.030042 | -0.006561 | -0.053522 |
| uniform_control | +0.000000 | +0.000000 | +0.000000 |

v2 minus old ensemble: +0.030042 log units per drawing; day-cluster 95% interval: [-0.023239, +0.083323].

## Interpretation and promotion rule

The v2 formula is a genuine conditional joint model. It only exposes
a nonuniform advantage if a model passes the past-only statistical gate.
Otherwise it uses fair 10%-per-position distributions and diverse
independent random candidates. It is designed to reduce overconfidence,
not to fake a winning edge. A lower log loss can be a valid improvement
in forecasting honesty even when hit rates remain indistinguishable.

Only strictly future, immutable paper predictions can validate a
claim of a new predictive edge. No model is promoted merely by
retrospectively finding a lucky ticket.

Machine readable target-level comparison:
[research_digit_formula_v2.json](research_digit_formula_v2.json).

