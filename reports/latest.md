# VAL next-draw report

Updated: 2026-11-20T06:44:35.505472-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. **Pick 3/4/5 now use the v2 conditional formula**: five digit-probability experts influence a pick only after passing prior-draw validation. Otherwise picks are fair-uniform paper candidates labeled Paper 1/2/3, not purported top predictions. Other games continue using experimental ensemble rankings. No method has validated winning probabilities. Old saved batches remain unchanged. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-20T13:59:00-05:00 | Day | #105 | **Paper 1:** `2 3 7` / **Paper 2:** `2 5 5` / **Paper 3:** `6 3 5` | 2026-11-19T23:00:00-05:00 | `7 6 6` (Night) |
| Pick 4 | 2026-11-20T13:59:00-05:00 | Day | #106 | **Paper 1:** `2 3 0 2` / **Paper 2:** `7 2 1 6` / **Paper 3:** `9 3 2 4` | 2026-11-19T23:00:00-05:00 | `4 4 9 8` (Night) |
| Pick 5 | 2026-11-20T13:59:00-05:00 | Day | #107 | **Paper 1:** `1 2 7 8 7` / **Paper 2:** `3 3 9 6 9` / **Paper 3:** `4 9 0 1 3` | 2026-11-19T23:00:00-05:00 | `3 0 0 7 2` (Night) |
| Cash 5 | 2026-11-20T23:00:00-05:00 | Main | #108 | **Primary:** `1 6 12 30 33` / **Alt 1:** `4 5 6 23 24` / **Alt 2:** `1 4 5 31 37` | 2026-11-19T23:00:00-05:00 | `3 14 19 30 43` (Main) |
| Powerball | 2026-11-21T22:59:00-05:00 | Main | #99 | **Primary:** `15 33 55 58 69 + 3` / **Alt 1:** `20 27 50 64 65 + 6` / **Alt 2:** `3 7 60 61 62 + 18` | 2026-11-18T22:59:00-05:00 | `18 31 43 51 62 + 12` (Main) |
| Mega Millions | 2026-11-20T23:00:00-05:00 | Main | #87 | **Primary:** `5 30 31 59 70 + 20` / **Alt 1:** `21 22 26 41 70 + 3` / **Alt 2:** `16 18 24 26 29 + 20` | 2026-11-17T23:00:00-05:00 | `3 10 19 28 33 + 21` (Main) |
| Millionaire for Life | 2026-11-20T23:15:00-05:00 | Main | #109 | **Primary:** `2 28 31 37 39 + 3` / **Alt 1:** `19 40 41 48 49 + 5` / **Alt 2:** `18 19 28 30 54 + 5` | 2026-11-19T23:15:00-05:00 | `1 15 27 28 41 + 5` (Main) |
| Bank a Million | 2026-11-21T23:00:00-05:00 | Main | #101 | **Primary:** `2 10 21 30 32 36` / **Alt 1:** `8 14 25 26 35 39` / **Alt 2:** `4 6 9 14 29 35` | 2026-11-18T23:00:00-05:00 | `5 6 10 17 29 38` (Main) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 18 | 54 | 0 | 54 | 0 |
| Pick 4 | 18 | 54 | 0 | 54 | 0 |
| Pick 5 | 18 | 54 | 0 | 54 | 0 |
| Cash 5 | 9 | 27 | 0 | 27 | 0 |
| Powerball | 4 | 12 | 0 | 12 | 0 |
| Mega Millions | 3 | 9 | 0 | 9 | 0 |
| Millionaire for Life | 9 | 27 | 0 | 27 | 0 |
| Bank a Million | 3 | 9 | 0 | 9 | 0 |
| Cash Pop | 18 | 54 | 4 | 54 | 4 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 3 / 300 | 1 / 300 | 0.3536 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9850 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.7722 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.5285 |
| Powerball | 0 / 300 | 0 / 300 | 0.6943 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3287 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.6553 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3167 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

### Update / analysis failures

- Cash Pop: Waiting for latest completed After Hours result (2026-11-19T23:59:00-05:00); new picks withheld
