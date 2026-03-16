# LEAPS Watchlist V1

Date: March 15, 2026

## Scope

This watchlist turns the first public delayed LEAPS comparison into a tracked
set of concrete contracts.

Tracked contracts:

- `MP 2027-01-15 70c`
- `MU 2027-01-15 440c`
- `VRT 2027-01-15 270c`

## Baseline

### MP 2027-01-15 70c

- bid `10.55`
- ask `11.10`
- mid `10.825`
- open interest `7,947`
- implied volatility `72.14%`
- relative spread `5.08%`

### MU 2027-01-15 440c

- bid `106.05`
- ask `109.10`
- mid `107.575`
- open interest `892`
- implied volatility `73.56%`
- relative spread `2.84%`

### VRT 2027-01-15 270c

- bid `56.55`
- ask `59.30`
- mid `57.925`
- open interest `1,040`
- implied volatility `66.47%`
- relative spread `4.75%`

## Tracking Artifact

Machine-readable watchlist:

- [2026-03-15-leaps-watchlist-v1.json](/home/d/codex/MiroFish/research/watchlists/2026-03-15-leaps-watchlist-v1.json)

Refresh script:

- [refresh_leaps_watchlist.py](/home/d/codex/MiroFish/scripts/refresh_leaps_watchlist.py)

Example:

```bash
python3 scripts/refresh_leaps_watchlist.py \
  research/watchlists/2026-03-15-leaps-watchlist-v1.json \
  --write
```

The refresh step looks up each tracked contract in its configured normalized
snapshot and appends a new observation if the timestamp is new.

## What To Watch

- midpoint changes
- implied volatility changes
- open-interest trend
- spread deterioration or improvement

## Next Step

The next useful extension is to capture fresh public delayed snapshots on later
dates and append them into this watchlist so we can see whether the chain-level
ranking ages well over time.
