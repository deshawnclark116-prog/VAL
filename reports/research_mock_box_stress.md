# VAL mock-lottery full Box stress test

Simulates hidden-machine digit drawing conditions using the repository's
existing virtual drawing machine. This is **not** a faithful
physical replica or evidence of machine bias in Virginia.

Only complete Any Order multisets count as wins, preserving repeats.
Three independent $1 paper Box combinations for each method and target.
No purchases. No future draw is available when its selection is made.

Fair scenario evaluates every held-out drawing. Biased scenarios
forecast every draw but sample Box tickets at the fixed stride;
their observed Box wins are too sparse for reliable superiority claims.

| Game | Injected mechanism | Held-out draws | Box trials | VAL Box wins | Random Box wins | VAL *true* expected wins | Random *true* expected wins | Active draws | Log gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 40,000 | 40,000 | 724 | 741 | 720.00 | 720.00 | 0 | +0.000000 |
| pick3 | fixed_position_small | 6,000 | 60 | 2 | 1 | 1.08 | 1.08 | 0 | +0.000000 |
| pick3 | fixed_position_strong | 6,000 | 60 | 2 | 4 | 1.42 | 1.09 | 6,000 | +0.047788 |
| pick3 | pooled_device_bias | 6,000 | 60 | 1 | 0 | 1.41 | 1.08 | 6,000 | +0.020770 |
| pick3 | day_only_bias | 6,000 | 60 | 1 | 1 | 1.56 | 1.07 | 6,000 | +0.012754 |
| pick3 | halfway_replacement | 6,000 | 60 | 1 | 1 | 1.60 | 1.03 | 6,000 | +0.062265 |
| pick3 | hidden_opposing_machines | 6,000 | 60 | 1 | 3 | 1.11 | 1.07 | 0 | +0.000000 |
| pick3 | within_draw_echo | 6,000 | 60 | 1 | 0 | 0.96 | 0.53 | 6,000 | +0.389721 |
| pick4 | fair_independent | 40,000 | 40,000 | 330 | 294 | 288.00 | 288.00 | 0 | +0.000000 |
| pick4 | fixed_position_small | 6,000 | 60 | 1 | 1 | 0.43 | 0.43 | 0 | +0.000000 |
| pick4 | fixed_position_strong | 6,000 | 60 | 0 | 0 | 0.52 | 0.44 | 6,000 | +0.042268 |
| pick4 | pooled_device_bias | 6,000 | 60 | 0 | 0 | 0.54 | 0.43 | 6,000 | +0.036320 |
| pick4 | day_only_bias | 6,000 | 60 | 0 | 1 | 0.58 | 0.42 | 6,000 | +0.026434 |
| pick4 | halfway_replacement | 6,000 | 60 | 0 | 1 | 0.59 | 0.42 | 6,000 | +0.094935 |
| pick4 | hidden_opposing_machines | 6,000 | 60 | 0 | 1 | 0.42 | 0.43 | 0 | +0.000000 |
| pick4 | within_draw_echo | 6,000 | 60 | 0 | 0 | 0.40 | 0.15 | 6,000 | +0.666445 |
| pick5 | fair_independent | 40,000 | 40,000 | 160 | 156 | 144.00 | 144.00 | 0 | +0.000000 |
| pick5 | fixed_position_small | 6,000 | 60 | 0 | 0 | 0.22 | 0.22 | 0 | +0.000000 |
| pick5 | fixed_position_strong | 6,000 | 60 | 0 | 1 | 0.24 | 0.22 | 6,000 | +0.043913 |
| pick5 | pooled_device_bias | 6,000 | 60 | 1 | 0 | 0.26 | 0.22 | 6,000 | +0.041809 |
| pick5 | day_only_bias | 6,000 | 60 | 0 | 0 | 0.27 | 0.21 | 6,000 | +0.029738 |
| pick5 | halfway_replacement | 6,000 | 60 | 2 | 1 | 0.27 | 0.21 | 6,000 | +0.118048 |
| pick5 | hidden_opposing_machines | 6,000 | 60 | 1 | 2 | 0.20 | 0.21 | 0 | +0.000000 |
| pick5 | within_draw_echo | 6,000 | 60 | 1 | 0 | 0.13 | 0.05 | 6,000 | +0.905162 |

## Fair generator: maximum-coverage three-Box baseline

| Game | Expected full Box matches in 40,000 draws | VAL observed | Random observed | VAL minus random (percentage points) | Approx paired 95% range (points) |
| --- | ---: | ---: | ---: | ---: | --- |
| pick3 | 720.0 | 724 | 741 | -0.042 | [-0.228, +0.143] |
| pick4 | 288.0 | 330 | 294 | +0.090 | [-0.032, +0.212] |
| pick5 | 144.0 | 160 | 156 | +0.010 | [-0.077, +0.097] |

## Interpretation

Only the fair scenario is sized to evaluate stable hit-rate estimates.
Even with a known injected statistical bias, observed Box wins in the
small sampled biased scenario can deviate greatly from expected wins.
The known-mechanism *true expected wins* measure whether the model
actually selected higher-probability Box outcomes under simulation.
Those oracles are strictly post-prediction diagnostics.

This mock draw cannot demonstrate that real Virginia drawings
are predictable. An exploitable real-world claim needs frozen
prospective results that beat fair/random on full Box outcomes.

[Machine-readable results](research_mock_box_stress.json).
