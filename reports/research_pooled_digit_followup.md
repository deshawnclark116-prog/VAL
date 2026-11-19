# VAL pooled-digit candidate: year/session robustness audit

**This candidate was identified after inspecting historical data.**
The results are exploratory and cannot establish a new edge.
The exact same formula was replayed through all available years
without seeing each target draw until after its prediction.
The 5,000-draw rolling window and 200-per-position digit prior
were held fixed throughout.

Fair chance for the top selected digit in any specified position
is 10%. A full Straight win requires the entire ordered result;
position hits alone are not prizes.

| Game | Period | Draws | Top-1 hit rate | Top-3 coverage | Mean log gain vs fair | Exact winners |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| pick3 | all | 23257 | 9.84% | 29.59% | -0.000660 | 24 |
| pick3 | year_2023 | 730 | 9.77% | 30.32% | -0.000087 | 0 |
| pick3 | year_2024 | 732 | 9.74% | 27.91% | -0.001958 | 0 |
| pick3 | year_2025 | 730 | 10.68% | 31.14% | +0.000151 | 2 |
| pick3 | year_2026 | 642 | 11.32% | 31.62% | +0.001140 | 0 |
| pick3 | stream_Day | 10991 | 9.65% | 29.57% | -0.000546 | 10 |
| pick3 | stream_Night | 12266 | 10.01% | 29.60% | -0.000763 | 14 |
| pick3 | recent_Day | 686 | 10.74% | 30.81% | +0.000417 | 1 |
| pick3 | recent_Night | 686 | 11.22% | 31.92% | +0.000810 | 1 |
| pick3 | 2026_Day | 321 | 10.90% | 30.63% | +0.000922 | 0 |
| pick3 | 2026_Night | 321 | 11.73% | 32.61% | +0.001357 | 0 |
| pick4 | all | 22523 | 10.09% | 29.97% | -0.000616 | 3 |
| pick4 | year_2023 | 730 | 9.86% | 30.03% | -0.000614 | 0 |
| pick4 | year_2024 | 732 | 10.38% | 30.23% | -0.000230 | 0 |
| pick4 | year_2025 | 730 | 10.24% | 28.84% | -0.001293 | 1 |
| pick4 | year_2026 | 642 | 9.70% | 30.49% | -0.000399 | 0 |
| pick4 | stream_Day | 10991 | 10.30% | 30.17% | -0.000337 | 1 |
| pick4 | stream_Night | 11532 | 9.88% | 29.78% | -0.000883 | 2 |
| pick4 | recent_Day | 686 | 11.08% | 30.79% | +0.000455 | 0 |
| pick4 | recent_Night | 686 | 8.89% | 28.43% | -0.002205 | 1 |
| pick4 | 2026_Day | 321 | 10.90% | 31.54% | +0.001153 | 0 |
| pick4 | 2026_Night | 321 | 8.49% | 29.44% | -0.001951 | 0 |
| pick5 | all | 2024 | 10.19% | 29.79% | -0.000392 | 0 |
| pick5 | year_2024 | 652 | 9.08% | 30.34% | -0.000272 | 0 |
| pick5 | year_2025 | 730 | 10.27% | 29.21% | -0.001563 | 0 |
| pick5 | year_2026 | 642 | 11.21% | 29.91% | +0.000818 | 0 |
| pick5 | stream_Day | 1012 | 10.47% | 29.80% | -0.000004 | 0 |
| pick5 | stream_Night | 1012 | 9.90% | 29.78% | -0.000780 | 0 |
| pick5 | recent_Day | 686 | 11.43% | 30.00% | +0.000421 | 0 |
| pick5 | recent_Night | 686 | 10.00% | 29.07% | -0.001319 | 0 |
| pick5 | 2026_Day | 321 | 12.52% | 31.09% | +0.003691 | 0 |
| pick5 | 2026_Night | 321 | 9.91% | 28.72% | -0.002055 | 0 |

## Decision

No favorable row is grounds for promotion; the model was
chosen after other VAL backtests had been inspected. A real
test is an immutable forecast ledger covering every future
drawing with its saved prediction, fair odds and controls.

[Raw period-level results](research_pooled_digit_followup.json).

