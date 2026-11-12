# VAL daily report

Generated: 2026-11-12T22:44:24.465232+00:00 · Eastern date: 2026-11-12

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Each batch targets the first draw in its selected session on an Eastern date **after its creation date**. Same-day draws are excluded. Picks for games without a draw tomorrow wait for their next eligible draw.

Three unique combinations per game/session, with three saved random control combinations. Re-running on the same Eastern date reuses saved batches.

| Game | Session | Batch | Combinations | Latest loaded draw (ET) |
| --- | --- | --- | --- | --- |
| Pick 3 | Day | #1 | `2 6 4` / `9 6 5` / `8 2 2` | 2026-11-11T13:59:00-05:00 |
| Pick 3 | Night | #2 | `9 3 9` / `4 6 9` / `6 0 0` | 2026-11-11T23:00:00-05:00 |
| Pick 4 | Day | #3 | `5 8 9 0` / `1 3 7 7` / `9 4 6 8` | 2026-11-11T13:59:00-05:00 |
| Pick 4 | Night | #4 | `0 3 3 5` / `3 2 1 0` / `2 2 5 1` | 2026-11-11T23:00:00-05:00 |
| Pick 5 | Day | #5 | `8 0 1 6 8` / `1 4 1 3 4` / `0 0 1 5 9` | 2026-11-11T13:59:00-05:00 |
| Pick 5 | Night | #6 | `3 5 5 1 4` / `3 9 3 6 8` / `4 7 3 7 0` | 2026-11-11T23:00:00-05:00 |
| Cash 5 | Main | #7 | `5 11 13 20 29` / `5 17 35 37 38` / `2 16 19 20 44` | 2026-11-11T23:00:00-05:00 |
| Powerball | Main | #8 | `19 32 40 52 67 + 5` / `3 4 7 62 63 + 18` / `8 9 38 59 69 + 19` | 2026-11-11T22:59:00-05:00 |
| Mega Millions | Main | #9 | `5 39 60 61 63 + 1` / `9 17 25 36 47 + 22` / `4 19 27 34 50 + 1` | 2026-11-10T23:00:00-05:00 |
| Millionaire for Life | Main | #10 | `2 27 42 54 58 + 1` / `6 24 32 42 49 + 3` / `2 15 38 43 45 + 4` | 2026-11-11T23:15:00-05:00 |
| Bank a Million | Main | #11 | `12 25 29 35 39 40` / `15 17 18 34 35 40` / `15 20 28 30 31 36` | 2026-11-11T23:00:00-05:00 |
| Cash Pop | Coffee Break | #12 | `11` / `4` / `2` | 2026-11-12T09:00:00-05:00 |
| Cash Pop | Lunch Break | #13 | `8` / `7` / `4` | 2026-11-12T12:00:00-05:00 |
| Cash Pop | Rush Hour | #14 | `4` / `8` / `7` | 2026-11-12T17:00:00-05:00 |
| Cash Pop | Prime Time | #15 | `6` / `10` / `9` | 2026-11-11T21:00:00-05:00 |
| Cash Pop | After Hours | #16 | `2` / `8` / `14` | 2026-11-11T23:59:00-05:00 |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 0 | 0 | 0 | 0 | 0 |
| Pick 4 | 0 | 0 | 0 | 0 | 0 |
| Pick 5 | 0 | 0 | 0 | 0 | 0 |
| Cash 5 | 0 | 0 | 0 | 0 | 0 |
| Powerball | 0 | 0 | 0 | 0 | 0 |
| Mega Millions | 0 | 0 | 0 | 0 | 0 |
| Millionaire for Life | 0 | 0 | 0 | 0 | 0 |
| Bank a Million | 0 | 0 | 0 | 0 | 0 |
| Cash Pop | 0 | 0 | 0 | 0 | 0 |

Pending batches: 16. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 0 / 300 | 0.3217 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9441 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.8212 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4555 |
| Powerball | 0 / 300 | 0 / 300 | 0.7163 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3816 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7502 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3816 |
| Cash Pop | 19 / 300 | 20 / 300 | 0.5734 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Pick 3/4/5 have separate Day and Night picks; Cash Pop has five separate sessions. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

All nine automatic history updates and analyses completed.
