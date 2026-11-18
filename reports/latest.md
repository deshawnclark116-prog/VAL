# VAL next-draw report

Updated: 2026-11-17T21:55:02.823022-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. New batches label Primary, Alt 1, and Alt 2 using experimental model sampling weights, not calibrated winning chances. Previously saved batches remain unranked and unchanged. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-17T23:00:00-05:00 | Night | #80 | **Primary:** `7 0 7` / **Alt 1:** `5 6 7` / **Alt 2:** `3 2 6` | 2026-11-17T13:59:00-05:00 | `1 2 1` (Day) |
| Pick 4 | 2026-11-17T23:00:00-05:00 | Night | #81 | **Primary:** `6 3 6 3` / **Alt 1:** `3 6 4 5` / **Alt 2:** `8 7 8 2` | 2026-11-17T13:59:00-05:00 | `5 5 4 9` (Day) |
| Pick 5 | 2026-11-17T23:00:00-05:00 | Night | #82 | **Primary:** `5 4 0 1 2` / **Alt 1:** `7 8 2 3 0` / **Alt 2:** `7 0 2 2 6` | 2026-11-17T13:59:00-05:00 | `7 4 9 4 5` (Day) |
| Cash 5 | 2026-11-17T23:00:00-05:00 | Main | #77 | **Primary:** `23 24 28 37 45` / **Alt 1:** `3 7 14 39 41` / **Alt 2:** `1 2 13 31 40` | 2026-11-16T23:00:00-05:00 | `7 17 24 35 39` (Main) |
| Powerball | 2026-11-18T22:59:00-05:00 | Main | #78 | **Primary:** `4 13 35 40 45 + 18` / **Alt 1:** `45 47 50 51 52 + 1` / **Alt 2:** `11 12 62 64 66 + 5` | 2026-11-16T22:59:00-05:00 | `17 35 48 60 69 + 17` (Main) |
| Mega Millions | 2026-11-17T23:00:00-05:00 | Main | #42 | `13 28 42 50 60 + 15` / `13 31 37 43 68 + 19` / `10 26 27 64 70 + 16` (legacy: unranked) | 2026-11-13T23:00:00-05:00 | `10 22 33 49 57 + 18` (Main) |
| Millionaire for Life | 2026-11-17T23:15:00-05:00 | Main | #79 | **Primary:** `6 11 38 43 57 + 5` / **Alt 1:** `6 12 13 22 29 + 2` / **Alt 2:** `10 17 26 44 47 + 2` | 2026-11-16T23:15:00-05:00 | `9 17 26 33 35 + 5` (Main) |
| Bank a Million | 2026-11-18T23:00:00-05:00 | Main | #57 | `7 15 28 31 34 38` / `16 17 20 22 27 34` / `2 19 26 29 31 34` (legacy: unranked) | 2026-11-14T23:00:00-05:00 | `1 7 9 10 26 38` (Main) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 12 | 36 | 0 | 36 | 0 |
| Pick 4 | 12 | 36 | 0 | 36 | 0 |
| Pick 5 | 12 | 36 | 0 | 36 | 0 |
| Cash 5 | 6 | 18 | 0 | 18 | 0 |
| Powerball | 3 | 9 | 0 | 9 | 0 |
| Mega Millions | 2 | 6 | 0 | 6 | 0 |
| Millionaire for Life | 6 | 18 | 0 | 18 | 0 |
| Bank a Million | 2 | 6 | 0 | 6 | 0 |
| Cash Pop | 18 | 54 | 4 | 54 | 4 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 0 / 300 | 0.4995 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9940 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.7532 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4605 |
| Powerball | 0 / 300 | 0 / 300 | 0.7063 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3267 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7113 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3886 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

### Update / analysis failures

- Cash Pop: Waiting for latest completed Prime Time result (2026-11-17T21:00:00-05:00); new picks withheld
