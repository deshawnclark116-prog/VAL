# VAL next-draw report

Updated: 2026-11-24T23:17:21.801780-05:00 · Eastern time

Paper picks for research. These weights are not proven winning probabilities.

## Picks

Only the next scheduled drawing for each game is shown, as of the update time above. The Target column is the drawing these picks are for. After that time, the row is expired until this report refreshes.

Picks use previous completed results from ALL sessions of the same game: today's Day result is included when preparing Night picks. No future draw or other game's results are used. Batches stay fixed for their target; refreshes do not replace losing picks.

**Exactly one prediction and one independent random control per upcoming game draw.** Pick 3/4/5 target complete Any Order (Box) digit sets, not partial-position matches. Box v4 evaluates cumulative and recent evidence; without a proven signal it returns one clearly labeled random paper Box selection, not an asserted edge. All tickets are hypothetical; none are purchased. Older multi-ticket batches are preserved unchanged in the ledger, but only each original first ticket is shown and counted in the one-pick comparison. Missing latest results withhold new picks.

| Game | Target draw (ET) | Session | Batch | One prediction | Latest result used (ET) | Latest winning numbers used |
| --- | --- | --- | --- | --- | --- | --- |
| Pick 3 | 2026-11-25T13:59:00-05:00 | Day | #152 | **Paper:** `2 5 9` | 2026-11-24T23:00:00-05:00 | `1 2 3` (Night) |
| Pick 4 | 2026-11-25T13:59:00-05:00 | Day | #153 | **Paper:** `2 5 6 9` | 2026-11-24T23:00:00-05:00 | `7 5 9 9` (Night) |
| Pick 5 | 2026-11-25T13:59:00-05:00 | Day | #154 | **Paper:** `0 1 3 7 9` | 2026-11-24T23:00:00-05:00 | `7 4 2 9 9` (Night) |
| Powerball | 2026-11-25T22:59:00-05:00 | Main | #147 | **Primary:** `14 42 57 58 68 + 23` | 2026-11-23T22:59:00-05:00 | `7 9 27 40 58 + 19` (Main) |
| Bank a Million | 2026-11-25T23:00:00-05:00 | Main | #131 | **Primary:** `3 10 17 19 25 27` | 2026-11-21T23:00:00-05:00 | `4 12 14 15 22 33` (Main) |

## Complete Any Order (Box) results — PRIMARY METRIC

A Box match requires ALL selected digits, including repeated digits, regardless of their order. A one-way all-identical pattern is Straight-only. Every settled batch is rescored using only its FIRST originally saved ticket and the FIRST original random control. Old three-ticket ledgers stay immutable, but their alternatives do not count toward this one-pick score. Historical picks were not necessarily purchased as Box tickets.

Payout and net are **hypothetical** $1 Any Order paper-wagers using published no-FIREBALL prize tables, one ticket per side per settled batch. No tickets were bought. Historical first-choice tickets may have different digit multiplicities.

| Digit game | Settled batches | Model Box wins | Control Box wins | Model Straight | Control Straight | Model paper net | Control paper net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pick 3 | 29 | 0 | 0 | 0 | 0 | $-29 | $-29 |
| Pick 4 | 29 | 2 | 0 | 1 | 0 | $371 | $-29 |
| Pick 5 | 29 | 0 | 0 | 0 | 0 | $-29 | $-29 |

## Fallback watch — one original ticket per drawing

Only settled Pick 3/4/5 batches explicitly tagged as a no-signal fallback are included. Each row uses the first saved ticket and its original first random control; alternatives are never counted. Grouping by formula version avoids combining distinct experiments. Fair-expected wins come from the exact digit-multiplicity odds of those tickets, not estimated predictive probabilities. **These results do not demonstrate an edge**, especially when examining a version after its early wins.

| Game | Fallback formula | Settled picks | Box wins | Random-control wins | Fair expected Box wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Pick 3 | `digit_box_v3` | 1 | 0 | 0 | 0.0060 |
| Pick 3 | `digit_box_v4` | 9 | 0 | 0 | 0.0540 |
| Pick 3 | `digit_conditional_v2` | 4 | 0 | 0 | 0.0240 |
| Pick 4 | `digit_box_v3` | 1 | 0 | 0 | 0.0024 |
| Pick 4 | `digit_box_v4` | 9 | 2 | 0 | 0.0216 |
| Pick 4 | `digit_conditional_v2` | 4 | 0 | 0 | 0.0060 |
| Pick 5 | `digit_box_v3` | 1 | 0 | 0 | 0.0012 |
| Pick 5 | `digit_box_v4` | 9 | 0 | 0 | 0.0108 |
| Pick 5 | `digit_conditional_v2` | 4 | 0 | 0 | 0.0042 |

## Other game results

| Game | Settled batches | Model tickets | Model exact hits | Random tickets | Random exact hits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cash 5 | 13 | 13 | 0 | 13 | 0 |
| Powerball | 6 | 6 | 0 | 6 | 0 |
| Mega Millions | 4 | 4 | 0 | 4 | 0 |
| Millionaire for Life | 13 | 13 | 0 | 13 | 0 |
| Bank a Million | 4 | 4 | 0 | 4 | 0 |
| Cash Pop | 18 | 18 | 3 | 18 | 3 |

Pending batches: 9. This report retains the original saved picks and controls; no retrospective replacement.

## Historical checks

100 rolling test draws per game, with only earlier data used for training. These are historical tests, separate from the prospective ledger. Frequency p-values test dispersion only; they are not win probabilities. Multiple comparisons can produce chance findings.

| Game (all sessions) | Ensemble full Box wins | Random full Box wins | Ensemble exact wins | Random exact wins | Frequency p-value |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pick 3 | 1 | 0 | 1 | 0 | 0.3307 |
| Pick 4 | 0 | 0 | 0 | 0 | 0.9640 |
| Pick 5 | 0 | 0 | 0 | 0 | 0.8581 |
| Powerball | — | — | 0 | 0 | 0.7263 |
| Bank a Million | — | — | 0 | 0 | 0.3127 |

Full five-method statistics and simulation details: [analysis.json](analysis.json).

## Coverage and update status

Nine recurring games update from Virginia Lottery official downloads. Same-day Pick 3/4/5 results are supplemented from the official latest-result cards. Box scoring uses published no-FIREBALL $1 Any Order prize tables for paper-only payout and net estimates; no actual wagering occurs. Fireball, 50/50, and Combo are excluded. Other games have no payout/ROI calculation. Keno needs a CSV import, and seasonal raffle ticket numbers are assigned.

[Official Virginia game rules and results](https://www.valottery.com/alldrawgames)

### Update / analysis failures

- Cash 5: Waiting for latest completed Main result (2026-11-24T23:00:00-05:00); new picks withheld
- Mega Millions: Waiting for latest completed Main result (2026-11-24T23:00:00-05:00); new picks withheld
- Millionaire for Life: Waiting for latest completed Main result (2026-11-24T23:15:00-05:00); new picks withheld
- Cash Pop: Waiting for latest completed Prime Time result (2026-11-24T21:00:00-05:00); new picks withheld
