# VAL adaptive contextual Box forecast — actual predictions

The candidate is a NEW prediction engine, not an auditing layer.
Experts: recent-regime positional model; weekday+session
posterior; independently timestamp-verified equipment and
pretest data when available; and a fair baseline. Expert
weights adapt using only earlier complete-draw likelihood.
Picks maximize predicted probability of a whole unordered
digit combination (all digits including repeats), never
partial matches or ordered-position hits.

## Real Virginia Lottery 2025–2026 predictions

The entire real history has been explored before. Results below
are exploratory chronological backtests, not an untouched
validation set. No real machine/pretest metadata is silently
inferred or injected from the simulator.

| Game | Actual target draws | New contextual Box wins | Pooled Box wins | Random Box wins | New mean joint log gain | New - random 95% paired hit CI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | 1376 | 22 | 29 | 24 | -0.000106 | [-14, 11] |
| pick4 | 1376 | 9 | 15 | 13 | -0.000461 | [-14, 6] |
| pick5 | 1376 | 4 | 6 | 9 | -0.000471 | [-12, 2] |

## Equipment genuinely unavailable vs available in invented scenarios

Public equipment here means **hypothetical** machine/pretest
observations, generated before the simulated winning draw and
explicitly timestamped BEFORE its synthetic cutoff.
Hidden scenarios do not allow the predictor to read the simulator
machine field or private pretests. This does NOT demonstrate
that this information is public before real Virginia wagers.

| Game | Artificial scenario | Test draws | Contextual Box wins | Random Box wins | Context joint log gain | Eligible metadata draws |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent_hidden_equipment | 900 | 17 | 13 | +0.000663 | 0 |
| pick3 | day_only_bias_hidden_equipment | 900 | 22 | 14 | +0.010013 | 0 |
| pick3 | halfway_replacement_hidden_equipment | 900 | 22 | 12 | +0.028862 | 0 |
| pick3 | hidden_opposing_machines_hidden_equipment | 900 | 17 | 19 | +0.000439 | 0 |
| pick3 | hidden_opposing_machines_public_equipment | 900 | 22 | 15 | +0.073163 | 900 |
| pick4 | fair_independent_hidden_equipment | 900 | 6 | 10 | -0.000685 | 0 |
| pick4 | day_only_bias_hidden_equipment | 900 | 11 | 6 | +0.006937 | 0 |
| pick4 | halfway_replacement_hidden_equipment | 900 | 2 | 6 | +0.021971 | 0 |
| pick4 | hidden_opposing_machines_hidden_equipment | 900 | 3 | 9 | -0.000309 | 0 |
| pick4 | hidden_opposing_machines_public_equipment | 900 | 15 | 5 | +0.082344 | 900 |
| pick5 | fair_independent_hidden_equipment | 900 | 3 | 2 | -0.000291 | 0 |
| pick5 | day_only_bias_hidden_equipment | 900 | 2 | 3 | +0.016927 | 0 |
| pick5 | halfway_replacement_hidden_equipment | 900 | 2 | 4 | +0.056357 | 0 |
| pick5 | hidden_opposing_machines_hidden_equipment | 900 | 1 | 3 | -0.000407 | 0 |
| pick5 | hidden_opposing_machines_public_equipment | 900 | 0 | 4 | +0.142925 | 900 |

## Production decision

No production changes from this exploratory study.
A real model promotion requires pre-frozen predictions
with stronger full Box and proper probability performance
on genuinely new outcomes and independent evidence that
external features were publicly available before wagering
closed. Synthetic machine IDs are never evidence of this.

The deployed digit_box_v4 formula is probed on a small,
predeclared set of actual targets per game; those probe
results are in the JSON, not a full-window head-to-head.

[Target-by-target research JSON](contextual_regime_box_v1.json).

