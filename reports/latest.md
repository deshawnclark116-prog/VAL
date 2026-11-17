# VAL next-draw report

Updated: 2026-11-16T21:28:52.389243-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. New batches label Primary, Alt 1, and Alt 2 using experimental model sampling weights, not calibrated winning chances. Previously saved batches remain unranked and unchanged. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-16T23:00:00-05:00 | Night | #71 | **Primary:** `4 6 7` / **Alt 1:** `0 7 5` / **Alt 2:** `7 3 6` | 2026-11-16T13:59:00-05:00 | `0 6 9` (Day) |
| Pick 4 | 2026-11-16T23:00:00-05:00 | Night | #72 | **Primary:** `4 5 8 1` / **Alt 1:** `5 5 5 5` / **Alt 2:** `3 4 7 6` | 2026-11-16T13:59:00-05:00 | `9 1 4 3` (Day) |
| Pick 5 | 2026-11-16T23:00:00-05:00 | Night | #73 | **Primary:** `8 9 5 3 1` / **Alt 1:** `4 8 9 4 9` / **Alt 2:** `6 0 0 2 1` | 2026-11-16T13:59:00-05:00 | `5 3 0 9 5` (Day) |
| Cash 5 | 2026-11-16T23:00:00-05:00 | Main | #68 | **Primary:** `20 26 35 36 39` / **Alt 1:** `6 8 14 22 24` / **Alt 2:** `13 16 18 19 33` | 2026-11-15T23:00:00-05:00 | `2 8 9 14 42` (Main) |
| Powerball | 2026-11-16T22:59:00-05:00 | Main | #55 | `10 19 21 32 57 + 18` / `6 10 25 37 42 + 4` / `4 37 54 60 61 + 20` (legacy: unranked) | 2026-11-14T22:59:00-05:00 | `9 44 49 51 68 + 4` (Main) |
| Mega Millions | 2026-11-17T23:00:00-05:00 | Main | #42 | `13 28 42 50 60 + 15` / `13 31 37 43 68 + 19` / `10 26 27 64 70 + 16` (legacy: unranked) | 2026-11-13T23:00:00-05:00 | `10 22 33 49 57 + 18` (Main) |
| Millionaire for Life | 2026-11-16T23:15:00-05:00 | Main | #69 | **Primary:** `23 34 35 41 48 + 3` / **Alt 1:** `3 12 13 21 24 + 3` / **Alt 2:** `10 25 45 48 49 + 4` | 2026-11-15T23:15:00-05:00 | `5 7 11 20 52 + 3` (Main) |
| Bank a Million | 2026-11-18T23:00:00-05:00 | Main | #57 | `7 15 28 31 34 38` / `16 17 20 22 27 34` / `2 19 26 29 31 34` (legacy: unranked) | 2026-11-14T23:00:00-05:00 | `1 7 9 10 26 38` (Main) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 10 | 30 | 0 | 30 | 0 |
| Pick 4 | 10 | 30 | 0 | 30 | 0 |
| Pick 5 | 10 | 30 | 0 | 30 | 0 |
| Cash 5 | 5 | 15 | 0 | 15 | 0 |
| Powerball | 2 | 6 | 0 | 6 | 0 |
| Mega Millions | 2 | 6 | 0 | 6 | 0 |
| Millionaire for Life | 5 | 15 | 0 | 15 | 0 |
| Bank a Million | 2 | 6 | 0 | 6 | 0 |
| Cash Pop | 18 | 54 | 4 | 54 | 4 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 0 / 300 | 0.4855 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9950 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.7872 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4446 |
| Powerball | 0 / 300 | 0 / 300 | 0.7053 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3267 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7692 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3886 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

### Update / analysis failures

- Cash Pop: Waiting for latest completed Prime Time result (2026-11-16T21:00:00-05:00); new picks withheld
