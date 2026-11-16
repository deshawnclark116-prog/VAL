# VAL: one prediction per drawing, historical walk-forward research

Generated: 2026-11-16T00:16:22.528213+00:00

**Research only. No winning advantage has been demonstrated.**
Every method generates **one** digit combination for every real future
historical drawing on the same eligibility dates, with only strictly
earlier results used in training. No live VAL picks have changed.

Compared history windows: 30, 100, 500, 1,000, 5,000 prior draws
(5,000 unavailable for Pick 5, whose archive is shorter).
Methods: positional hot/cold, pooled hot, Day-versus-Night
hierarchical frequencies. Each uses a single *top-scoring* ticket
or a single random sample from the same probability model.
Controls: unrestricted uniform random and random all-distinct digits.

**Important Any Order distinction:** The all-distinct baseline covers
more orderings than tickets with repeated digits. Its higher chance
of an Any Order match is mathematical coverage, NOT prediction.
Every method is compared with the expected number of Any Order hits
for the exact digit compositions it actually chose.

Straight counts exact order. Any Order includes Straight. FIREBALL
Any Order is separate, and only applies after FIREBALL was introduced.
Methods were chosen after inspecting earlier historical experiments;
so even results on older years are **exploratory, not clean confirmation**.
With dozens of comparisons a lucky leader is expected; no retrospective
winner is promoted without an untouched future validation period.

## Pick3

History: 23,751 draws. One-number test:
**18,751 actual drawings**,
2000-03-25 to 2026-11-14.

| Prediction method | Exact Straight | Any Order | Fair-expected Any Order | Fireball Any Order | Log-score gain vs fair |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 27 | 107 | 96.7 | 58 | +0.00000 |
| random_distinct | 23 | 104 | 112.5 | 63 | +0.00000 |
| position_hot_top_30 | 23 | 108 | 96.4 | 61 | -0.00841 |
| position_hot_sample_30 | 19 | 100 | 96.3 | 50 | -0.00841 |
| position_cold_top_30 | 22 | 116 | 96.8 | 58 | -0.00138 |
| position_cold_sample_30 | 12 | 107 | 96.2 | 59 | -0.00138 |
| pooled_hot_top_30 | 19 | 20 | 25.2 | 13 | -0.00275 |
| pooled_hot_sample_30 | 23 | 90 | 96.3 | 45 | -0.00275 |
| session_hier_top_30 | 20 | 105 | 95.8 | 64 | -0.09395 |
| session_hier_sample_30 | 15 | 90 | 96.4 | 54 | -0.09395 |
| position_hot_top_100 | 15 | 91 | 96.4 | 64 | -0.01612 |
| position_hot_sample_100 | 24 | 86 | 96.4 | 57 | -0.01612 |
| position_cold_top_100 | 22 | 90 | 97.7 | 63 | -0.00288 |
| position_cold_sample_100 | 22 | 105 | 96.6 | 60 | -0.00288 |
| pooled_hot_top_100 | 20 | 27 | 22.6 | 12 | -0.00546 |
| pooled_hot_sample_100 | 15 | 90 | 96.6 | 63 | -0.00546 |
| session_hier_top_100 | 20 | 101 | 94.9 | 43 | -0.11504 |
| session_hier_sample_100 | 22 | 101 | 96.4 | 59 | -0.11504 |
| position_hot_top_500 | 20 | 86 | 93.3 | 52 | -0.01519 |
| position_hot_sample_500 | 19 | 96 | 96.4 | 58 | -0.01519 |
| position_cold_top_500 | 19 | 88 | 95.0 | 56 | -0.00221 |
| position_cold_sample_500 | 20 | 101 | 96.8 | 44 | -0.00221 |
| pooled_hot_top_500 | 16 | 21 | 20.7 | 7 | -0.00515 |
| pooled_hot_sample_500 | 20 | 97 | 96.2 | 56 | -0.00515 |
| session_hier_top_500 | 10 | 67 | 94.2 | 48 | -0.04821 |
| session_hier_sample_500 | 21 | 89 | 96.8 | 63 | -0.04821 |
| position_hot_top_1000 | 13 | 94 | 94.5 | 56 | -0.00965 |
| position_hot_sample_1000 | 17 | 87 | 96.0 | 53 | -0.00965 |
| position_cold_top_1000 | 25 | 106 | 94.3 | 60 | -0.00165 |
| position_cold_sample_1000 | 25 | 102 | 96.3 | 50 | -0.00165 |
| pooled_hot_top_1000 | 14 | 16 | 20.1 | 11 | -0.00332 |
| pooled_hot_sample_1000 | 23 | 92 | 96.3 | 44 | -0.00332 |
| session_hier_top_1000 | 15 | 95 | 93.2 | 59 | -0.02567 |
| session_hier_sample_1000 | 15 | 89 | 96.3 | 66 | -0.02567 |
| position_hot_top_5000 | 21 | 94 | 102.2 | 47 | -0.00251 |
| position_hot_sample_5000 | 22 | 89 | 96.4 | 57 | -0.00251 |
| position_cold_top_5000 | 23 | 86 | 93.2 | 70 | -0.00013 |
| position_cold_sample_5000 | 22 | 99 | 96.3 | 67 | -0.00013 |
| pooled_hot_top_5000 | 17 | 17 | 19.6 | 9 | -0.00096 |
| pooled_hot_sample_5000 | 16 | 88 | 96.4 | 58 | -0.00096 |
| session_hier_top_5000 | 18 | 86 | 98.9 | 61 | -0.00509 |
| session_hier_sample_5000 | 22 | 100 | 96.2 | 60 | -0.00509 |

