# VAL v3 pooled-digit future accuracy trial

New forecast specification frozen BEFORE each individual drawing.
Never retargets or replaces saved forecasts and controls.
**This candidate was selected after historical exploration.**
Its credibility depends entirely on subsequent real-world draws.

Top-1 forecast checks one digit in each position (chance 10%).
Top-three digit coverage checks three guesses per position (chance 30%).
Ticket metrics check complete ordered tickets independently.
Top-1 successes and partial matches are not prize claims.

| Game | Settled draws | Top-1 digit hit rate | Top-3 coverage | Model exact | Uniform exact | Mean log gain | Anytime e-value trigger |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| pick3 | 0 | — | — | 0 | 0 | — | No |
| pick4 | 0 | — | — | 0 | 0 | — | No |
| pick5 | 0 | — | — | 0 | 0 | — | No |

Fair e-value evidence threshold is log(60) with a
three-game union-bound allocation; it begins at the first
future saved prediction and is not a historical backtest p-value.
A threshold crossing alone warrants source and regime auditing,
not claims of profitable lottery prediction.

[Immutable prediction records](prospective_pooled_digit_v3.json).

