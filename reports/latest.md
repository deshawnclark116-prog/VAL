# VAL next-draw report

Updated: 2026-11-14T18:56:07.852856-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-14T23:00:00-05:00 | Night | #46 | `3 2 5` / `1 7 7` / `9 7 7` | 2026-11-14T13:59:00-05:00 | `3 8 0` (Day) |
| Pick 4 | 2026-11-14T23:00:00-05:00 | Night | #47 | `4 3 2 1` / `4 2 2 6` / `2 4 8 6` | 2026-11-14T13:59:00-05:00 | `9 9 2 2` (Day) |
| Pick 5 | 2026-11-14T23:00:00-05:00 | Night | #48 | `4 2 4 5 6` / `0 8 8 1 2` / `9 9 6 9 2` | 2026-11-14T13:59:00-05:00 | `2 0 7 2 0` (Day) |
| Cash 5 | 2026-11-14T23:00:00-05:00 | Main | #41 | `7 8 24 30 37` / `1 10 16 33 37` / `7 22 29 38 41` | 2026-11-13T23:00:00-05:00 | `18 22 33 34 45` (Main) |
| Powerball | 2026-11-14T22:59:00-05:00 | Main | #21 | `5 11 43 60 66 + 11` / `2 30 39 40 66 + 20` / `17 34 37 55 57 + 22` | 2026-11-11T22:59:00-05:00 | `8 42 45 51 57 + 17` (Main) |
| Mega Millions | 2026-11-17T23:00:00-05:00 | Main | #42 | `13 28 42 50 60 + 15` / `13 31 37 43 68 + 19` / `10 26 27 64 70 + 16` | 2026-11-13T23:00:00-05:00 | `10 22 33 49 57 + 18` (Main) |
| Millionaire for Life | 2026-11-14T23:15:00-05:00 | Main | #43 | `16 22 30 49 51 + 3` / `11 15 16 48 54 + 5` / `10 13 28 45 53 + 1` | 2026-11-13T23:15:00-05:00 | `34 37 46 50 52 + 4` (Main) |
| Bank a Million | 2026-11-14T23:00:00-05:00 | Main | #24 | `2 19 22 24 27 36` / `3 9 22 26 36 39` / `8 15 22 24 27 30` | 2026-11-11T23:00:00-05:00 | `5 6 15 24 25 28` (Main) |
| Cash Pop | 2026-11-14T21:00:00-05:00 | Prime Time | #50 | `9` / `2` / `5` | 2026-11-14T17:00:00-05:00 | `15` (Rush Hour) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 6 | 18 | 0 | 18 | 0 |
| Pick 4 | 6 | 18 | 0 | 18 | 0 |
| Pick 5 | 6 | 18 | 0 | 18 | 0 |
| Cash 5 | 3 | 9 | 0 | 9 | 0 |
| Powerball | 0 | 0 | 0 | 0 | 0 |
| Mega Millions | 2 | 6 | 0 | 6 | 0 |
| Millionaire for Life | 3 | 9 | 0 | 9 | 0 |
| Bank a Million | 0 | 0 | 0 | 0 | 0 |
| Cash Pop | 13 | 39 | 3 | 39 | 2 |

Pending batches: 11. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 0 / 300 | 0.6184 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9660 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.6364 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.3716 |
| Powerball | 0 / 300 | 0 / 300 | 0.7163 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3267 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7982 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3816 |
| Cash Pop | 23 / 300 | 22 / 300 | 0.6573 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

All nine automatic history updates and analyses completed.
