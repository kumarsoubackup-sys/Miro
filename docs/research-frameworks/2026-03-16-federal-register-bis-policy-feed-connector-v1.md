# Federal Register / BIS Policy Feed Connector v1

## Purpose

This is the first real connector slice for the `policy spine`.

It converts normalized Federal Register / BIS feed documents into a regular
`source_bundle` artifact so the existing research pipeline can consume policy
evidence without custom downstream handling.

## Implementation

- Service: [policy_feed_connector.py](/home/d/codex/MiroFish/backend/app/services/policy_feed_connector.py)
- Live Federal Register fetcher: [federal_register_feed.py](/home/d/codex/MiroFish/backend/app/services/federal_register_feed.py)
- CLI: [build_policy_feed_source_bundle.py](/home/d/codex/MiroFish/scripts/build_policy_feed_source_bundle.py)
- Live fetch CLI: [fetch_federal_register_policy_feed.py](/home/d/codex/MiroFish/scripts/fetch_federal_register_policy_feed.py)
- API route:
  - `POST /research/project/<id>/source-bundle/policy-feed-import`
  - `POST /research/project/<id>/source-bundle/federal-register-fetch`

## Input Contract

The connector expects:

- top-level feed payload
- `feed_documents` list

Each feed document should include:

- `document_id`
- `source_target_id`
- `source_target_name`
- `source_class`
- `publisher`
- `title`
- `canonical_url`
- `published_at`
- `retrieved_at`
- `summary`
- `excerpt`
- `theme_refs`
- `research_tags`
- `entity_hints`
- `relationship_hints`
- optional:
  - `claim_candidates`
  - `inference_candidates`

## Output Contract

The connector emits a normal `source_bundle`:

- `sources`
- `fragments`
- `connector_metadata`

That means it can flow directly into:

- structural parsing
- graduation
- decomposition
- knowledge-node aggregation
- node-aware ranking

## Sample Template

Synthetic sample input:

- [federal-register-bis-policy-feed-template-v1.json](/home/d/codex/MiroFish/research/templates/federal-register-bis-policy-feed-template-v1.json)
- [federal-register-api-sample-response-v1.json](/home/d/codex/MiroFish/research/templates/federal-register-api-sample-response-v1.json)
- [federal-register-live-fetch-sample-policy-feed-v1.json](/home/d/codex/MiroFish/research/analysis/2026-03-16-federal-register-live-fetch-sample-policy-feed-v1.json)

The sample is explicitly synthetic and should be treated as a connector
validation artifact, not evidence.

## Why This Matters

The project already knew how to:

- prioritize sources
- plan source acquisition
- build monitor plans

But it did not yet have a connector that turns `policy feed documents` into
evidence intake.

This connector is the first bridge from:

- `source target`

to:

- `normalized source bundle`

## Next Steps

The Federal Register retrieval layer now exists in code. The next useful
expansion is:

- live runtime validation against the real Federal Register API
- selective query profiles by theme
- BIS retrieval layer parallel to the Federal Register path
- event-driven project updates for tracked theses

Current limitation:

- the live fetcher is fully implemented and tested with mocked API responses
- it was not executed against the real network in this environment
