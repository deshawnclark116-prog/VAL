# VAL next-draw report

Updated: 2026-11-12T17:52:10.707709-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

Three unique combinations per target, with three saved random controls. If the latest completed result is missing, the game waits rather than generating from outdated input.

| Game | Target draw (ET) | Session | Batch | Combinations | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-12T23:00:00-05:00 | Night | #17 | `7 6 2` / `3 0 6` / `7 6 1` | 2026-11-12T13:59:00-05:00 | `6 0 0` (Day) |
| Pick 4 | 2026-11-12T23:00:00-05:00 | Night | #18 | `8 2 3 0` / `9 4 6 9` / `7 9 7 1` | 2026-11-12T13:59:00-05:00 | `1 5 8 9` (Day) |
| Pick 5 | 2026-11-12T23:00:00-05:00 | Night | #19 | `4 9 4 6 9` / `2 1 0 1 6` / `5 4 2 9 5` | 2026-11-12T13:59:00-05:00 | `2 8 9 3 0` (Day) |
| Cash 5 | 2026-11-12T23:00:00-05:00 | Main | #20 | `14 15 22 23 42` / `3 26 35 36 43` / `6 15 31 34 40` | 2026-11-11T23:00:00-05:00 | `11 15 19 32 39` (Main) |
| Powerball | 2026-11-14T22:59:00-05:00 | Main | #21 | `5 11 43 60 66 + 11` / `2 30 39 40 66 + 20` / `17 34 37 55 57 + 22` | 2026-11-11T22:59:00-05:00 | `8 42 45 51 57 + 17` (Main) |
| Mega Millions | 2026-11-13T23:00:00-05:00 | Main | #22 | `13 33 34 45 46 + 12` / `1 3 13 27 30 + 17` / `6 26 28 49 66 + 16` | 2026-11-10T23:00:00-05:00 | `2 18 25 30 65 + 22` (Main) |
| Millionaire for Life | 2026-11-12T23:15:00-05:00 | Main | #23 | `4 13 16 17 48 + 4` / `6 14 45 47 50 + 4` / `2 17 36 48 57 + 2` | 2026-11-11T23:15:00-05:00 | `6 17 28 41 47 + 1` (Main) |
| Bank a Million | 2026-11-14T23:00:00-05:00 | Main | #24 | `2 19 22 24 27 36` / `3 9 22 26 36 39` / `8 15 22 24 27 30` | 2026-11-11T23:00:00-05:00 | `5 6 15 24 25 28` (Main) |
| Cash Pop | 2026-11-12T21:00:00-05:00 | Prime Time | #25 | `13` / `7` / `15` | 2026-11-12T17:00:00-05:00 | `13` (Rush Hour) |

## Prospective results

Every saved batch is retained in [ledger.json](ledger.json), including losses. New batches settle only against their explicit target date/time/session. Older batches retain their original later-date scoring rule and are not retargeted or replaced. Exact hits require all selected main numbers and the special ball where applicable. Partial matches are not prize wins. Repeated batches on one drawing are correlated.

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

Pending batches: 25. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble exact hits / tickets | Random exact hits / tickets | Frequency-check p-value |
| --- | --- | --- | --- |
| Pick 3 | 0 / 300 | 0 / 300 | 0.3926 |
| Pick 4 | 0 / 300 | 0 / 300 | 0.9510 |
| Pick 5 | 0 / 300 | 0 / 300 | 0.8212 |
| Cash 5 | 0 / 300 | 0 / 300 | 0.4555 |
| Powerball | 0 / 300 | 0 / 300 | 0.7163 |
| Mega Millions | 0 / 300 | 0 / 300 | 0.3816 |
| Millionaire for Life | 0 / 300 | 0 / 300 | 0.7502 |
| Bank a Million | 0 / 300 | 0 / 300 | 0.3816 |
| Cash Pop | 19 / 300 | 20 / 300 | 0.5734 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Each game shows only its next upcoming session; completed sessions are used as input. Keno needs a CSV import in the local dashboard and is not automatically picked here. Seasonal raffle ticket numbers are assigned. FIREBALL, EZ Match, multipliers, payouts, and ROI are not modeled.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

All nine automatic history updates and analyses completed.