Log-score gain > 0 means the probabilistic model assigned
higher likelihood to actual ordered winners than uniform
probabilities. Both selection policies share identical log scores
because their underlying probability model is identical.

## Pick4

History: 23,017 draws. One-number test:
**18,017 actual drawings**,
2001-05-29 to 2026-11-14.

| Prediction method | Exact Straight | Any Order | Fair-expected Any Order | Fireball Any Order | Log-score gain vs fair |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 2 | 32 | 31.5 | 19 | +0.00000 |
| random_distinct | 0 | 35 | 43.2 | 34 | +0.00000 |
| position_hot_top_30 | 2 | 28 | 31.5 | 21 | -0.01141 |
| position_hot_sample_30 | 3 | 28 | 31.6 | 34 | -0.01141 |
| position_cold_top_30 | 1 | 26 | 31.8 | 29 | -0.00175 |
| position_cold_sample_30 | 2 | 28 | 31.6 | 26 | -0.00175 |
| pooled_hot_top_30 | 1 | 2 | 3.2 | 4 | -0.00331 |
| pooled_hot_sample_30 | 5 | 38 | 31.5 | 19 | -0.00331 |
| session_hier_top_30 | 4 | 27 | 31.7 | 16 | -0.12311 |
| session_hier_sample_30 | 1 | 29 | 31.7 | 21 | -0.12311 |
| position_hot_top_100 | 1 | 30 | 31.9 | 19 | -0.02133 |
| position_hot_sample_100 | 1 | 31 | 31.9 | 22 | -0.02133 |
| position_cold_top_100 | 1 | 19 | 31.7 | 25 | -0.00397 |
| position_cold_sample_100 | 1 | 39 | 31.7 | 18 | -0.00397 |
| pooled_hot_top_100 | 1 | 1 | 2.6 | 2 | -0.00578 |
| pooled_hot_sample_100 | 1 | 36 | 31.5 | 27 | -0.00578 |
| session_hier_top_100 | 1 | 28 | 32.4 | 19 | -0.15397 |
| session_hier_sample_100 | 1 | 24 | 31.7 | 20 | -0.15397 |
| position_hot_top_500 | 1 | 46 | 32.9 | 16 | -0.01915 |
| position_hot_sample_500 | 1 | 43 | 31.4 | 24 | -0.01915 |
| position_cold_top_500 | 1 | 44 | 32.4 | 32 | -0.00386 |
| position_cold_sample_500 | 0 | 25 | 31.5 | 19 | -0.00386 |
| pooled_hot_top_500 | 0 | 0 | 2.1 | 4 | -0.00468 |
| pooled_hot_sample_500 | 2 | 37 | 31.7 | 28 | -0.00468 |
| session_hier_top_500 | 1 | 28 | 32.4 | 25 | -0.06226 |
| session_hier_sample_500 | 1 | 30 | 31.7 | 26 | -0.06226 |
| position_hot_top_1000 | 2 | 25 | 32.4 | 22 | -0.01203 |
| position_hot_sample_1000 | 2 | 37 | 31.7 | 15 | -0.01203 |
| position_cold_top_1000 | 1 | 31 | 32.0 | 28 | -0.00311 |
| position_cold_sample_1000 | 4 | 41 | 31.7 | 25 | -0.00311 |
| pooled_hot_top_1000 | 3 | 3 | 2.0 | 1 | -0.00300 |
| pooled_hot_sample_1000 | 0 | 25 | 31.6 | 33 | -0.00300 |
| session_hier_top_1000 | 3 | 30 | 33.4 | 27 | -0.03318 |
| session_hier_sample_1000 | 3 | 31 | 31.7 | 20 | -0.03318 |
| position_hot_top_5000 | 1 | 29 | 30.3 | 21 | -0.00323 |
| position_hot_sample_5000 | 4 | 40 | 31.6 | 27 | -0.00323 |
| position_cold_top_5000 | 0 | 26 | 34.2 | 22 | -0.00101 |
| position_cold_sample_5000 | 2 | 32 | 31.8 | 24 | -0.00101 |
| pooled_hot_top_5000 | 2 | 2 | 1.9 | 3 | -0.00101 |
| pooled_hot_sample_5000 | 2 | 33 | 31.6 | 20 | -0.00101 |
| session_hier_top_5000 | 4 | 30 | 28.9 | 14 | -0.00608 |
| session_hier_sample_5000 | 2 | 27 | 31.8 | 30 | -0.00608 |

