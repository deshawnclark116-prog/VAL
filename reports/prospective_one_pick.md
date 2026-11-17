# VAL frozen future-draw one-number test

Latest run (UTC): 2026-11-17T05:12:16.219475+00:00

**Paper predictions only. No money wagered.**
Each named method gets one number for the same exact future
Day/Night draw. Entries are saved before wager close and can only
be scored against the identified official result.
Old predictions are not replaced or retargeted.

All contenders are frozen as version val_prospective_one_pick_v1.
Method selection followed exploratory historical testing; only
results **after this registry started** can independently test them.
A few hits cannot prove a persistent lottery advantage.

## Pick3

Draws recorded: 3. Graded: 2. Pending: 1.

| Method | Paper picks graded | Straight | Any Order | Fair expected Any Order | Average log-score vs fair |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 2 | 0 | 0 | 0.012 | +0.00000 |
| position_hot_top_500 | 2 | 0 | 0 | 0.012 | +0.11948 |
| position_cold_top_30 | 2 | 0 | 0 | 0.009 | -0.01322 |
| session_hier_sample_500 | 2 | 0 | 0 | 0.012 | +0.12762 |
| position_cold_sample_1000 | 2 | 0 | 0 | 0.009 | -0.02070 |

Most recent future target: 2026-11-17 Day; created 2026-11-17T05:12:16.219475+00:00.

Precommitted paper numbers: random: 204, position_hot_top_500: 242, position_cold_top_30: 814, session_hier_sample_500: 499, position_cold_sample_1000: 824.

## Pick4

Draws recorded: 3. Graded: 2. Pending: 1.

| Method | Paper picks graded | Straight | Any Order | Fair expected Any Order | Average log-score vs fair |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 2 | 0 | 1 | 0.004 | +0.00000 |
| position_hot_top_500 | 2 | 0 | 0 | 0.005 | -0.04374 |
| position_cold_top_30 | 2 | 0 | 0 | 0.005 | -0.02500 |
| session_hier_sample_500 | 2 | 0 | 0 | 0.002 | +0.07336 |
| position_cold_sample_1000 | 2 | 0 | 0 | 0.005 | -0.02274 |

Most recent future target: 2026-11-17 Day; created 2026-11-17T05:12:16.219475+00:00.

Precommitted paper numbers: random: 4517, position_hot_top_500: 0928, position_cold_top_30: 7317, session_hier_sample_500: 3705, position_cold_sample_1000: 6082.

## Pick5

Draws recorded: 3. Graded: 2. Pending: 1.

| Method | Paper picks graded | Straight | Any Order | Fair expected Any Order | Average log-score vs fair |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 2 | 0 | 0 | 0.002 | +0.00000 |
| position_hot_top_500 | 2 | 0 | 0 | 0.001 | +0.28396 |
| position_cold_top_30 | 2 | 0 | 0 | 0.002 | +0.00917 |
| session_hier_sample_500 | 2 | 0 | 0 | 0.001 | +0.26437 |
| position_cold_sample_1000 | 2 | 0 | 0 | 0.002 | -0.05320 |

Most recent future target: 2026-11-17 Day; created 2026-11-17T05:12:16.219475+00:00.

Precommitted paper numbers: random: 31040, position_hot_top_500: 40441, position_cold_top_30: 74654, session_hier_sample_500: 10257, position_cold_sample_1000: 87057.

## Reliability

- Only verified earlier public drawing results may train a method.
- Day/Night target and sales-closing time are fixed and logged.
- Any Order counts account for ticket digit multiplicity.
- FIREBALL is only evaluated when the actual official result reports it.
- Scores do not establish profitability or predictive advantage.
- The independent random control is retained, including all losses.
- Some official archives lag; pending picks are not assumed to lose.

Full append-only prediction ledger: [prospective_one_pick.json](prospective_one_pick.json).

