# Theme-to-Equity Decomposition v1

This layer sits between promoted structural parses and the pick engine.

## Purpose

Promoted thematic parses should not stop at basket-level expressions like:

- `Equity basket: MP / NEO / UUUU`

They should resolve into explicit per-name candidate rows so the pick engine can
rank actual public equities.

## Implementation

- Service: `backend/app/services/theme_equity_decomposer.py`
- CLI: `scripts/generate_theme_equity_decomposition.py`
- Handoff integration: `scripts/generate_candidates_from_promoted_parses.py`

The decomposer reads:

- `source_bundle`
- `structural_parse`
- `graduation`

and emits a `theme_equity_decomposition` artifact with per-name rows that
include:

- `underlying`
- `company_role`
- `linked_process_layers`
- `linked_components`
- `linked_materials`
- `supporting_claim_ids`
- `supporting_relationship_ids`
- `market_miss_alignment_score_0_to_100`
- `value_capture_alignment_score_0_to_100`
- `expression_readiness_score_0_to_100`
- `decomposition_confidence`

## First Artifact

Robotics actuation v2 decomposition:

- [theme-equity decomposition](/home/d/codex/MiroFish/research/analysis/2026-03-16-robotics-actuation-theme-equity-decomposition-v1.json)

Resolved names:

- `MP`
- `UUUU`
- `NEO`

Current graph-derived role split:

- `MP`: `anchor`
- `UUUU`: `satellite`
- `NEO`: `satellite`

## Pick Flow Impact

The promoted-parse handoff now prefers decomposition rows when available.

Updated artifacts:

- [manifest v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-promoted-parse-manifest-v2.json)
- [candidate rows v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-promoted-parse-candidates-v2.json)
- [ranked picks v2](/home/d/codex/MiroFish/research/analysis/2026-03-16-promoted-parse-picks-v2.json)

This means the robotics thesis now enters the pick flow as explicit names rather
than a single basket thesis.

## Remaining Gap

`MP` currently appears twice in the ranked output:

- once from the standalone `MP` parse
- once from the decomposed robotics parse

That is acceptable for now because the theses are distinct, but eventual
underlying-level deduplication may be useful.
