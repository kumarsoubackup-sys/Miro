# SIVE Corroboration Pass v1

## Objective

Use `SIVE` as the first boundary-case calibration test for promotion.

`SIVE` started as a `watchlist_candidate`, not an obvious `pick_candidate`. That made it the best current test of whether the promotion rules are too easy once better sources are added.

## New Evidence Bundle

New bundle:

- [SIVE source bundle v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-source-bundle-v2.json)

Pipeline outputs:

- [SIVE structural parse v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-structural-parse-v2.json)
- [SIVE graduation v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-graduation-v2.json)
- [SIVE acquisition plan v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-source-acquisition-plan-v2.json)
- [SIVE gap report v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-source-gap-report-v2.json)
- [SIVE monitor plan v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-source-monitor-plan-v2.json)

## What Changed

The original `SIVE` parse relied almost entirely on Sivers-originated company releases.

The v2 pass added independent ecosystem corroboration:

- POET official collaboration disclosure
- Ayar Labs ecosystem page naming Sivers
- Ayar OFC-linked technical relevance around external light source architecture

The core thesis did not change. The source mix did.

## Result

v1:

- [SIVE graduation v1](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-graduation-v1.json)
- status: `watchlist_candidate`
- weighted score: `84.45`
- source mix: `69.5`
- failed gate: `high_conviction_source_gate`

v2:

- [SIVE graduation v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-sive-photonics-graduation-v2.json)
- status: `pick_candidate`
- weighted score: `92.89`
- source mix: `90.0`
- all gates pass

Dimension change:

- `source_mix`: `69.5 -> 90.0`
- `structure_quality`: `93.39 -> 90.54`
- `market_miss_quality`: `84.17 -> 94.17`
- `expression_readiness`: `100.0 -> 100.0`

## Interpretation

This is a meaningful result, but it is not enough by itself to prove the promotion rules are perfectly calibrated.

What it does show:

- `SIVE` was not promoted just because it had a good narrative
- it crossed only after adding independent corroboration
- the current system is very sensitive to source-mix quality

What it does not show:

- whether a structurally weaker thesis with polished source mix would also over-promote

So `SIVE v2` should be treated as:

- a successful boundary-case promotion
- and also a warning that source-mix improvements can move borderline theses quickly

## Next Calibration Need

The next anti-overpromotion test should be a structurally weaker idea with good source mix.

That is the cleanest way to answer whether the current graduation rules are too permissive or merely responsive to legitimate corroboration.
