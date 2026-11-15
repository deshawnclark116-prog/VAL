# VAL next-draw report

Updated: 2026-11-15T09:47:10.476184-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-15T13:59:00-05:00 | Day | #51 | `8 8 6` / `1 9 6` / `9 7 2` | 2026-11-14T23:00:00-05:00 | `0 3 6` (Night) |
| Pick 4 | 2026-11-15T13:59:00-05:00 | Day | #52 | `7 3 3 4` / `9 1 6 5` / `9 2 7 6` | 2026-11-14T23:00:00-05:00 | `1 8 6 6` (Night) |
| Pick 5 | 2026-11-15T13:59:00-05:00 | Day | #53 | `6 6 4 1 9` / `2 4 3 6 6` / `1 9 8 1 7` | 2026-11-14T23:00:00-05:00 | `6 7 5 0 1` (Night) |
| Cash 5 | 2026-11-15T23:00:00-05:00 | Main | #54 | `7 8 15 23 37` / `4 11 19 30 31` / `5 9 22 25 28` | 2026-11-14T23:00:00-05:00 | `2 11 31 40 44` (Main) |
| Powerball | 2026-11-16T22:59:00-05:00 | Main | #55 | `10 19 21 32 57 + 18` / `6 10 25 37 42 + 4` / `4 37 54 60 61 + 20` | 2026-11-14T22:59:00-05:00 | `9 44 49 51 68 + 4` (Main) |
| Mega Millions | 2026-11-17T23:00:00-05:00 | Main | #42 | `13 28 42 50 60 + 15` / `13 31 37 43 68 + 19` / `10 26 27 64 70 + 16` | 2026-11-13T23:00:00-05:00 | `10 22 33 49 57 + 18` (Main) |
| Millionaire for Life | 2026-11-15T23:15:00-05:00 | Main | #56 | `10 34 40 41 43 + 1` / `5 17 18 27 41 + 5` / `9 14 18 21 56 + 2` | 2026-11-14T23:15:00-05:00 | `2 10 24 29 54 + 1` (Main) |
| Bank a Million | 2026-11-18T23:00:00-05:00 | Main | #57 | `7 15 28 31 34 38` / `16 17 20 22 27 34` / `2 19 26 29 31 34` | 2026-11-14T23:00:00-05:00 | `1 7 9 10 26 38` (Main) |
| Cash Pop | 2026-11-15T12:00:00-05:00 | Lunch Break | #59 | `4` / `9` / `3` | 2026-11-15T09:00:00-05:00 | `11` (Coffee Break) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 7 | 21 | 0 | 21 | 0 |
| Pick 4 | 7 | 21 | 0 | 21 | 0 |
| Pick 5 | 7 | 21 | 0 | 21 | 0 |
| Cash 5 | 4 | 12 | 0 | 12 | 0 |
| Powerball | 2 | 6 | 0 | 6 | 0 |
| Mega Millions | 2 | 6 | 0 | 6 | 0 |
| Millionaire for Life | 4 | 12 | 0 | 12 | 0 |
| Bank a Million | 2 | 6 | 0 | 6 | 0 |
| Cash Pop | 15 | 45 | 4 | 45 | 3 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 0 / 300 | 0.6174 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9760 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.6573 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4206 |
| Powerball | 0 / 300 | 0 / 300 | 0.7053 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3267 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7642 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3886 |
| Cash Pop | 20 / 300 | 16 / 300 | 0.6304 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

All nine automatic history updates and analyses completed.
