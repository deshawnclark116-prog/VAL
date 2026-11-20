# VAL pooled-digit full Any Order accuracy: actual historical drawings

**This is real lottery history, NOT a simulated drawing machine.**
The 2025/2026 periods have already been inspected in other VAL
research, so this is a retrospective, exploratory test, NOT fresh
independent proof of an edge. Every candidate is based on earlier
official outcomes. No hidden future results or training leakage.

The metric is the probability of **at least one complete Box hit**
from three tickets. Three ticket rotations of the same multiset
count as ONE opportunity. Random controls use three distinct
all-distinct digit sets. All tickets are paper-only.

| Game | Period | Real targets | Corrected v2 Box | Old rotations v1 Box | Fair random Box | v2 fair expected | random fair expected | v2 minus random | Paired 95% CI on hit difference |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| pick3 | 2025 | 730 | 13 | 5 | 16 | 13.14 | 13.14 | -3 | [-13, 6] |
| pick3 | 2026 | 646 | 9 | 4 | 13 | 11.63 | 11.63 | -4 | [-14, 5] |
| pick3 | combined | 1376 | 22 | 9 | 29 | 24.77 | 24.77 | -7 | [-20, 7] |
| pick4 | 2025 | 730 | 4 | 4 | 4 | 5.26 | 5.26 | +0 | [-6, 6] |
| pick4 | 2026 | 646 | 5 | 0 | 3 | 4.65 | 4.65 | +2 | [-3, 7] |
| pick4 | combined | 1376 | 9 | 4 | 7 | 9.91 | 9.91 | +2 | [-5, 10] |
| pick5 | 2025 | 730 | 4 | 0 | 2 | 2.63 | 2.63 | +2 | [-2, 7] |
| pick5 | 2026 | 646 | 2 | 0 | 4 | 2.33 | 2.33 | -2 | [-7, 3] |
| pick5 | combined | 1376 | 6 | 0 | 6 | 4.95 | 4.95 | +0 | [-7, 7] |

## Interpretation and promotion rule

The original v1 pool rotated the same top-3 digits. In Pick 3
that buys one Box set three times; the corrected v2 portfolio
uses three distinct Box sets. This improves fair any-order
coverage per *three distinct predictions*, but does NOT show
that the digit probabilities contain information about the next
random drawing. Expected paper payout and chance of at least one
hit are different objectives; no profitability is inferred.

A formula predictive edge would need repeated excess complete
Box winners above equally priced maximum-coverage fair controls,
with uncertainty under the iid-fair hypothesis and strictly
future, frozen predictions whose outcomes were never used to
choose the formula. Historical comparative wins do not establish
that standard.

[Target-by-target full Box results](research_pooled_box_v2_real.json).

