# VAL actual prediction formula v4 vs frozen v3

This tests the production number-generation functions on identical
prior histories, fixed target draws, and the same three-ticket budget.
If neither detects evidence, v3 and v4 use IDENTICAL random controls.
Every credited winner is a complete Any Order multiset match.
Results on artificial draws cannot establish a real lottery edge.
Real archive results are retrospective and previously inspected.

## Simulated machines

| Game | Machine condition | Target draws | v4 Box | v3 Box | Random Box | v4 gated | v3 gated | v4 log gain | v3 log gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 16 | 0 | 0 | 2 | 0 | 0 | +0.00000 | +0.00000 |
| pick3 | fixed_position_small | 16 | 1 | 1 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick3 | fixed_position_strong | 16 | 1 | 1 | 0 | 16 | 5 | +0.05788 | +0.01144 |
| pick3 | pooled_device_bias | 16 | 1 | 0 | 0 | 16 | 1 | +0.01771 | -0.00184 |
| pick3 | day_only_bias | 16 | 0 | 0 | 0 | 15 | 0 | -0.00435 | +0.00000 |
| pick3 | halfway_replacement | 16 | 1 | 1 | 2 | 15 | 8 | +0.01368 | +0.01006 |
| pick3 | hidden_opposing_machines | 16 | 0 | 0 | 2 | 0 | 0 | +0.00000 | +0.00000 |
| pick3 | within_draw_echo | 16 | 0 | 0 | 1 | 16 | 16 | +0.22343 | +0.11227 |
| pick4 | fair_independent | 16 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick4 | fixed_position_small | 16 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick4 | fixed_position_strong | 16 | 0 | 0 | 0 | 16 | 0 | -0.01899 | +0.00000 |
| pick4 | pooled_device_bias | 16 | 0 | 0 | 0 | 16 | 1 | -0.01900 | -0.00023 |
| pick4 | day_only_bias | 16 | 1 | 0 | 0 | 16 | 1 | +0.02971 | -0.00028 |
| pick4 | halfway_replacement | 16 | 0 | 0 | 0 | 16 | 2 | +0.01066 | -0.00064 |
| pick4 | hidden_opposing_machines | 16 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick4 | within_draw_echo | 16 | 0 | 0 | 1 | 16 | 16 | +0.32543 | +0.15185 |
| pick5 | fair_independent | 16 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick5 | fixed_position_small | 16 | 1 | 1 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick5 | fixed_position_strong | 16 | 0 | 0 | 0 | 16 | 3 | +0.00654 | -0.00204 |
| pick5 | pooled_device_bias | 16 | 0 | 0 | 0 | 16 | 0 | +0.05833 | +0.00000 |
| pick5 | day_only_bias | 16 | 0 | 0 | 1 | 16 | 2 | +0.01615 | +0.00044 |
| pick5 | halfway_replacement | 16 | 0 | 1 | 0 | 13 | 12 | +0.04288 | +0.03730 |
| pick5 | hidden_opposing_machines | 16 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick5 | within_draw_echo | 16 | 0 | 0 | 0 | 16 | 16 | +0.93432 | +0.35223 |

## Actual historical drawings (exploratory)

| Game | Targets | v4 full Box | v3 full Box | Random full Box | v4 gated | v3 gated | v4 mean log gain | v3 mean log gain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | 70 | 3 | 3 | 4 | 0 | 0 | +0.00000 | +0.00000 |
| pick4 | 70 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |
| pick5 | 40 | 0 | 0 | 0 | 0 | 0 | +0.00000 | +0.00000 |

A newly activated signal is not proof of genuine winning ability.
Live promotion requires correct probability calibration and
future full-Box confirmation against independent fair controls.

[Auditable target-level outcomes](research_box_v4_direct.json).

