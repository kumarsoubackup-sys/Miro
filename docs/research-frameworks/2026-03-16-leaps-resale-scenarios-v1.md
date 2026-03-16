# LEAPS Resale Scenarios V1

Date: March 16, 2026

## Purpose

This layer shifts the watchlist from `expiration payoff only` to rough
`pre-expiration resale value` estimates.

That matters because the working strategy is not primarily:

- buy LEAPS
- hold to exercise

It is more likely:

- buy long-dated optionality before a thesis reprices
- resell the contract later if stock price and/or implied volatility move in our
  favor

## Method

For each watched contract, this model uses:

- baseline midpoint from the captured watchlist observation
- baseline implied volatility from the same observation
- a reference underlying spot
- the contract strike and expiry
- a simple Black-Scholes call estimate under future scenarios

The model outputs a rough estimated resale value under:

- stock up, IV flat
- stock up, IV up
- stock flat, IV up
- stock up strongly, IV flat
- delay / theta drag
- thesis failure

## Caveat

This is not a live pricing engine.

It is only a rough scenario layer for:

- directional intuition
- vega intuition
- understanding whether a contract might work before expiration

It does not account for:

- changing skew shape
- dividends beyond the zero-yield assumption
- early exercise effects
- real market microstructure
- live borrow or hedge dynamics

## Components

- [estimate_leaps_resale_scenarios.py](/home/d/codex/MiroFish/scripts/estimate_leaps_resale_scenarios.py)
- [2026-03-15-leaps-watchlist-v1.json](/home/d/codex/MiroFish/research/watchlists/2026-03-15-leaps-watchlist-v1.json)

Example:

```bash
python3 scripts/estimate_leaps_resale_scenarios.py \
  research/watchlists/2026-03-15-leaps-watchlist-v1.json \
  --output-json research/analysis/2026-03-16-leaps-resale-scenarios-v1.json
```

## What Changes Conceptually

This makes the analysis much closer to the strategy we are actually trying to
study.

Instead of asking only:

- what happens at expiration?

we can now ask:

- what if the stock is up 10% in 90 days?
- what if the stock is flat but implied volatility jumps?
- what if the thesis is delayed and time decay starts to matter?

## Next Step

The next useful extension is to connect this scenario layer back to fresh chain
captures so we can compare:

- rough model price
- public delayed market midpoint

over time.
