# VAL v3: test new prediction FORMULAS on real later drawings

This evaluates eight **previously unimplemented contextual
prediction hypotheses** against fair uniform probability, using
only strictly earlier official results. Every method is checked
for ordered next-draw likelihood, its top digit in each position,
three most likely digits in each position, and a complete
highest-scoring Straight number. All models are fixed before
the later test segment, with no holdout-based parameter tuning.

The archive itself has been inspected in prior VAL experiments,
so this remains historical exploratory research rather than
untouched future proof.

Top-1 fair expectation = **10%**, top-3 = **30%** of positions.
E-value log threshold controls a hypothetical frozen study over
eight methods × three games at family-wise 5% under iid fair
draws; a historical threshold crossing would still need future
replication. The running maximum checks every past prefix.

| Game | Method | Later draws | Top-digit accuracy | Top-3 coverage | Complete Straight hits | Fair-relative log gain | Anytime gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| pick3 | historical_5000 | 950 | 10.35% | 31.68% | 2 | +0.001024 | No |
| pick3 | weekday_session | 950 | 9.65% | 29.51% | 0 | -0.007671 | No |
| pick3 | month_session | 950 | 9.23% | 30.25% | 0 | -0.001990 | No |
| pick3 | two_draw_lag | 950 | 9.96% | 30.18% | 0 | -0.003167 | No |
| pick3 | pooled_digit_bias | 950 | 11.44% | 31.79% | 2 | +0.001077 | No |
| pick3 | cold_60 | 950 | 10.42% | 31.44% | 1 | -0.000250 | No |
| pick3 | previous_sum | 950 | 10.63% | 30.28% | 1 | -0.004973 | No |
| pick3 | previous_set_presence | 950 | 10.04% | 29.58% | 0 | -0.022518 | No |
| pick4 | historical_5000 | 950 | 9.29% | 29.92% | 0 | -0.003849 | No |
| pick4 | weekday_session | 950 | 9.37% | 30.21% | 0 | -0.001194 | No |
| pick4 | month_session | 950 | 10.11% | 30.03% | 0 | -0.002244 | No |
| pick4 | two_draw_lag | 950 | 10.00% | 30.45% | 0 | -0.005999 | No |
| pick4 | pooled_digit_bias | 950 | 9.76% | 30.03% | 0 | -0.001349 | No |
| pick4 | cold_60 | 950 | 9.97% | 30.34% | 0 | +0.000909 | No |
| pick4 | previous_sum | 950 | 9.08% | 29.42% | 0 | -0.006110 | No |
| pick4 | previous_set_presence | 950 | 9.26% | 30.47% | 0 | -0.038032 | No |
| pick5 | historical_5000 | 950 | 10.46% | 31.26% | 0 | -0.001241 | No |
| pick5 | weekday_session | 950 | 10.32% | 29.94% | 0 | -0.002686 | No |
| pick5 | month_session | 950 | 10.82% | 29.81% | 0 | -0.004172 | No |
| pick5 | two_draw_lag | 950 | 9.85% | 30.00% | 0 | -0.009974 | No |
| pick5 | pooled_digit_bias | 950 | 10.99% | 29.66% | 0 | +0.000495 | No |
| pick5 | cold_60 | 950 | 10.65% | 31.12% | 0 | -0.000728 | No |
| pick5 | previous_sum | 950 | 9.18% | 29.22% | 0 | -0.007266 | No |
| pick5 | previous_set_presence | 950 | 10.32% | 30.19% | 0 | -0.064197 | No |

## Promotion protocol

A challenger must beat uniform on strict next-draw probability
accuracy, and independently demonstrate predictive value on
future time-stamped draws, with its complete model specification
and e-value gate frozen beforehand. A few high partial-hit
numbers or fortunate exact wins do not establish a repeatable edge.
No production prediction formula is automatically switched.

[Complete results](research_digit_accuracy_v3.json).

