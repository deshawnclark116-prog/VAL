# VAL next-draw report

Updated: 2026-11-13T14:49:50.592389-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-13T23:00:00-05:00 | Night | #33 | `4 9 9` / `5 2 7` / `8 0 2` | 2026-11-13T13:59:00-05:00 | `2 0 6` (Day) |
| Pick 4 | 2026-11-13T23:00:00-05:00 | Night | #34 | `9 2 9 2` / `4 2 7 7` / `3 9 8 4` | 2026-11-13T13:59:00-05:00 | `0 2 6 2` (Day) |
| Pick 5 | 2026-11-13T23:00:00-05:00 | Night | #35 | `9 2 4 0 3` / `4 9 7 4 4` / `4 5 4 1 8` | 2026-11-13T13:59:00-05:00 | `9 5 2 2 3` (Day) |
| Cash 5 | 2026-11-13T23:00:00-05:00 | Main | #30 | `3 10 14 18 27` / `1 35 37 43 44` / `3 6 22 30 32` | 2026-11-12T23:00:00-05:00 | `3 13 21 42 43` (Main) |
| Powerball | 2026-11-14T22:59:00-05:00 | Main | #21 | `5 11 43 60 66 + 11` / `2 30 39 40 66 + 20` / `17 34 37 55 57 + 22` | 2026-11-11T22:59:00-05:00 | `8 42 45 51 57 + 17` (Main) |
| Mega Millions | 2026-11-13T23:00:00-05:00 | Main | #22 | `13 33 34 45 46 + 12` / `1 3 13 27 30 + 17` / `6 26 28 49 66 + 16` | 2026-11-10T23:00:00-05:00 | `2 18 25 30 65 + 22` (Main) |
| Millionaire for Life | 2026-11-13T23:15:00-05:00 | Main | #31 | `10 11 27 32 33 + 5` / `6 13 17 22 56 + 1` / `27 35 41 56 57 + 3` | 2026-11-12T23:15:00-05:00 | `6 22 27 29 39 + 5` (Main) |
| Bank a Million | 2026-11-14T23:00:00-05:00 | Main | #24 | `2 19 22 24 27 36` / `3 9 22 26 36 39` / `8 15 22 24 27 30` | 2026-11-11T23:00:00-05:00 | `5 6 15 24 25 28` (Main) |
| Cash Pop | 2026-11-13T17:00:00-05:00 | Rush Hour | #36 | `15` / `11` / `7` | 2026-11-13T12:00:00-05:00 | `8` (Lunch Break) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 3 | 9 | 0 | 9 | 0 |
| Pick 4 | 3 | 9 | 0 | 9 | 0 |
| Pick 5 | 3 | 9 | 0 | 9 | 0 |
| Cash 5 | 1 | 3 | 0 | 3 | 0 |
| Powerball | 0 | 0 | 0 | 0 | 0 |
| Mega Millions | 0 | 0 | 0 | 0 | 0 |
| Millionaire for Life | 1 | 3 | 0 | 3 | 0 |
| Bank a Million | 0 | 0 | 0 | 0 | 0 |
| Cash Pop | 5 | 15 | 1 | 15 | 0 |

Pending batches: 20. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 1 / 300 | 0 / 300 | 0.4056 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9510 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.8102 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4236 |
| Powerball | 0 / 300 | 0 / 300 | 0.7163 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3786 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7882 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3816 |
| Cash Pop | 30 / 300 | 15 / 300 | 0.5215 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

All nine automatic history updates and analyses completed.
