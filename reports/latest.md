# VAL next-draw report

Updated: 2026-11-21T09:51:22.064329-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

**Exactly one prediction and one independent random control per upcoming game draw.** Pick 3/4/5 target complete Any Order (Box) digit sets, not partial-position matches. Box v4 evaluates cumulative and recent evidence; without a proven signal it returns one clearly labeled random paper Box selection, not an asserted edge. All tickets are hypothetical; none are purchased. Older multi-ticket batches are preserved unchanged in the ledger, but only each original first ticket is shown and counted in the one-pick comparison. Missing latest results withhold new picks.

| Game | Target draw (ET) | Session | Batch | One prediction | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-21T13:59:00-05:00 | Day | #116 | **Paper:** `1 2 8` | 2026-11-20T23:00:00-05:00 | `5 6 8` (Night) |
| Pick 4 | 2026-11-21T13:59:00-05:00 | Day | #117 | **Paper:** `0 1 4 8` | 2026-11-20T23:00:00-05:00 | `8 6 0 1` (Night) |
| Pick 5 | 2026-11-21T13:59:00-05:00 | Day | #118 | **Paper:** `0 3 4 7 8` | 2026-11-20T23:00:00-05:00 | `2 0 7 2 5` (Night) |
| Cash 5 | 2026-11-21T23:00:00-05:00 | Main | #119 | **Primary:** `2 7 26 30 41` | 2026-11-20T23:00:00-05:00 | `17 18 33 34 38` (Main) |
| Powerball | 2026-11-21T22:59:00-05:00 | Main | #99 | **Primary:** `15 33 55 58 69 + 3` | 2026-11-18T22:59:00-05:00 | `18 31 43 51 62 + 12` (Main) |
| Mega Millions | 2026-11-24T23:00:00-05:00 | Main | #120 | **Primary:** `5 25 28 34 38 + 14` | 2026-11-20T23:00:00-05:00 | `32 35 48 58 61 + 21` (Main) |
| Millionaire for Life | 2026-11-21T23:15:00-05:00 | Main | #121 | **Primary:** `13 18 29 38 57 + 3` | 2026-11-20T23:15:00-05:00 | `2 6 19 20 30 + 4` (Main) |
| Bank a Million | 2026-11-21T23:00:00-05:00 | Main | #101 | **Primary:** `2 10 21 30 32 36` | 2026-11-18T23:00:00-05:00 | `5 6 10 17 29 38` (Main) |

## Complete Any Order (Box) results — PRIMARY METRIC

A Box match requires ALL selected digits, including repeated digits, regardless of their order. A one-way all-identical pattern is Straight-only. Every settled batch is rescored using only its FIRST originally saved ticket and the FIRST original random control. Old three-ticket ledgers stay immutable, but their alternatives do not count toward this one-pick score. Historical picks were not necessarily purchased as Box tickets.

Payout and net are **hypothetical** $1 Any Order paper-wagers using published no-FIREBALL prize tables, one ticket per side per settled batch. No tickets were bought. Historical first-choice tickets may have different digit multiplicities.

| Digit game | Settled batches | Model Box wins | Control Box wins | Model Straight | Control Straight | Model paper net | Control paper net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pick 3 | 21 | 0 | 0 | 0 | 0 | $-21 | $-21 |
| Pick 4 | 21 | 1 | 0 | 0 | 0 | $179 | $-21 |
| Pick 5 | 21 | 0 | 0 | 0 | 0 | $-21 | $-21 |

## Other game results

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cash 5 | 10 | 10 | 0 | 10 | 0 |
| Powerball | 4 | 4 | 0 | 4 | 0 |
| Mega Millions | 4 | 4 | 0 | 4 | 0 |
| Millionaire for Life | 10 | 10 | 0 | 10 | 0 |
| Bank a Million | 3 | 3 | 0 | 3 | 0 |
| Cash Pop | 18 | 18 | 3 | 18 | 3 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble full Box wins | Random full Box wins | Ensemble exact wins | Random exact wins | Frequency p-value |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pick 3 | 0 | 0 | 0 | 0 | 0.4136 |
| Pick 4 | 0 | 0 | 0 | 0 | 0.9860 |
| Pick 5 | 0 | 0 | 0 | 0 | 0.7602 |
| Cash 5 | — | — | 0 | 0 | 0.4705 |
| Powerball | — | — | 0 | 0 | 0.6943 |
| Mega Millions | — | — | 0 | 0 | 0.3367 |
| Millionaire for Life | — | — | 0 | 0 | 0.5514 |
| Bank a Million | — | — | 0 | 0 | 0.3167 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Box scoring uses published no-FIREBALL $1 Any Order prize tables for paper-only payout and net estimates; no actual wagering occurs. Fireball, 50/50, and Combo are excluded. Other games have no payout/ROI calculation. Keno needs a CSV import, and seasonal raffle ticket numbers are assigned.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

### Update / analysis failures

- Cash Pop: Waiting for latest completed Coffee Break result (2026-11-21T09:00:00-05:00); new picks withheld
