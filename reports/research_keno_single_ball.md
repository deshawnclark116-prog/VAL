# VAL Keno — ONE BALL predicted per drawing

A real 1-spot prediction: one number 1 through 80, and 20 winning
numbers in each official drawing. Fair hit probability: **25%**.
No five-number combinations and no three tickets.

Frozen official archive: 10,665 draws.
Training: 6,399 draws (2026-10-17T00:02:00 to 2026-11-04T04:58:00).
Later chronological test: 4,266 draws (2026-11-04T05:02:00 to 2026-11-16T09:45:30).

| One-ball method | Correct / draws | Hit rate | 95% Wilson interval | Adjusted p vs 25% | Earlier validation half | Later validation half |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| global_hot | 1054/4266 | 24.71% | 23.44–26.02% | 1 | 24.85% | 24.57% |
| recent_50_hot | 1076/4266 | 25.22% | 23.94–26.55% | 1 | 25.93% | 24.52% |
| recent_500_hot | 1032/4266 | 24.19% | 22.93–25.50% | 1 | 24.43% | 23.96% |
| recent_500_cold | 1099/4266 | 25.76% | 24.47–27.10% | 1 | 24.89% | 26.63% |
| last_draw_ball | 1100/4266 | 25.79% | 24.49–27.12% | 1 | 25.88% | 25.69% |
| time_bucket_hot | 1069/4266 | 25.06% | 23.78–26.38% | 1 | 24.47% | 25.64% |
| lag_transition | 1050/4266 | 24.61% | 23.34–25.93% | 1 | 25.04% | 24.19% |
| original_ensemble_weighted | 1112/4266 | 26.07% | 24.77–27.41% | 1 | 26.25% | 25.88% |
| random_control | 1071/4266 | 25.11% | 23.83–26.43% | 1 | 23.91% | 26.30% |

20 extra independent random controls each predicted one
ball per draw. Average correct rate 24.84%; range 23.91–26.02%.

Approximate binomial p-values use a continuity correction and
Bonferroni adjustment for nine strategies. Because test variants
were considered after earlier exploration of this archive, these
are descriptive historical checks rather than independent proof.
Winning numbers do NOT enter models until after their draw is scored.
Only true 1-ball hits counted. Not a five-spot prize calculation.
No live betting, no original VAL changes, no purchased tickets.

Detailed paired comparisons and pick audit:
[research_keno_single_ball.json](research_keno_single_ball.json).

