# Source Acquisition Planning v1

## Purpose

Turn the `source_registry` into a project-aware acquisition plan instead of a static list.

This layer answers:

- what sources should be ingested next for a thesis
- what source gaps are blocking promotion
- which source classes should be covered before an exploratory parse is allowed to upgrade

## Current Implementation

Primary planner:

- [source_registry.py](/home/d/codex/MiroFish/backend/app/services/source_registry.py)

Supporting interfaces:

- [research project model](/home/d/codex/MiroFish/backend/app/models/research_project.py)
- [research API](/home/d/codex/MiroFish/backend/app/api/research.py)
- [registry prioritization script](/home/d/codex/MiroFish/scripts/prioritize_source_registry_for_project.py)

Generated example:

- [robotics actuation acquisition plan](/home/d/codex/MiroFish/research/analysis/2026-03-16-robotics-actuation-source-acquisition-plan-v1.json)

## Planner Logic

The planner uses four inputs:

- `source_registry`
- `thesis_intake`
- `source_bundle`
- `structural_parse`
- optional `graduation`

It computes:

- inferred project domains
- source-quality and evidence gaps
- missing corroboration classes
- acquisition priority per source target

## Key Design Choice

The planner does not simply sort by source priority score.

That caused bad behavior: too many government-policy targets and not enough corroboration diversity.

The current planner first identifies the missing source jobs implied by the parse, then ensures coverage across those jobs:

- policy context
- company disclosures
- supplier / qualification confirmation
- foreign exchange coverage
- industry validation
- conference / architecture validation
- expression validation
- trade-flow coverage

Only after that does it fill remaining slots with high-scoring diverse targets.

## Example Read

For the robotics actuation exploratory parse, the plan now prioritizes a better mix:

- BIS / CHIPS / Federal Register for policy and export-control context
- SEC EDGAR for company disclosure coverage
- partnership / qualification disclosures for supplier edge confirmation
- ASX for foreign listed upstream names
- Advanced Photonics Coalition and DesignCon for architecture / industry validation
- trade-flow data for cross-border bottleneck confirmation

That is the right shape for promotion work:

- exploratory graph first
- targeted corroboration next
- rerun parse after evidence intake

## Why This Matters

This is the first layer that makes the source registry operational.

Instead of manually deciding what to research next, MiroFish can now produce a project-specific answer to:

`what information should we acquire next to strengthen this thesis?`
