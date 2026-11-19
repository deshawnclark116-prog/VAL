# VAL: pooled-digit forecast ablation, by Day/Night

The prior accuracy lead was identified after looking at 2026.
**All comparisons here remain retrospective and exploratory.**
Four additional pooled-digit formula architectures are compared
with the original 5,000-draw pooled model.

The reported *top-1* hit rate checks one selected digit at each
position, where 10% is fair expectation. The 30% top-3
benchmark is also shown. Neither is the rate of winning
complete ordered tickets.

| Game | Session/year | Formula | Draws | Top-digit accuracy | Top-3 coverage | Proper log gain |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| pick3 | 2024_Day | global_5000 | 366 | 10.20% | 28.78% | -0.001084 |
| pick3 | 2024_Day | stream_5000 | 366 | 10.75% | 29.87% | +0.000555 |
| pick3 | 2024_Day | recent_500 | 366 | 10.20% | 30.51% | -0.001982 |
| pick3 | 2024_Day | hier_stream | 366 | 10.66% | 29.78% | +0.000449 |
| pick3 | 2024_Day | multiscale | 366 | 10.38% | 30.24% | -0.000507 |
| pick3 | 2024_Night | global_5000 | 366 | 9.29% | 27.05% | -0.002832 |
| pick3 | 2024_Night | stream_5000 | 366 | 11.29% | 28.23% | -0.001447 |
| pick3 | 2024_Night | recent_500 | 366 | 8.65% | 31.51% | +0.000344 |
| pick3 | 2024_Night | hier_stream | 366 | 11.29% | 28.87% | -0.002940 |
| pick3 | 2024_Night | multiscale | 366 | 10.38% | 28.60% | -0.001260 |
| pick3 | 2025_Day | global_5000 | 365 | 10.59% | 30.96% | -0.000027 |
| pick3 | 2025_Day | stream_5000 | 365 | 10.68% | 31.42% | +0.000662 |
| pick3 | 2025_Day | recent_500 | 365 | 7.49% | 28.13% | -0.001190 |
| pick3 | 2025_Day | hier_stream | 365 | 10.50% | 31.32% | +0.000656 |
| pick3 | 2025_Day | multiscale | 365 | 9.22% | 30.14% | +0.000069 |
| pick3 | 2025_Night | global_5000 | 365 | 10.78% | 31.32% | +0.000329 |
| pick3 | 2025_Night | stream_5000 | 365 | 9.95% | 30.68% | +0.000763 |
| pick3 | 2025_Night | recent_500 | 365 | 8.58% | 28.49% | -0.000222 |
| pick3 | 2025_Night | hier_stream | 365 | 9.86% | 30.14% | +0.001109 |
| pick3 | 2025_Night | multiscale | 365 | 9.77% | 31.32% | +0.000465 |
| pick3 | 2026_Day | global_5000 | 321 | 10.90% | 30.63% | +0.000922 |
| pick3 | 2026_Day | stream_5000 | 321 | 9.45% | 31.15% | -0.000428 |
| pick3 | 2026_Day | recent_500 | 321 | 8.72% | 30.94% | +0.001229 |
| pick3 | 2026_Day | hier_stream | 321 | 9.45% | 31.15% | -0.001063 |
| pick3 | 2026_Day | multiscale | 321 | 10.49% | 30.32% | +0.000552 |
| pick3 | 2026_Night | global_5000 | 321 | 11.73% | 32.61% | +0.001357 |
| pick3 | 2026_Night | stream_5000 | 321 | 9.03% | 28.66% | -0.000644 |
| pick3 | 2026_Night | recent_500 | 321 | 8.83% | 30.84% | +0.001704 |
| pick3 | 2026_Night | hier_stream | 321 | 9.24% | 28.56% | -0.001006 |
| pick3 | 2026_Night | multiscale | 321 | 11.42% | 30.32% | +0.000780 |
| pick4 | 2024_Day | global_5000 | 366 | 10.45% | 30.05% | -0.000987 |
| pick4 | 2024_Day | stream_5000 | 366 | 11.13% | 30.60% | -0.000307 |
| pick4 | 2024_Day | recent_500 | 366 | 10.45% | 30.05% | -0.001367 |
| pick4 | 2024_Day | hier_stream | 366 | 11.13% | 30.74% | -0.001663 |
| pick4 | 2024_Day | multiscale | 366 | 11.13% | 31.56% | -0.000675 |
| pick4 | 2024_Night | global_5000 | 366 | 10.31% | 30.40% | +0.000527 |
| pick4 | 2024_Night | stream_5000 | 366 | 10.18% | 29.92% | -0.001190 |
| pick4 | 2024_Night | recent_500 | 366 | 9.36% | 28.96% | +0.000477 |
| pick4 | 2024_Night | hier_stream | 366 | 10.18% | 30.60% | -0.002309 |
| pick4 | 2024_Night | multiscale | 366 | 10.52% | 29.92% | -0.000062 |
| pick4 | 2025_Day | global_5000 | 365 | 11.23% | 30.14% | -0.000159 |
| pick4 | 2025_Day | stream_5000 | 365 | 11.23% | 31.64% | +0.002595 |
| pick4 | 2025_Day | recent_500 | 365 | 10.41% | 29.11% | -0.000633 |
| pick4 | 2025_Day | hier_stream | 365 | 11.23% | 31.71% | +0.003169 |
| pick4 | 2025_Day | multiscale | 365 | 11.23% | 31.51% | +0.000895 |
| pick4 | 2025_Night | global_5000 | 365 | 9.25% | 27.53% | -0.002428 |
| pick4 | 2025_Night | stream_5000 | 365 | 9.66% | 31.03% | -0.001148 |
| pick4 | 2025_Night | recent_500 | 365 | 10.48% | 31.37% | +0.000061 |
| pick4 | 2025_Night | hier_stream | 365 | 9.93% | 30.82% | -0.002475 |
| pick4 | 2025_Night | multiscale | 365 | 10.21% | 29.59% | -0.000962 |
| pick4 | 2026_Day | global_5000 | 321 | 10.90% | 31.54% | +0.001153 |
| pick4 | 2026_Day | stream_5000 | 321 | 10.98% | 31.70% | +0.003497 |
| pick4 | 2026_Day | recent_500 | 321 | 9.89% | 28.74% | -0.000304 |
| pick4 | 2026_Day | hier_stream | 321 | 10.90% | 31.39% | +0.004731 |
| pick4 | 2026_Day | multiscale | 321 | 11.29% | 31.70% | +0.001764 |
| pick4 | 2026_Night | global_5000 | 321 | 8.49% | 29.44% | -0.001951 |
| pick4 | 2026_Night | stream_5000 | 321 | 8.49% | 28.58% | -0.003760 |
| pick4 | 2026_Night | recent_500 | 321 | 8.33% | 29.05% | -0.000324 |
| pick4 | 2026_Night | hier_stream | 321 | 8.49% | 27.96% | -0.006631 |
| pick4 | 2026_Night | multiscale | 321 | 8.57% | 26.32% | -0.001966 |
| pick5 | 2024_Day | global_5000 | 326 | 8.47% | 29.39% | -0.000899 |
| pick5 | 2024_Day | stream_5000 | 326 | 7.79% | 27.24% | -0.001776 |
| pick5 | 2024_Day | recent_500 | 326 | 8.65% | 29.14% | -0.001087 |
| pick5 | 2024_Day | hier_stream | 326 | 8.53% | 27.55% | -0.009003 |
| pick5 | 2024_Day | multiscale | 326 | 9.14% | 29.39% | -0.001241 |
| pick5 | 2024_Night | global_5000 | 326 | 9.69% | 31.29% | +0.000354 |
| pick5 | 2024_Night | stream_5000 | 326 | 9.51% | 29.57% | -0.000382 |
| pick5 | 2024_Night | recent_500 | 326 | 10.37% | 30.86% | +0.001391 |
| pick5 | 2024_Night | hier_stream | 326 | 9.33% | 29.51% | -0.003867 |
| pick5 | 2024_Night | multiscale | 326 | 8.90% | 30.49% | +0.000314 |
| pick5 | 2025_Day | global_5000 | 365 | 10.47% | 29.04% | -0.002454 |
| pick5 | 2025_Day | stream_5000 | 365 | 9.26% | 28.77% | -0.001726 |
| pick5 | 2025_Day | recent_500 | 365 | 9.53% | 29.53% | -0.001637 |
| pick5 | 2025_Day | hier_stream | 365 | 8.88% | 28.55% | -0.006257 |
| pick5 | 2025_Day | multiscale | 365 | 10.19% | 29.21% | -0.001890 |
| pick5 | 2025_Night | global_5000 | 365 | 10.08% | 29.37% | -0.000673 |
| pick5 | 2025_Night | stream_5000 | 365 | 11.12% | 29.70% | -0.000312 |
| pick5 | 2025_Night | recent_500 | 365 | 9.92% | 29.92% | -0.001169 |
| pick5 | 2025_Night | hier_stream | 365 | 11.12% | 29.10% | -0.003232 |
| pick5 | 2025_Night | multiscale | 365 | 11.12% | 29.59% | -0.000571 |
| pick5 | 2026_Day | global_5000 | 321 | 12.52% | 31.09% | +0.003691 |
| pick5 | 2026_Day | stream_5000 | 321 | 11.90% | 30.59% | +0.001009 |
| pick5 | 2026_Day | recent_500 | 321 | 12.15% | 32.02% | +0.003033 |
| pick5 | 2026_Day | hier_stream | 321 | 12.02% | 30.97% | +0.002116 |
| pick5 | 2026_Day | multiscale | 321 | 12.52% | 30.72% | +0.002436 |
| pick5 | 2026_Night | global_5000 | 321 | 9.91% | 28.72% | -0.002055 |
| pick5 | 2026_Night | stream_5000 | 321 | 9.91% | 28.97% | -0.001087 |
| pick5 | 2026_Night | recent_500 | 321 | 10.03% | 29.66% | -0.002482 |
| pick5 | 2026_Night | hier_stream | 321 | 9.91% | 29.10% | -0.004377 |
| pick5 | 2026_Night | multiscale | 321 | 9.91% | 28.97% | -0.001588 |

## Research constraint

No new contender can be called a winning system based on
this historical selection. A truly new pre-draw
paper prediction study is required before any promotion.
[Machine-readable results](research_pooled_digit_ablation.json).

