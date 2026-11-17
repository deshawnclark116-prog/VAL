# VAL Keno: ONE five-number prediction per official drawing

Same frozen official archive and exact RNG/model state as prior 3-ticket replay.
Each single prediction is the FIRST of the original three tickets.
No looking at the result to select the best ticket; no live wagers.

Official drawings tested: **10,165**.
Each method spends one hypothetical dollar per drawing.

| Model | 5/5 | 4/5 | Avg balls matched | Gross per dollar (one) | Net (one) | Gross per dollar (three) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 6 | 135 | 1.2611 | 0.6943 | -3,107 | 0.6294 |
| random | 9 | 120 | 1.2543 | 0.7959 | -2,075 | 0.7380 |
| frequency | 7 | 148 | 1.2620 | 0.7707 | -2,331 | 0.7460 |
| recent | 6 | 135 | 1.2518 | 0.6924 | -3,127 | 0.7589 |
| cold | 4 | 122 | 1.2517 | 0.5905 | -4,163 | 0.6579 |
| ensemble | 7 | 125 | 1.2585 | 0.7284 | -2,761 | 0.7192 |

## Early vs later period — single ticket

| Model | Early return per dollar | Late return per dollar | Early 5/5 | Late 5/5 |
| --- | ---: | ---: | ---: | ---: |
| control | 0.8115 | 0.5772 | 4 | 2 |
| random | 0.8323 | 0.7594 | 5 | 4 |
| frequency | 0.7816 | 0.7598 | 4 | 3 |
| recent | 0.8383 | 0.5465 | 5 | 1 |
| cold | 0.6065 | 0.5745 | 2 | 2 |
| ensemble | 0.6828 | 0.7740 | 3 | 4 |

## Statistical interpretation

The fair average is 1.25 of five numbers matched per play; an
ordinary five-spot ticket has a chance of about 1 in 1,550 of 5/5.
Random expectation for these drawings: 6.56 perfect tickets per method.
The official Keno Director's Order 134 (2026), Section H, page 8,
specifies main-game prizes on a 1-dollar 5-spot ticket:
0–2 matches pay nothing, 3 matches pay 2 dollars,
4 pay 20 dollars, 5 pay 450 dollars.
Fair expected gross return per dollar: 0.6999 (i.e., negative expected return).

The original three-ticket report's entire outcome distribution,
cost, gross winnings and 5/5 counts are reproduced exactly.
Historical testing across several methods remains exploratory:
the highest observed method is not an independently proven edge.
No real bets, no live code changes.

Details and individual 5/5 tickets in
[research_keno_one_ticket.json](research_keno_one_ticket.json).

