# Live Mispricing Eval Batch V1

Date: March 15, 2026

## Purpose

This is the first live check of whether the MiroFish mispricing workflow can narrow a structural bottleneck thesis into a smaller set of option-expression candidates worth deeper follow-up.

The workflow used here was:

1. Start from five manually defined candidates.
2. Run them through the structural mispricing screen.
3. Take the top names and compare them against recent public option and volatility snapshots.

This is still a screening exercise, not live options pricing or backtesting.

## Input Candidates

- MU LEAPS on packaging duration
- MP Materials long-vol on magnet sovereignty
- VRT calls on cooling deployment bottlenecks
- HUBB calls on transformer lead-time persistence
- LITE calls on InP / CPO dependency

## Screen Results

Ranking by average of `mispricing` and `options_fit`:

| Rank | Underlying | Mispricing | Options Fit | Combined |
| --- | --- | ---: | ---: | ---: |
| 1 | MP | 82.8 | 77.6 | 80.2 |
| 2 | MU | 78.0 | 81.6 | 79.8 |
| 3 | VRT | 66.8 | 72.8 | 69.8 |
| 4 | HUBB | 67.2 | 68.4 | 67.8 |
| 5 | LITE | 75.2 | 58.4 | 66.8 |

Interpretation:

- `MP` ranked first because the sovereignty/magnet thesis still looks structurally underappreciated and options remain a plausible convex expression.
- `MU` ranked second because the packaging-duration thesis matches long-dated options well.
- `VRT` ranked third because facility-side cooling remains an investable deployment bottleneck, though it looks less hidden than `MP` or `MU`.
- `LITE` is the intended negative-control example. The thesis is real, but the options already look expensive enough that the screen penalized the expression.

## Live Snapshot Review

The top three names from the screen were `MP`, `MU`, and `VRT`.

### MP

Screen result:

- Mispricing: `82.8` (`critical`)
- Options fit: `77.6` (`high`)

Recent public market and option snapshots:

- AlphaQuery showed `MP Materials Corp. (MP)` with a last close of `58.03` on `February 13, 2026`, `30-day implied volatility mean` of `70.67%`, and `30-day historical volatility` of `82.55%`.
- ADVFN options pages showed `MP` around `63.013` on `March 2, 2026`. In the `March 6, 2026` chain, the `64 put` was quoted `2.74 x 2.92`, and nearby calls such as the `65 call` were quoted `1.50 x 1.60`.

Read:

- This still looks viable as a long-vol / convexity candidate.
- IV is not obviously cheap in absolute terms, but it does not look as clearly over-owned as `LITE`.
- The public-company expression remains cleaner than the broader rare-earth narrative because MP sits directly on the domestic magnet-independence axis.

### MU

Screen result:

- Mispricing: `78.0` (`high`)
- Options fit: `81.6` (`critical`)

Recent public market and option snapshots:

- AlphaQuery showed `Micron Technology, Inc. (MU)` with a last close of `418.69` on `March 11, 2026`, `30-day implied volatility mean` of `75.98%`, and `120-day historical volatility` of `69.83%`.
- ADVFN options pages showed `MU` around `401.10` on `March 2, 2026`. In the `March 6, 2026` chain, the `410 call` was quoted `10.15 x 10.50`.
- Nasdaq's `March 27th Options Now Available For Micron Technology (MU)` article dated `February 5, 2026` cited a `March 27, 2026` `365 put` bid of `37.15` with the stock at `369.94`.

Read:

- MU still looks like the cleanest `LEAPS-style` candidate in this batch.
- The expression is not "cheap" in any naive sense, but it is the best match between structural thesis duration and listed options structure.
- The main risk is that this thesis may already be partially recognized, so further work needs actual term-structure and event-vol data, not just a single IV snapshot.

### VRT

Screen result:

- Mispricing: `66.8` (`high`)
- Options fit: `72.8` (`high`)

Recent public market and option snapshots:

