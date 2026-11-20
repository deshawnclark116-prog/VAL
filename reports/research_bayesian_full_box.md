# VAL new Bayesian full Box formula vs previous pooled model

**REAL TESTS: actual Virginia Lottery outcomes in 2025/2026.**
Every target is scored chronologically with earlier drawings only.
These years have been inspected during previous VAL experiments;
therefore no positive retrospective result is independent proof.

All methods choose three distinct complete digit MULTISETS,
excluding all-identical Straight-only outcomes. Every hit must
match the entire multiset including repeated digits. Joint log
gain uses the target's full unordered Box probability, not the
accuracy of individual positions.

Exact bag: Dirichlet-smoothed empirical frequencies of each
whole multiset. Pair shape: normalized probability adjustment
using co-occurrence of *pairs* of digits (including duplicates).
The pooled model and fair random baseline receive the same
three-ticket budget.

## Actual real drawings

| Game | Period | Targets | Exact bag Box | Pair-shape Box | Pooled v2 Box | Random Box | Bag vs random 95% paired CI | Pair vs random 95% paired CI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| pick3 | 2025 | 730 | 11 | 6 | 13 | 18 | [-16, 3] | [-21, -4] |
| pick3 | 2026 | 646 | 13 | 9 | 9 | 11 | [-7, 11] | [-11, 6] |
| pick3 | combined | 1376 | 24 | 15 | 22 | 29 | [-20, 9] | [-25, -2] |
| pick4 | 2025 | 730 | 2 | 3 | 4 | 10 | [-15, -2] | [-14, 0] |
| pick4 | 2026 | 646 | 11 | 4 | 5 | 5 | [-2, 14] | [-7, 5] |
| pick4 | combined | 1376 | 13 | 7 | 9 | 15 | [-12, 10] | [-17, 1] |
| pick5 | 2025 | 730 | 3 | 1 | 4 | 6 | [-9, 3] | [-10, 0] |
| pick5 | 2026 | 646 | 1 | 2 | 2 | 1 | [-2, 3] | [-2, 5] |
| pick5 | combined | 1376 | 4 | 3 | 6 | 7 | [-10, 3] | [-11, 3] |

## Real full Box joint probability score

| Game | Exact bag log gain | Pair shape log gain | Pooled log gain |
| --- | ---: | ---: | ---: |
| pick3 | -0.012902 | -0.000475 | +0.000620 |
| pick4 | -0.031570 | -0.000608 | -0.000847 |
| pick5 | -0.062162 | -0.000135 | -0.000410 |

## Artificial-machine sanity tests

| Game | Hypothetical mechanism | Targets | Exact bag | Pair shape | Pooled | Fair random | Bag log gain | Pair log gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pick3 | fair_independent | 1400 | 27 | 26 | 28 | 25 | -0.00623 | +0.00004 |
| pick3 | within_draw_echo | 1400 | 17 | 12 | 17 | 11 | +0.26917 | +0.11436 |
| pick3 | favored_exact_box | 1400 | 112 | 110 | 111 | 19 | +0.06558 | +0.01582 |
| pick4 | fair_independent | 1400 | 13 | 20 | 16 | 10 | -0.02193 | +0.00022 |
| pick4 | within_draw_echo | 1400 | 2 | 2 | 2 | 2 | +0.32524 | +0.07362 |
| pick4 | favored_exact_box | 1400 | 76 | 75 | 66 | 13 | +0.06272 | +0.00592 |
| pick5 | fair_independent | 1400 | 4 | 4 | 7 | 4 | -0.05838 | -0.00028 |
| pick5 | within_draw_echo | 1400 | 2 | 2 | 1 | 3 | +0.26417 | +0.05411 |
| pick5 | favored_exact_box | 1400 | 69 | 70 | 68 | 10 | +0.05300 | +0.00128 |

## Promotion decision

Do not replace the live VAL model merely because the challenger
detects a pattern artificially injected into fake drawings.
Look for positive, repeatable and uncertainty-adjusted complete
Box performance AND proper probability-score improvement on
future real draws that were unknown when models were chosen.

The source used no official ball-set or machine IDs; there
is no basis here to assume the real draws match the simulator.

[Exact target-level picks, outcomes and metrics]
(research_bayesian_full_box.json).