Log-score gain > 0 means the probabilistic model assigned
higher likelihood to actual ordered winners than uniform
probabilities. Both selection policies share identical log scores
because their underlying probability model is identical.

## Pick5

History: 2,518 draws. One-number test:
**1,518 actual drawings**,
2024-10-17 to 2026-11-14.

| Prediction method | Exact Straight | Any Order | Fair-expected Any Order | Fireball Any Order | Log-score gain vs fair |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 0 | 1 | 1.1 | 2 | +0.00000 |
| random_distinct | 0 | 1 | 1.8 | 4 | +0.00000 |
| position_hot_top_30 | 0 | 2 | 1.1 | 1 | -0.01000 |
| position_hot_sample_30 | 0 | 0 | 1.1 | 5 | -0.01000 |
| position_cold_top_30 | 0 | 0 | 1.1 | 6 | -0.00464 |
| position_cold_sample_30 | 0 | 1 | 1.1 | 3 | -0.00464 |
| pooled_hot_top_30 | 0 | 0 | 0.0 | 0 | -0.00247 |
| pooled_hot_sample_30 | 0 | 1 | 1.1 | 4 | -0.00247 |
| session_hier_top_30 | 0 | 0 | 1.1 | 7 | -0.15185 |
| session_hier_sample_30 | 0 | 0 | 1.1 | 7 | -0.15185 |
| position_hot_top_100 | 0 | 0 | 1.2 | 1 | -0.03047 |
| position_hot_sample_100 | 0 | 1 | 1.1 | 2 | -0.03047 |
| position_cold_top_100 | 0 | 1 | 1.1 | 3 | -0.00327 |
| position_cold_sample_100 | 0 | 1 | 1.1 | 7 | -0.00327 |
| pooled_hot_top_100 | 0 | 0 | 0.0 | 0 | -0.00476 |
| pooled_hot_sample_100 | 0 | 1 | 1.1 | 5 | -0.00476 |
| session_hier_top_100 | 0 | 2 | 1.1 | 3 | -0.19831 |
| session_hier_sample_100 | 0 | 2 | 1.1 | 4 | -0.19831 |
| position_hot_top_500 | 0 | 1 | 1.0 | 4 | -0.02553 |
| position_hot_sample_500 | 0 | 0 | 1.1 | 5 | -0.02553 |
| position_cold_top_500 | 0 | 1 | 1.2 | 6 | -0.00323 |
| position_cold_sample_500 | 0 | 0 | 1.1 | 3 | -0.00323 |
| pooled_hot_top_500 | 0 | 0 | 0.0 | 1 | -0.00454 |
| pooled_hot_sample_500 | 0 | 0 | 1.1 | 3 | -0.00454 |
| session_hier_top_500 | 0 | 2 | 1.1 | 4 | -0.07717 |
| session_hier_sample_500 | 0 | 4 | 1.1 | 10 | -0.07717 |
| position_hot_top_1000 | 0 | 1 | 0.9 | 2 | -0.01973 |
| position_hot_sample_1000 | 0 | 1 | 1.1 | 5 | -0.01973 |
| position_cold_top_1000 | 0 | 1 | 1.0 | 5 | +0.00023 |
| position_cold_sample_1000 | 0 | 2 | 1.1 | 2 | +0.00023 |
| pooled_hot_top_1000 | 0 | 0 | 0.0 | 0 | -0.00317 |
| pooled_hot_sample_1000 | 0 | 0 | 1.1 | 4 | -0.00317 |
| session_hier_top_1000 | 0 | 1 | 1.0 | 5 | -0.04554 |
| session_hier_sample_1000 | 0 | 3 | 1.1 | 7 | -0.04554 |

Log-score gain > 0 means the probabilistic model assigned
higher likelihood to actual ordered winners than uniform
probabilities. Both selection policies share identical log scores
because their underlying probability model is identical.

## Research decision

Keep the fair-uniform model as the null until a completely
future, frozen-rule test shows reliable improvement in log
probability with statistical uncertainty and multiple testing
accounted for. Exact-hit and Any Order deviations must also
outperform their relevant fair expected counts across years.

Full per-year and per-period breakdown: [research_one_pick.json](research_one_pick.json).

