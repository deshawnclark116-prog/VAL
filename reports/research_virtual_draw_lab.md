# VAL virtual drawing-machine laboratory

**This is a statistical virtual apparatus, not an exact physical
replica of the Virginia Lottery's equipment.** Ball-set IDs,
pretest observations and equipment-selection availability are
unknown for the individual real Pick 3/4/5 archived draws.

Each virtual draw contains one independent digit selection per
position, except for the explicitly declared echo experiment.
Repetitions are allowed, as in the real digit games. The simulator
selects one hypothetical equipment ID per day, and performs two
pretests. Those private synthetic states do not automatically
become legal pre-wager features.

Eight scenarios: fair independent; weak fixed-position skew
(12.5% instead of 10% for one digit); strong fixed-position skew
(22% for one digit); pooled 14.5% digit bias; Day-only 17%
pooled skew; 18% favorite-digit reversal midway through held-out draws; randomly
selected hidden opposing machines with *uniform unconditional*
outcomes; and a 30% same-previous-position echo mechanism.

Models are online rolling-frequency baselines with symmetric
smoothing, plus the exact deployed v2 formula probed on a fixed
sparse sample of target origins. The perfect-information oracle
receives the simulator's secret probabilities and supplies the
best possible log-score achievable under those assumptions.
The equipment-aware model has hypothetical advance access to
machine identity; real-world advance access is UNVERIFIED.

| Game | Virtual scenario | Fair top-1 | Pooled top-1 | Position top-1 | Visible equipment top-1 | Oracle top-1 | Live v2 gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 10.14% | 10.31% | 10.58% | 10.20% | 10.14% | 0/5 |
| pick3 | fixed_position_small | 9.94% | 9.91% | 10.13% | 10.07% | 10.98% | 0/5 |
| pick3 | fixed_position_strong | 9.56% | 13.90% | 14.05% | 14.15% | 14.40% | 0/5 |
| pick3 | pooled_device_bias | 9.56% | 14.29% | 13.99% | 13.16% | 14.29% | 0/5 |
| pick3 | day_only_bias | 9.77% | 14.05% | 13.55% | 12.77% | 14.16% | 0/5 |
| pick3 | halfway_replacement | 8.94% | 14.02% | 14.15% | 14.27% | 18.09% | 0/5 |
| pick3 | hidden_opposing_machines | 9.82% | 9.92% | 10.03% | 14.13% | 14.11% | 0/5 |
| pick3 | within_draw_echo | 10.26% | 10.04% | 10.24% | 10.29% | 28.16% | 5/5 |
| pick4 | fair_independent | 10.12% | 10.25% | 9.79% | 10.43% | 10.12% | 0/5 |
| pick4 | fixed_position_small | 9.75% | 10.68% | 10.79% | 10.50% | 10.82% | 0/5 |
| pick4 | fixed_position_strong | 9.53% | 13.07% | 12.86% | 13.18% | 13.02% | 2/5 |
| pick4 | pooled_device_bias | 9.54% | 14.53% | 14.36% | 13.63% | 14.53% | 0/5 |
| pick4 | day_only_bias | 9.50% | 13.08% | 12.61% | 11.74% | 13.08% | 0/5 |
| pick4 | halfway_replacement | 9.25% | 14.30% | 14.46% | 14.43% | 18.22% | 1/5 |
| pick4 | hidden_opposing_machines | 9.88% | 9.58% | 10.12% | 13.46% | 13.58% | 0/5 |
| pick4 | within_draw_echo | 10.16% | 9.99% | 9.85% | 9.77% | 30.49% | 5/5 |
| pick5 | fair_independent | 10.05% | 10.02% | 9.88% | 10.07% | 10.05% | 0/5 |
| pick5 | fixed_position_small | 9.93% | 9.67% | 10.12% | 10.40% | 10.35% | 0/5 |
| pick5 | fixed_position_strong | 10.01% | 12.52% | 12.22% | 12.32% | 12.57% | 1/5 |
| pick5 | pooled_device_bias | 9.47% | 14.50% | 14.35% | 13.82% | 14.50% | 0/5 |
| pick5 | day_only_bias | 9.56% | 13.51% | 13.20% | 12.47% | 13.58% | 0/5 |
| pick5 | halfway_replacement | 9.16% | 14.08% | 14.14% | 14.32% | 18.20% | 4/5 |
| pick5 | hidden_opposing_machines | 10.26% | 9.82% | 9.89% | 14.15% | 14.29% | 0/5 |
| pick5 | within_draw_echo | 9.64% | 10.07% | 9.91% | 9.98% | 31.48% | 5/5 |

## Decision

A simulator with injected bias measures our *ability to recover that
bias*. It does not demonstrate that Virginia's real drawings have
the same bias. The fair scenario quantifies false positives; the
hidden-machine scenario checks irreducible uncertainty.
Model selection must come from observations available before the
actual wager cut-off. A model that improves only with secret
machine IDs is not a usable strategy.

[Complete target-level aggregate metrics](research_virtual_draw_lab.json).

