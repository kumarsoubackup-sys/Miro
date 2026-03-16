# LEAPS Strike Rescreen V1

Date: March 16, 2026

## Purpose

This pass re-screens Jan 15, 2027 call strikes by comparing each call against
buying the stock with the same capital.

This is a stronger test than looking at option chains in isolation because it
asks:

- does the option actually improve on same-dollar stock exposure in plausible
  pre-expiration scenarios?

## Method

For each liquid call with reasonable spread and open interest:

- estimate resale value under the bullish scenario set
- compare option PnL to stock PnL using the same initial dollars
- rank strikes by average bullish excess versus stock

This is still approximate and model-based.

## Output

Machine-readable results:

- [2026-03-16-leaps-strike-rescreen-v1.json](/home/d/codex/MiroFish/research/analysis/2026-03-16-leaps-strike-rescreen-v1.json)

Script:

- [rescreen_leaps_strikes_vs_stock.py](/home/d/codex/MiroFish/scripts/rescreen_leaps_strikes_vs_stock.py)

## Intended Read

If a strike ranks poorly here, that usually means:

- the stock thesis may still be fine
- but the specific call is probably a weak same-capital expression

That is exactly the distinction we want this system to make.

## First Read

The first rescreen is directionally strong:

- `MP`
  Same-capital rescreening favors deeper ITM calls, led by `30c`, `25c`, and
  `20c`, over the original `70c` candidate.
- `MU`
  No liquid Jan 15, 2027 call strike in the top screen beats same-capital stock
  exposure under the current rough scenario set.
- `VRT`
  No liquid Jan 15, 2027 call strike in the top screen beats same-capital stock
  exposure under the current rough scenario set.

So the practical implication is:

- `MP`: option expression may still be viable, but likely at lower strikes than
  the first watchlist pick
- `MU`: thesis may be better expressed in stock than calls
- `VRT`: thesis may also be better expressed in stock than calls
