# Public Options Chain Capture V1

Date: March 15, 2026

## Purpose

This is the first actual chain-capture implementation for the mispricing
workflow.

It is intentionally:

- public-page first
- user mediated
- generic rather than site hard-coded
- compatible with the existing normalization step

This avoids overcommitting to a brittle broker DOM or a terms-sensitive
site-specific scraper while still giving us a path to collect proof-of-concept
LEAPS data.

## Components

- [capture_options_chain_playwright.mjs](/home/d/codex/MiroFish/scripts/capture_options_chain_playwright.mjs)
- [normalize_options_chain_snapshot.py](/home/d/codex/MiroFish/scripts/normalize_options_chain_snapshot.py)
- [options-chain-capture-rows-template.csv](/home/d/codex/MiroFish/research/templates/options-chain-capture-rows-template.csv)
- [options-chain-snapshot-template.json](/home/d/codex/MiroFish/research/templates/options-chain-snapshot-template.json)

## How It Works

### Step 1: Capture a visible table

The Playwright script opens a browser, lets the user prepare the page manually,
then captures the currently visible HTML tables.

It scores tables based on option-chain-like headers such as:

- `strike`
- `bid`
- `ask`
- `open interest`
- `iv`

The highest-scoring visible table is exported as:

- `capture-summary.json`
- `best-table.csv`

Artifacts are written under:

- `research/options-data/raw/<UNDERLYING>/<TIMESTAMP>/`

Example:

```bash
node scripts/capture_options_chain_playwright.mjs \
  --url "https://www.nasdaq.com/market-activity/stocks/mu/option-chain" \
  --underlying MU \
  --provider nasdaq-public
```

### Step 2: Normalize the captured CSV

The normalizer now supports:

- common header aliases
- fallback metadata from CLI args
- OCC option-symbol parsing when present

Example:

```bash
python3 scripts/normalize_options_chain_snapshot.py \
  research/options-data/raw/MU/<TIMESTAMP>/best-table.csv \
  --output-json research/options-data/2026-03-15/MU-chain.json \
  --provider nasdaq-public \
  --underlying MU \
  --expiry 2027-01-15 \
  --right call
```

## Design Notes

- The script does not automate search or login flows.
- The user is expected to navigate the page manually and press Enter only when
  the desired table is visible.
- This is better aligned with a proof-of-concept workflow than a full scraper.
- Some pages will still require manual normalization inputs, especially when
  they separate calls and puts or do not expose expiry per row.

## Validation

The Playwright script itself is syntax-checkable locally, but it still requires
the `playwright` package to run.

The normalization path was validated locally with sample capture data.

## Next Step

Use this flow on a single public page for `MP` or `MU`, then inspect:

- whether the right table is selected automatically
- whether headers map cleanly into the canonical schema
- whether one far-dated expiry is enough to define a candidate LEAPS expression
