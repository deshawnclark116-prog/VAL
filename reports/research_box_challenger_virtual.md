# VAL cumulative-evidence Box challenger: virtual-draw check

All wins require the COMPLETE digit multiset including repeats.
Three paper Box tickets per sampled target, no purchases.
Candidate evidence uses strictly earlier draws. It must cross
a conservative anytime threshold against the iid uniform null.
No production forecast or previously saved pick was modified.

**These are simulated devices with injected distributions,
not evidence of exploitable Virginia Lottery machinery.**

| Game | Scenario | Signal-active draws | Box trial draws | Challenger Box | Random Box | Candidate true-expected Box | Control true-expected Box | Mean log gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 0 | 52 | 1 | 0 | 0.936 | 0.936 | +0.000000 |
| pick3 | fixed_position_small | 0 | 52 | 4 | 0 | 0.946 | 0.940 | +0.000000 |
| pick3 | fixed_position_strong | 1300 | 52 | 1 | 3 | 1.227 | 0.955 | +0.053152 |
| pick3 | pooled_device_bias | 1300 | 52 | 0 | 3 | 1.225 | 0.949 | +0.017689 |
| pick3 | day_only_bias | 1300 | 52 | 2 | 0 | 1.145 | 0.938 | +0.031044 |
| pick3 | halfway_replacement | 1300 | 52 | 3 | 1 | 1.359 | 0.903 | +0.032081 |
| pick3 | hidden_opposing_machines | 0 | 52 | 0 | 0 | 0.921 | 0.881 | +0.000000 |
| pick3 | within_draw_echo | 1300 | 52 | 1 | 1 | 0.808 | 0.459 | +0.392268 |
| pick4 | fair_independent | 0 | 52 | 0 | 0 | 0.374 | 0.374 | +0.000000 |
| pick4 | fixed_position_small | 0 | 52 | 1 | 1 | 0.374 | 0.373 | +0.000000 |
| pick4 | fixed_position_strong | 1300 | 52 | 1 | 1 | 0.449 | 0.366 | +0.051999 |
| pick4 | pooled_device_bias | 1300 | 52 | 1 | 0 | 0.465 | 0.358 | +0.020902 |
| pick4 | day_only_bias | 1300 | 52 | 1 | 0 | 0.437 | 0.364 | +0.019262 |
| pick4 | halfway_replacement | 1300 | 52 | 1 | 1 | 0.489 | 0.371 | +0.047739 |
| pick4 | hidden_opposing_machines | 0 | 52 | 0 | 0 | 0.384 | 0.349 | +0.000000 |
| pick4 | within_draw_echo | 1300 | 52 | 2 | 0 | 0.309 | 0.128 | +0.595427 |
| pick5 | fair_independent | 0 | 52 | 0 | 0 | 0.187 | 0.187 | +0.000000 |
| pick5 | fixed_position_small | 31 | 52 | 0 | 1 | 0.188 | 0.187 | -0.001832 |
| pick5 | fixed_position_strong | 1300 | 52 | 1 | 0 | 0.212 | 0.188 | +0.040017 |
| pick5 | pooled_device_bias | 1300 | 52 | 0 | 0 | 0.221 | 0.184 | +0.030941 |
| pick5 | day_only_bias | 1300 | 52 | 0 | 0 | 0.209 | 0.186 | +0.022368 |
| pick5 | halfway_replacement | 1300 | 52 | 1 | 0 | 0.217 | 0.165 | +0.052310 |
| pick5 | hidden_opposing_machines | 0 | 52 | 0 | 0 | 0.174 | 0.175 | +0.000000 |
| pick5 | within_draw_echo | 1300 | 52 | 0 | 0 | 0.129 | 0.045 | +0.894858 |

## Decision

Only future, immutable predictions that demonstrate an actual
full-Box edge and pass a precommitted statistical rule can
justify promotion to production. False positive and false negative
behavior in simulations is diagnostic, never proof of a live edge.

