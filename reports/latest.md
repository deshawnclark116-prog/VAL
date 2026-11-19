# VAL next-draw report

Updated: 2026-11-19T15:39:57.054642-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. **Pick 3/4/5 now use the v2 conditional formula**: five digit-probability experts influence a pick only after passing prior-draw validation. Otherwise picks are fair-uniform paper candidates labeled Paper 1/2/3, not purported top predictions. Other games continue using experimental ensemble rankings. No method has validated winning probabilities. Old saved batches remain unchanged. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-19T23:00:00-05:00 | Night | #102 | **Paper 1:** `0 7 8` / **Paper 2:** `7 3 9` / **Paper 3:** `7 6 1` | 2026-11-19T13:59:00-05:00 | `2 5 2` (Day) |
| Pick 4 | 2026-11-19T23:00:00-05:00 | Night | #103 | **Paper 1:** `2 5 9 3` / **Paper 2:** `4 5 9 8` / **Paper 3:** `9 1 3 9` | 2026-11-19T13:59:00-05:00 | `7 6 4 1` (Day) |
| Pick 5 | 2026-11-19T23:00:00-05:00 | Night | #104 | **Paper 1:** `0 4 1 6 3` / **Paper 2:** `0 7 9 5 9` / **Paper 3:** `1 1 1 3 3` | 2026-11-19T13:59:00-05:00 | `2 5 3 5 7` (Day) |
| Cash 5 | 2026-11-19T23:00:00-05:00 | Main | #98 | **Primary:** `2 6 33 34 44` / **Alt 1:** `5 26 29 35 44` / **Alt 2:** `7 18 20 26 27` | 2026-11-18T23:00:00-05:00 | `6 20 23 37 40` (Main) |
| Powerball | 2026-11-21T22:59:00-05:00 | Main | #99 | **Primary:** `15 33 55 58 69 + 3` / **Alt 1:** `20 27 50 64 65 + 6` / **Alt 2:** `3 7 60 61 62 + 18` | 2026-11-18T22:59:00-05:00 | `18 31 43 51 62 + 12` (Main) |
| Mega Millions | 2026-11-20T23:00:00-05:00 | Main | #87 | **Primary:** `5 30 31 59 70 + 20` / **Alt 1:** `21 22 26 41 70 + 3` / **Alt 2:** `16 18 24 26 29 + 20` | 2026-11-17T23:00:00-05:00 | `3 10 19 28 33 + 21` (Main) |
| Millionaire for Life | 2026-11-19T23:15:00-05:00 | Main | #100 | **Primary:** `9 19 33 36 57 + 1` / **Alt 1:** `6 21 26 29 37 + 1` / **Alt 2:** `1 2 41 55 57 + 2` | 2026-11-18T23:15:00-05:00 | `9 18 38 54 57 + 3` (Main) |
| Bank a Million | 2026-11-21T23:00:00-05:00 | Main | #101 | **Primary:** `2 10 21 30 32 36` / **Alt 1:** `8 14 25 26 35 39` / **Alt 2:** `4 6 9 14 29 35` | 2026-11-18T23:00:00-05:00 | `5 6 10 17 29 38` (Main) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | --- | --- | --- | --- | --- |
| Pick 3 | 17 | 51 | 0 | 51 | 0 |
| Pick 4 | 17 | 51 | 0 | 51 | 0 |
| Pick 5 | 17 | 51 | 0 | 51 | 0 |
| Cash 5 | 8 | 24 | 0 | 24 | 0 |
| Powerball | 4 | 12 | 0 | 12 | 0 |
| Mega Millions | 3 | 9 | 0 | 9 | 0 |
| Millionaire for Life | 8 | 24 | 0 | 24 | 0 |
| Bank a Million | 3 | 9 | 0 | 9 | 0 |
| Cash Pop | 18 | 54 | 4 | 54 | 4 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 3 / 300 | 0.3666 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9920 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.8242 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4825 |
| Powerball | 0 / 300 | 0 / 300 | 0.6943 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3287 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.6643 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3167 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

### Update / analysis failures

- Cash Pop: Waiting for latest completed Lunch Break result (2026-11-19T12:00:00-05:00); new picks withheld
