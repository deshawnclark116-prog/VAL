# VAL v2 — random-control jackpot anomaly audit

The fixed head-to-head replay produced unusually high Pick 4 exact
winners for one deterministic random control. That is a rare
multiple-testing hazard, **not** evidence the timestamp seed
predicts a fair lottery. We replicated 500 *independent* random
controls against the identical pre-selected target drawings.
No seed is selected for live bets; this audit only measures the null.

| Game | Target draws | Original control wins | Fair expected wins | Exact fair-tail P(>= observed) | 500-control average wins |
| --- | ---: | ---: | ---: | ---: | ---: |
| pick3 | 220 | 2 | 0.660 | 0.141852 | 0.700 |
| pick4 | 220 | 3 | 0.066 | 4.50156e-05 | 0.064 |
| pick5 | 120 | 0 | 0.004 | 1 | 0.000 |

Each single-control fair tail assumes truly independent
uniform draws and unique three-ticket selections. The original
control seed was just one of many models, games, experiments and
comparisons inspected, so its one-shot p-value does NOT establish
predictive power. Multiple-testing adjustment and future
precommitted replication are required.

Raw results: [research_digit_formula_placebos.json](research_digit_formula_placebos.json).

