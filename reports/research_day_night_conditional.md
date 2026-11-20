# Day-to-Night conditional prediction formula — full Any Order audit

Research-only mathematical challenger. The model learns statistical
relationships between completed Day drawings and later Night results.
It is NEVER supplied the simulator's hidden machine identity,
private pretest outcomes, or the target's future Night result.

Each target uses exactly three complete Box candidates and three
independent random Box controls. A hit requires every digit,
including multiplicity, in any order. The offline *true expected*
Box wins use known synthetic probabilities strictly for evaluation.
These experiments do NOT demonstrate how Virginia's actual drawing
equipment operates or that historical lottery numbers are predictable.

| Game | Artificial mechanism | Future Night draws | Candidate Box wins | Random Box wins | Candidate oracle expected | Random oracle expected | Signal-on draws | Gated mean Box log gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 2250 | 39 | 29 | 40.50 | 40.50 | 0 | +0.00000 |
| pick3 | fixed_position_small | 2250 | 43 | 48 | 40.51 | 40.49 | 0 | +0.00000 |
| pick3 | fixed_position_strong | 2250 | 44 | 45 | 42.31 | 40.61 | 326 | +0.00485 |
| pick3 | pooled_device_bias | 2250 | 37 | 45 | 42.03 | 40.25 | 316 | +0.00600 |
| pick3 | day_only_bias | 2250 | 39 | 33 | 40.50 | 40.50 | 0 | +0.00000 |
| pick3 | halfway_replacement | 2250 | 43 | 36 | 44.96 | 39.78 | 617 | +0.02653 |
| pick3 | hidden_opposing_machines | 2250 | 36 | 48 | 39.68 | 39.74 | 0 | +0.00000 |
| pick3 | within_draw_echo | 2250 | 22 | 12 | 19.85 | 19.85 | 0 | +0.00000 |
| pick4 | fair_independent | 2250 | 11 | 12 | 16.20 | 16.20 | 0 | +0.00000 |
| pick4 | fixed_position_small | 2250 | 16 | 19 | 16.20 | 16.20 | 0 | +0.00000 |
| pick4 | fixed_position_strong | 2250 | 16 | 10 | 16.67 | 16.25 | 330 | +0.00237 |
| pick4 | pooled_device_bias | 2250 | 14 | 13 | 16.76 | 16.03 | 416 | +0.00533 |
| pick4 | day_only_bias | 2250 | 23 | 19 | 16.20 | 16.20 | 0 | +0.00000 |
| pick4 | halfway_replacement | 2250 | 25 | 19 | 16.38 | 15.45 | 304 | +0.01084 |
| pick4 | hidden_opposing_machines | 2250 | 14 | 22 | 16.56 | 15.65 | 679 | +0.00481 |
| pick4 | within_draw_echo | 2250 | 7 | 7 | 5.56 | 5.56 | 0 | +0.00000 |
| pick5 | fair_independent | 2250 | 7 | 7 | 8.10 | 8.10 | 0 | +0.00000 |
| pick5 | fixed_position_small | 2250 | 10 | 6 | 8.10 | 8.10 | 0 | +0.00000 |
| pick5 | fixed_position_strong | 2250 | 10 | 10 | 8.18 | 8.10 | 132 | +0.00077 |
| pick5 | pooled_device_bias | 2250 | 6 | 8 | 8.08 | 7.92 | 261 | +0.00836 |
| pick5 | day_only_bias | 2250 | 9 | 4 | 8.10 | 8.10 | 0 | +0.00000 |
| pick5 | halfway_replacement | 2250 | 8 | 8 | 7.74 | 7.56 | 207 | +0.00688 |
| pick5 | hidden_opposing_machines | 2250 | 7 | 8 | 8.57 | 7.53 | 1204 | +0.01128 |
| pick5 | within_draw_echo | 2250 | 1 | 1 | 1.94 | 1.94 | 0 | +0.00000 |

## Promotion discipline

The deployed VAL Box v4 generator remains unchanged by this challenge.
A synthetic win is useful evidence about the challenger's ability
to learn that hypothetical mechanism, NOT evidence of a Virginia
Lottery weakness. Real-time adoption requires a clean, prospective
improvement on actual future full Box outcomes and calibrated
probabilities compared with an equal-cost control.

[All results and paired counts](research_day_night_conditional.json).

