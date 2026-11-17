# VAL Keno — machine-learning challenger under falsification controls

Frozen source: **10,665 official draws**.
Training 6399 draws; model/calibration selection 2133 draws; **final chronological evaluation 2133 draws**.

Model features: multi-scale frequency, six lag indicators, number recency,
scheduled draw-time and weekday cycles, and draw index conditions.
Architectures: regularized logistic regression, gradient boosted trees,
static frequency control and exact fair null.

**Frozen before final test:** static_frequency with shrinkage 0.25 (selected using Brier score only on middle period).

| Final period model | Single-ball hits | Hit rate | Brier gain vs fair | 95% day-bootstrap Brier gain |
| --- | ---: | ---: | ---: | --- |
| fair_uniform | 521/2133 | 24.43% | +0.00000000 | [+0.00000000, +0.00000000] |
| regularized_linear_unshrunk | 542/2133 | 25.41% | -0.00000782 | [-0.00001230, -0.00000306] |
| nonlinear_boosted_unshrunk | 513/2133 | 24.05% | -0.00002818 | [-0.00005090, -0.00001207] |
| static_frequency_unshrunk | 524/2133 | 24.57% | -0.00004593 | [-0.00006074, -0.00003270] |
| calibration_selected_champion | 524/2133 | 24.57% | -0.00000634 | [-0.00001005, -0.00000304] |

25 independent random ticket controls, one ball per draw:
mean 1.40%, range 0.09% to 11.67%.

The 25% chance baseline is the expected hit rate under fair selection.
Brier score assesses ALL 80 probabilities per drawing and cannot
be rescued by occasional unusually lucky five-number jackpots.
Day-level bootstrap accounts for within-day related outcomes.
We never choose a final-period winner after seeing final results.

**Caution:** all these draws are historical and had previously been
examined in other experiments. This is a stronger chronological
falsification study, not a genuinely unseen prospective test.
A physically perfect generator and an exploitable one may be hard
to distinguish with only a month of outputs.

No live VAL change, real gambling, or claims of guaranteed winnings.
Full audit: [research_keno_ml_challenger.json](research_keno_ml_challenger.json).

