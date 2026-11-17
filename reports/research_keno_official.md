# VAL official Keno expanded historical test

Official Keno drawings downloaded: **10,665**.
Range: 2026-10-17T00:02:00 to 2026-11-16T09:45:30.
Number gaps in official source: 6.

Strictly chronological paper backtest: **10,165** real
drawings, three five-number tickets per method per draw.
First 500 used only for warmup. Independent random control.

Official Director's Order No. 134 (2026), Section H, page 8:
five-spot $1 prizes: 3 hits $2, 4 hits $20, 5 hits $450.
**Zero, one, or two hits pay $0.** The current marketing website
incorrectly lists a zero-match five-spot prize.

| Method | Tickets | 3+ hits | 4+ hits | 5/5 | Avg matches | Return/$1 | Net $ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 30,495 | 2,978 | 401 | 14 | 1.2584 | 0.6294 | -11,301 |
| random | 30,495 | 2,869 | 382 | 23 | 1.2477 | 0.7380 | -7,991 |
| frequency | 30,495 | 3,034 | 425 | 21 | 1.2572 | 0.7460 | -7,747 |
| recent | 30,495 | 2,971 | 430 | 22 | 1.2604 | 0.7589 | -7,353 |
| cold | 30,495 | 2,982 | 401 | 16 | 1.2526 | 0.6579 | -10,433 |
| ensemble | 30,495 | 3,012 | 406 | 20 | 1.2519 | 0.7192 | -8,563 |

## Early vs late historical periods

| Method | Early return per $ | Later return per $ | Early 5/5 | Later 5/5 |
| --- | ---: | ---: | ---: | ---: |
| control | 0.7544 | 0.5044 | 11 | 3 |
| random | 0.8646 | 0.6113 | 16 | 7 |
| frequency | 0.7771 | 0.7148 | 12 | 9 |
| recent | 0.8116 | 0.7061 | 13 | 9 |
| cold | 0.7021 | 0.6137 | 9 | 7 |
| ensemble | 0.6457 | 0.7927 | 8 | 12 |

Fair random expected payout: 0.6999 per $1.
All tickets and prizes are hypothetical. No money wagered.
Multiple-method selection and rare big prizes prevent declaring
a genuine predictive edge on this history alone. No promotion
of any historical winner until a separately frozen future test.

Raw official result sample: [keno_official_history.json.gz](keno_official_history.json.gz).
Detailed audit [research_keno_official.json](research_keno_official.json).

