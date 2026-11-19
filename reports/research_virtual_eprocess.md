# VAL virtual drawing lab — cumulative-evidence formula challenger

Tests a real algorithmic alternative to the deployed v2 gate.
Three *predictive probability formulas* are evaluated before each
virtual draw; their probabilities on actual future outcomes
accumulate likelihood-ratio evidence. A formula becomes active
only when accumulated evidence crosses a fixed, conservative
multiple-model threshold. On fair, independent draws this
procedure is designed not to invent persistent edges.

**These are artificial drawings with known injected patterns,
not historical Virginia Lottery outcomes.** Real-world
predictive advantage has not been established.

| Game | Synthetic scenario | Trials with signal | Signal-active test draws | New challenger top-1 | Fair top-1 | New log gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 0/8 | 0/5200 | 10.14% | 10.14% | +0.00000 |
| pick3 | fixed_position_small | 0/8 | 0/5200 | 9.94% | 9.94% | +0.00000 |
| pick3 | fixed_position_strong | 8/8 | 5200/5200 | 14.05% | 9.56% | +0.04465 |
| pick3 | pooled_device_bias | 8/8 | 5198/5200 | 14.01% | 9.56% | +0.01427 |
| pick3 | day_only_bias | 8/8 | 5089/5200 | 14.01% | 9.77% | +0.01926 |
| pick3 | halfway_replacement | 8/8 | 5200/5200 | 14.15% | 8.94% | +0.03041 |
| pick3 | hidden_opposing_machines | 0/8 | 0/5200 | 9.82% | 9.82% | +0.00000 |
| pick3 | within_draw_echo | 0/8 | 0/5200 | 10.26% | 10.26% | +0.00000 |
| pick4 | fair_independent | 0/8 | 0/5200 | 10.12% | 10.12% | +0.00000 |
| pick4 | fixed_position_small | 1/8 | 10/5200 | 9.74% | 9.75% | -0.00012 |
| pick4 | fixed_position_strong | 8/8 | 5200/5200 | 12.86% | 9.53% | +0.04216 |
| pick4 | pooled_device_bias | 8/8 | 5144/5200 | 14.30% | 9.54% | +0.02013 |
| pick4 | day_only_bias | 8/8 | 5192/5200 | 13.14% | 9.50% | +0.01689 |
| pick4 | halfway_replacement | 8/8 | 5200/5200 | 14.46% | 9.25% | +0.04790 |
| pick4 | hidden_opposing_machines | 0/8 | 0/5200 | 9.88% | 9.88% | +0.00000 |
| pick4 | within_draw_echo | 0/8 | 0/5200 | 10.16% | 10.16% | +0.00000 |
| pick5 | fair_independent | 0/8 | 0/5200 | 10.05% | 10.05% | +0.00000 |
| pick5 | fixed_position_small | 2/8 | 132/5200 | 9.87% | 9.93% | -0.00091 |
| pick5 | fixed_position_strong | 8/8 | 5200/5200 | 12.22% | 10.01% | +0.03480 |
| pick5 | pooled_device_bias | 8/8 | 5200/5200 | 14.24% | 9.47% | +0.02627 |
| pick5 | day_only_bias | 8/8 | 5200/5200 | 13.49% | 9.56% | +0.02671 |
| pick5 | halfway_replacement | 8/8 | 5200/5200 | 14.14% | 9.16% | +0.04594 |
| pick5 | hidden_opposing_machines | 0/8 | 0/5200 | 10.26% | 10.26% | +0.00000 |
| pick5 | within_draw_echo | 0/8 | 0/5200 | 9.64% | 9.64% | +0.00000 |

## Interpretation

Strong injected biases should be recoverable; weak effects
require much larger sample sizes. In the hidden-opposing
machine scenario, the unconditional digit distribution is
exactly uniform, making that mechanism unexploitable without
pre-wager information about the machine. The simulator's
perfect-information oracle is not a deployable model.

Any effect found in this controlled simulation must be retested
on fresh, real drawing outcomes before claiming accuracy gains.

[Raw results](research_virtual_eprocess.json).