- AlphaQuery showed `Vertiv Holdings Co. (VRT)` with a last close of `268.26` on `March 11, 2026`, `30-day implied volatility mean` of `64.81%`, and `30-day historical volatility` of `89.91%`.
- AlphaQuery also showed `60-day implied volatility mean` of `64.73%` on `February 6, 2026`, and `180-day implied volatility mean` of `61.86%` on `February 10, 2026`.
- ADVFN options pages showed `VRT` around `243.00` on `March 3, 2026`. In the `March 6, 2026` chain, the `250 call` was quoted `4.80 x 6.00` with `1,309` open interest.

Read:

- VRT still clears the first screen, but this looks more like a directional-plus-convexity setup than a pure hidden-volatility mispricing.
- The gap between recent realized and implied volatility is interesting, but the thesis itself is more visible than `MP` or `MU`.

## Negative-Control Check: LITE

Why `LITE` did not make the top three:

- Screen result:
  - Mispricing: `75.2` (`high`)
  - Options fit: `58.4` (`moderate`)
- AlphaQuery showed `Lumentum Holdings Inc. (LITE)` with a last close of `672.00` on `March 11, 2026` and `30-day implied volatility mean` of `102.78%`.
- AlphaQuery also showed `150-day implied volatility mean` of `107.27%` on `March 6, 2026`.

Read:

- The InP / photonics thesis remains strong.
- The options expression already looks expensive enough that the screen correctly demoted it versus `MP`, `MU`, and `VRT`.
- This is useful evidence that the workflow is doing more than just promoting every structurally interesting story.

## First Conclusion

The first live batch is directionally encouraging.

The workflow produced a usable ordering:

- `MP`: strongest structural mispricing candidate
- `MU`: best long-dated options-expression fit
- `VRT`: still viable, but weaker and more visible
- `LITE`: thesis yes, options no

That is not proof of option mispricing yet, but it is the first sign that the system can separate:

- structural bottleneck importance
- public-market expression quality
- cases where listed optionality already looks too expensive

## What Still Needs To Be Proven

This batch still does **not** answer:

- whether the selected options are actually cheap versus realized forward volatility
- whether term structure is mispriced
- whether skew is favorable
- whether entry timing is good enough to monetize the thesis

The next proof step should be narrower:

1. Pull real chains for `MP`, `MU`, and `VRT`.
2. Compare term structure and skew across several expiries.
3. Define one concrete candidate expression per name.
4. Track those expressions forward against thesis milestones.

## Source Links

- `MU` AlphaQuery 30-day IV mean: https://www.alphaquery.com/stock/MU/volatility-option-statistics/30-day/iv-mean
- `MU` AlphaQuery 120-day historical volatility: https://www.alphaquery.com/stock/MU/volatility-option-statistics/120-day/historical-volatility
- `MU` ADVFN option snapshot: https://investorshub.advfn.com/options/NASDAQ/MU/MU260306C00410000/quote
- `MU` Nasdaq March 27 options article: https://www.nasdaq.com/articles/march-27th-options-now-available-micron-technology-mu

- `MP` AlphaQuery 30-day historical volatility page with IV metrics: https://www.alphaquery.com/stock/MP/volatility-option-statistics
- `MP` AlphaQuery 30-day historical volatility dated page: https://www.alphaquery.com/stock/MP/volatility-option-statistics/30-day/historical-volatility
- `MP` ADVFN option snapshot: https://investorshub.advfn.com/options/NYSE/MP/MP260306P00064000/quote

- `VRT` AlphaQuery 30-day historical volatility page with IV metrics: https://www.alphaquery.com/stock/VRT/volatility-option-statistics
- `VRT` AlphaQuery 60-day IV mean: https://www.alphaquery.com/stock/VRT/volatility-option-statistics/60-day/iv-mean
- `VRT` AlphaQuery 180-day IV mean: https://www.alphaquery.com/stock/VRT/volatility-option-statistics/180-day/iv-mean
- `VRT` ADVFN option snapshot: https://investorshub.advfn.com/options/NYSE/VRT/VRT260306C00250000/quote

- `LITE` AlphaQuery 30-day IV mean: https://www.alphaquery.com/stock/LITE/volatility-option-statistics/30-day/iv-mean
- `LITE` AlphaQuery 150-day IV mean: https://www.alphaquery.com/stock/LITE/volatility-option-statistics/150-day/iv-mean
