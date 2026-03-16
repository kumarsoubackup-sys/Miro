# KO Defensive Baseline Control v1

## Objective

Create an adversarial false-positive control:

- strong official source mix
- low-volatility, well-known company
- low asymmetry thesis

If this promoted to `pick_candidate`, the graduation rules would be too permissive.

## Artifacts

- [source bundle](/home/d/codex/MiroFish/research/analysis/2026-03-16-ko-defensive-baseline-source-bundle-v1.json)
- [structural parse](/home/d/codex/MiroFish/research/analysis/2026-03-16-ko-defensive-baseline-structural-parse-v1.json)
- [graduation](/home/d/codex/MiroFish/research/analysis/2026-03-16-ko-defensive-baseline-graduation-v1.json)
- [source gap report](/home/d/codex/MiroFish/research/analysis/2026-03-16-ko-defensive-baseline-source-gap-report-v1.json)

## Result

The control stayed below promotion:

- status: `exploratory_only`
- weighted score: `64.95`

Dimension scores:

- `source_mix`: `89.0`
- `structure_quality`: `51.4`
- `market_miss_quality`: `34.67`
- `expression_readiness`: `100.0`

Failed gates:

- `structure_gate`
- `market_miss_gate`

## Interpretation

This is the first direct evidence that the current rules do not automatically promote a thesis just because it has:

- polished official sources
- a clean public equity expression
- a stable, credible business

The weak point was exactly where it should be weak:

- the market-miss inference is incremental and low-confidence
- there is no real structural asymmetry
- the idea reads like defensive quality, not structural information arbitrage

## Caveat

The downstream acquisition and gap-planning outputs are less meaningful for this control than for the AI / photonics / critical-materials cases, because the current source registry is tuned toward those structural domains.

That does not weaken the core calibration result:

`strong source quality alone was not enough to promote KO to pick_candidate`
