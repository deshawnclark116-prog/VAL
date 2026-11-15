# VAL method challengers: historical research

Produced: 2026-11-15T23:46:07.519574+00:00

**Exploratory replay, not evidence of predictable lottery outcomes.**
Each method makes 10,000 predictions per game on identical real historical draws.
Predictions only use earlier outcomes; model definitions were selected after
a previous analysis of overlapping history, so neither the full replay
nor the last-third segment is an independent untouched confirmation.
Live VAL predictions, ranked primary, random controls, and ledger are unchanged.

New approaches: Bayes Long (smoothed long-run digit position counts),
Decay 30 (recency-weighted), Session Hier (Day/Night context),
Transition (last-draw digit dependencies), Pair Chain (within-number digit
dependencies), Echo Repeat (same-position repeats from preceding draw).

Straight counts full ordered matches. Any Order counts the correct
digit multiset (including Straights); Box-only excludes Straights.
FIREBALL Any Order is separate and overlaps ordinary matches.
All outcomes are simulated paper plays, not actual winning tickets.

## Pick 3

1122 actual test drawings; 10,000 predictions per method.

| Method | Straight | Any Order | FIREBALL Any Order | Expected Any Order (fair) | Mean log-score edge vs fair (nats/draw) |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 14 | 57 | 157 | 51.4 | +0.00000 |
| ensemble | 12 | 58 | 150 | 51.4 | -0.03493 |
| bayes_long | 9 | 53 | 148 | 51.4 | -0.02391 |
| decay_30 | 9 | 51 | 135 | 51.7 | -0.04442 |
| session_hier | 9 | 53 | 147 | 51.6 | -0.03754 |
| transition | 8 | 58 | 149 | 51.5 | -0.09702 |
| pair_chain | 6 | 48 | 145 | 51.6 | -0.06743 |
| echo_repeat | 10 | 39 | 147 | 51.3 | -0.02316 |

The log-score statistic assigns a probability to the actual full
ordered draw before seeing it; positive is better than a uniform
fair model, negative is worse. This is an exploratory comparison.
Method rankings may be dominated by chance and multiple testing.

## Pick 4

1122 actual test drawings; 10,000 predictions per method.

| Method | Straight | Any Order | FIREBALL Any Order | Expected Any Order (fair) | Mean log-score edge vs fair (nats/draw) |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 0 | 22 | 63 | 17.5 | +0.00000 |
| ensemble | 0 | 12 | 74 | 17.7 | -0.04751 |
| bayes_long | 1 | 19 | 67 | 17.7 | -0.03912 |
| decay_30 | 0 | 12 | 48 | 17.6 | -0.06321 |
| session_hier | 3 | 16 | 76 | 17.7 | -0.05259 |
| transition | 1 | 17 | 74 | 17.5 | -0.15721 |
| pair_chain | 0 | 13 | 60 | 17.6 | -0.10839 |
| echo_repeat | 1 | 14 | 47 | 17.7 | -0.03733 |

The log-score statistic assigns a probability to the actual full
ordered draw before seeing it; positive is better than a uniform
fair model, negative is worse. This is an exploratory comparison.
Method rankings may be dominated by chance and multiple testing.

## Pick 5

1122 actual test drawings; 10,000 predictions per method.

| Method | Straight | Any Order | FIREBALL Any Order | Expected Any Order (fair) | Mean log-score edge vs fair (nats/draw) |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 0 | 4 | 19 | 7.1 | +0.00000 |
| ensemble | 1 | 7 | 28 | 7.1 | -0.05375 |
| bayes_long | 0 | 7 | 30 | 7.2 | -0.04663 |
| decay_30 | 0 | 9 | 29 | 7.1 | -0.07190 |
| session_hier | 0 | 5 | 33 | 7.1 | -0.06428 |
| transition | 1 | 10 | 32 | 7.2 | -0.20596 |
| pair_chain | 0 | 6 | 21 | 7.2 | -0.16224 |
| echo_repeat | 1 | 12 | 27 | 7.1 | -0.05108 |

The log-score statistic assigns a probability to the actual full
ordered draw before seeing it; positive is better than a uniform
fair model, negative is worse. This is an exploratory comparison.
Method rankings may be dominated by chance and multiple testing.

## What would justify a promotion?

Do not promote a method on these replay results. First freeze its settings;
then evaluate future draws that were not available while selecting models.
Require repeatable improvement in precommitted log scoring and target-draw
outcomes over random controls, with uncertainty and multiple tests accounted
for. A fair lottery supplies no persistent exploitable prediction signal.

