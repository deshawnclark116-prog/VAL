# Measurement-driven physical first-passage challenger

Status: research only; **not** a proven improvement on real Virginia Lottery outcomes. Production and wager behavior unchanged.

## Model

For a hypothetical air-driven chamber, effective acceleration is proportional to diameter squared divided by mass, under simplified drag assumptions. With independent exponentially distributed travel distances and travel time sqrt(2*distance/acceleration), the winning-ball law is categorical with probabilities proportional to acceleration. This is a tractable stochastic physical surrogate, not a CFD reconstruction of the actual apparatus. The measurement-based challenger estimates log mobility with prespecified Gaussian error shrinkage, marginalizes the randomly selected apparatus if it is hidden, and computes complete Box masses by summing every ordered permutation. It uses no previous winning numbers. An independent explicit travel-time race check (500,000 single-chamber trials) agreed with the analytic law; maximum absolute digit z-score 1.969. This verifies the mathematics under the assumed model, not its applicability to Virginia.

## Executed benchmark

Six independently parameterized synthetic equipment populations, four randomly selected hypothetical devices each, 20,000 independent simulated draws per population, 120,000 per game/scenario, 1,440,000 complete draws overall. The four scenarios are fair, small mobility variation, large illustrative variation, and a reversed-mechanism stress test. Noise, spread and device count are assumptions, not real equipment specifications. All models choose one complete Any Order combination. Actual synthetic draws are shared across methods; the predictor cannot access true parameters, except the explicitly labeled oracle. Expected hit lift is analytically evaluated under the generated truth, relative to the best fair all-distinct ticket; sampled hit counts and proper Box log scores are in the JSON.

| Game | Small variation, measured device | Large variation, hidden device but calibrated pool | Large variation, measured device | Wrong physics, measured device |
|---|---:|---:|---:|---:|
| Pick 3 | +0.67% | +10.81% | +23.15% | -20.11% |
| Pick 4 | +0.96% | +11.40% | +22.90% | -20.03% |
| Pick 5 | +1.09% | +9.94% | +20.58% | -18.60% |

All exact expected lifts were zero under the fair control. Finite simulation hit counts vary by chance. These conditional model-world expectations are not real effect estimates or confidence intervals. A well-calibrated model with correct physics may exploit informative measurements; wrong physics materially damages results.

## Real-world source and admission gate

Virginia Lottery's [Drawing Security](https://vl-cmsprd-594330-cd.azurewebsites.net/playingmatters/security) states that officials randomly select apparatus and ball sets, conduct equipment tests and pretests, and record equipment, pretest outcomes, winning outcomes and wager closure on a master control form. It does not publish per-ball measurement values, identify the apparatus model for every draw, or demonstrate that selected equipment or pretests are publicly available before the wager cutoff. Manufacturer [equipment descriptions](https://www.smartplay.com/lottery-products/lottery-draw-machines) establish that air- and gravity-mix designs exist, not that any particular model is installed in Virginia.

Do not treat private data, post-cutoff footage, generic equipment specifications or synthetic values as live features. With no lawful verified pre-cutoff measurements, the physical candidate abstains from claiming an advantage and cannot be real-world backtested as a measurement-driven model. To reopen: authenticated data, calibration of the actual mechanism, and immutable single-pick paper trials against full Box fair expectation and existing VAL models. No request for records has been sent.

## Reproduce

Run `node research/physical_first_passage.js` and `node research/physical_first_passage_check.js`. The former checks full probability normalization, exact fair combinatorics and oracle bounds. See [executed results](physical_first_passage_v1.json).
