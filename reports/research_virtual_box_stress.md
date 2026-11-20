# VAL high-volume virtual-draw COMPLETE Box test

8 independent synthetic trials per game/scenario,
850 historical virtual training results,
650 scored future virtual results per trial.
Tickets are frozen every 260 results, then
graded against each subsequent drawing in the block.
Each model has three distinct Box tickets for each drawing.
The random, incumbent Box v3 and challenger portfolios are
selected before the block and compared on identical outcomes.

**Primary metric: full Any Order digits, including repeated digits.**
Correct-position or partial-digit matches are never credited.
No actual Virginia Lottery edge is established by this synthetic test.

| Game | Simulated mechanism | Target draws | Challenger Box wins | Live v3 Box wins | Random Box wins | Fair expected (candidate) | Challenger active blocks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 5200 | 113 | 81 | 96 | 93.6 | 0/24 |
| pick3 | fixed_position_small | 5200 | 91 | 79 | 104 | 93.6 | 2/24 |
| pick3 | fixed_position_strong | 5200 | 107 | 93 | 87 | 93.6 | 24/24 |
| pick3 | pooled_device_bias | 5200 | 109 | 87 | 101 | 93.6 | 24/24 |
| pick3 | day_only_bias | 5200 | 125 | 113 | 102 | 93.6 | 22/24 |
| pick3 | halfway_replacement | 5200 | 124 | 101 | 111 | 93.6 | 24/24 |
| pick3 | hidden_opposing_machines | 5200 | 81 | 104 | 88 | 93.6 | 0/24 |
| pick3 | within_draw_echo | 5200 | 92 | 53 | 31 | 58.9 | 24/24 |
| pick4 | fair_independent | 5200 | 41 | 35 | 32 | 37.4 | 0/24 |
| pick4 | fixed_position_small | 5200 | 39 | 33 | 32 | 37.4 | 0/24 |
| pick4 | fixed_position_strong | 5200 | 46 | 38 | 41 | 37.4 | 24/24 |
| pick4 | pooled_device_bias | 5200 | 46 | 36 | 32 | 37.4 | 24/24 |
| pick4 | day_only_bias | 5200 | 46 | 38 | 36 | 37.4 | 22/24 |
| pick4 | halfway_replacement | 5200 | 45 | 24 | 33 | 37.4 | 24/24 |
| pick4 | hidden_opposing_machines | 5200 | 37 | 35 | 26 | 37.4 | 0/24 |
| pick4 | within_draw_echo | 5200 | 22 | 8 | 16 | 10.2 | 24/24 |
| pick5 | fair_independent | 5200 | 20 | 21 | 22 | 18.7 | 0/24 |
| pick5 | fixed_position_small | 5200 | 20 | 10 | 19 | 18.7 | 0/24 |
| pick5 | fixed_position_strong | 5200 | 17 | 20 | 16 | 18.7 | 24/24 |
| pick5 | pooled_device_bias | 5200 | 32 | 15 | 28 | 18.7 | 24/24 |
| pick5 | day_only_bias | 5200 | 20 | 21 | 23 | 18.7 | 24/24 |
| pick5 | halfway_replacement | 5200 | 22 | 22 | 11 | 18.7 | 24/24 |
| pick5 | hidden_opposing_machines | 5200 | 19 | 17 | 19 | 18.7 | 0/24 |
| pick5 | within_draw_echo | 5200 | 13 | 4 | 7 | 4.9 | 24/24 |

## Interpretation

A fair iid drawing gives no predictor a dependable edge.
Synthetic biases test detection capability, not real-world advantage.
The frozen deployment blocks differ from refresh-on-every-draw;
forecasts for both Day and Night are frozen before each block.
Real-world validation requires prospectively saved real outcomes.

[Raw results](research_virtual_box_stress.json).

