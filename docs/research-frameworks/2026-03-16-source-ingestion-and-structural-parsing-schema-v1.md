# Source Ingestion And Structural Parsing Schema v1

Date: March 16, 2026

## Purpose

Define the exact schema MiroFish should use for:

- source ingestion
- structural parsing

This is the layer that should come before any final storage decision.

The point is to answer:

- what enters the system?
- how is it normalized?
- what structural objects must the parser emit?
- how do we preserve causal structure and provenance?

This schema is designed for structural information arbitrage, not generic note
taking.

## Design goals

The schema must:

1. support mixed source quality
2. preserve provenance at the fragment and edge level
3. represent causal / dependency structure explicitly
4. support both industrial bottlenecks and geopolitical / event-driven theses
5. separate:
   - evidence
   - inferred structure
   - trade expression

## Part I: Source ingestion schema

Source ingestion should be treated as `evidence intake`, not just file upload.

### 1. Canonical source classes

Every source should be assigned one `source_class`.

Proposed values:

- `company_filing`
- `company_release`
- `earnings_transcript`
- `government`
- `policy_tracker`
- `industry_body`
- `technical_paper`
- `conference_material`
- `trade_press`
- `analyst_note`
- `investor_post`
- `forum_post`
- `user_note`
- `captured_image`
- `market_data_snapshot`

### 2. Canonical source object

Each ingested source should normalize into this shape:

```json
{
  "source_id": "src_xxx",
  "source_class": "company_filing",
  "title": "AXT 10-Q March 31 2025",
  "canonical_url": "https://...",
  "publisher": "AXT",
  "published_at": "2025-05-01T00:00:00Z",
  "retrieved_at": "2026-03-16T00:00:00Z",
  "language": "en",
  "jurisdiction": "US",
  "ticker_refs": ["AXTI"],
  "theme_refs": ["ai_photonics", "inp_substrates"],
  "source_quality": "high",
  "source_reliability_score": 0.88,
  "usage_mode": "evidence",
  "text_hash": "sha256...",
  "attachment_type": "html",
  "notes": []
}
```

### 3. Source quality model

Every source should get both:

- `source_quality` enum
- `source_reliability_score` numeric

Suggested `source_quality` values:

- `high`
- `medium`
- `low`
- `exploratory`

Interpretation:

- `high`
  - direct filing
  - direct policy release
  - direct company release
  - official technical material

- `medium`
  - trade press
  - industry summaries
  - analyst note summaries when the note itself is not fully available

- `low`
  - weak mirrors
  - unattributed summaries

- `exploratory`
  - X posts
  - Reddit comments
  - user notes
  - screenshots without strong provenance

### 4. Usage mode

Every source should carry a `usage_mode`:

- `evidence`
- `context`
- `hypothesis_seed`
- `market_signal`

This prevents a tweet from being silently treated like a filing.

Example:

- SEC filing -> `evidence`
- investor thread -> `hypothesis_seed`
- analyst note excerpt -> `context`
- options chain snapshot -> `market_signal`

### 5. Source fragments

The source object itself is too coarse.
The parser should operate on fragments.

Canonical fragment shape:

```json
{
  "fragment_id": "frag_xxx",
  "source_id": "src_xxx",
  "fragment_type": "paragraph",
  "position_start": 1820,
  "position_end": 2230,
  "section_label": "Risk Factors",
  "excerpt": "short stored excerpt or normalized passage",
  "embedding_ref": "emb_xxx",
  "contains_claim_candidate": true
}
```

Fragments are what:

- vector retrieval should index
- claims should cite
- edges should reference

### 6. Research intent tags

At ingestion time, allow lightweight tags:

- `theme`
- `system`
- `subsystem`
- `event_type`
- `geography`
- `expression_relevance`

This is not the final parse.
It is only first-pass routing.

Example:

- `theme=robotics`
- `subsystem=actuation_motion`
- `geography=china`
- `event_type=export_control`

### 7. Ingestion-specific metadata by source class

Some source classes need extra fields.

Examples:

#### company_filing

- `company_name`
- `form_type`
- `filing_period`
- `sec_accession`

#### investor_post / forum_post

- `author_handle`
- `platform`
- `post_id`
- `reply_count`
- `like_count`
- `quoted_post_id`
- `conversation_id`

#### market_data_snapshot

- `provider`
- `instrument_type`
- `symbol`
- `expiry`
- `captured_market_fields`

## Part II: Structural parsing schema

The parser must produce structured objects, not just embeddings or summaries.

The output should be split into:

1. entities
2. claims
3. relationships
4. evidence links
5. inference objects

### 1. Canonical entity object

```json
{
  "entity_id": "ent_xxx",
  "entity_type": "Component",
  "canonical_name": "Permanent Magnet Motor",
  "aliases": ["PM motor", "torque motor"],
  "description": "Motion-control component used in robotic joints",
  "attributes": {
    "system_role": "actuation_motion",
    "qualification_level": "high",
    "processing_stage": null,
    "ticker": null
  },
  "confidence": "high"
}
```

Entity types should extend the current ontology.
For this use case, the practical set should be:

- `Theme`
- `System`
- `Subsystem`
- `Component`
- `Material`
- `ProcessLayer`
- `Supplier`
- `Customer`
- `PublicCompany`
- `Facility`
- `Geography`
- `PolicyAction`
- `Event`
- `ExpressionCandidate`

This is slightly richer than the current ontology because `Subsystem`,
`ProcessLayer`, `Event`, and `ExpressionCandidate` should be explicit.

### 2. Canonical relationship object

```json
{
  "relationship_id": "rel_xxx",
  "relationship_type": "DEPENDS_ON",
  "source_entity_id": "ent_component_motor",
  "target_entity_id": "ent_material_ndpr",
  "direction": "source_to_target",
  "relationship_strength": "high",
  "causal_role": "required_input",
  "confidence": "medium",
  "evidence_refs": ["ev_xxx", "ev_yyy"],
  "notes": []
}
```

### 3. Required relationship types

The current ontology is a good start, but for structural arbitrage the parser
should produce this broader practical set:

- `PART_OF`
- `USED_IN`
- `DEPENDS_ON`
- `REQUIRES_PROCESSING`
- `PROCESSED_BY`
- `REFINED_BY`
- `SUPPLIED_BY`
- `QUALIFIED_BY`
- `CONSTRAINED_BY`
- `LOCATED_IN`
- `EXPOSED_TO`
- `AFFECTED_BY_POLICY`
- `ALTERNATIVE_TO`
- `BENEFITS_FROM`
- `HURT_BY`
- `ANCHORS`
- `SATELLITE_TO`
- `CANDIDATE_EXPRESSION_FOR`
- `REPRICES_VIA`

These are more useful for actual causal reasoning than a generic graph.

### 4. Canonical claim object

Claims should sit between raw source text and graph edges.

```json
{
  "claim_id": "claim_xxx",
  "claim_type": "market_share_or_concentration",
  "claim_text": "AXT and Sumitomo dominate InP substrate supply",
  "claim_status": "supported",
  "claim_kind": "factual",
  "confidence": "medium",
  "entity_refs": ["ent_axt", "ent_sumitomo", "ent_inp_substrate"],
  "relationship_refs": ["rel_xxx"],
  "source_ids": ["src_a", "src_b"],
  "fragment_ids": ["frag_a1", "frag_b2"],
  "notes": []
}
```

`claim_kind` should be one of:

- `factual`
- `inferential`
- `speculative`

This matters a lot for investor-post ingestion.

### 5. Canonical evidence link object

```json
{
  "evidence_link_id": "ev_xxx",
  "source_id": "src_xxx",
  "fragment_id": "frag_xxx",
  "supports_object_type": "relationship",
  "supports_object_id": "rel_xxx",
  "support_mode": "supporting",
  "strength": "direct"
}
```

This is the provenance layer.
It is what makes the graph auditable.

### 6. Canonical inference object

Not every structural output should be treated as a direct fact.
Some are model inferences.

```json
{
  "inference_id": "inf_xxx",
  "inference_type": "market_miss",
  "statement": "The market underweights neodymium processing relative to robotics end demand",
  "derived_from_claim_ids": ["claim_1", "claim_2", "claim_3"],
  "derived_from_relationship_ids": ["rel_1", "rel_2"],
  "confidence": "medium",
  "falsifiers": [
    "processing capacity expands much faster than expected",
    "motor architecture shifts away from NdFeB dependence"
  ]
}
```

This is where structural synthesis lives.

## Part III: Parsing stages

The parser should not try to do everything in one step.

Use a staged pipeline.

### Stage A. Fragment-level extraction

From each fragment, extract:

- candidate entities
- candidate claims
- candidate relationships
- source-class context

### Stage B. Entity normalization

Resolve:

- aliases
- ticker to company
- process synonyms
- geography normalization

Examples:

- `NdPr oxide`
- `neodymium praseodymium oxide`
- `Nd-Pr oxide`

should converge appropriately.

### Stage C. Relationship typing

Turn textual relations into typed edges.

This is where the model must decide:

- `depends_on`
- `processed_by`
- `supplied_by`
- `located_in`

not just “related to.”

### Stage D. Claim confidence assignment

Assign confidence based on:

- source class
- number of supporting sources
- whether the statement is direct or inferred
- whether the edge is repeated across sources

### Stage E. Inference generation

Only after the graph exists do we generate:

- bottleneck hypotheses
- market-miss hypotheses
- anchor / satellite assignments
- expression candidates

## Part IV: Confidence system

Every structural object should carry confidence.

Minimum fields:

- `confidence`
- `supporting_source_count`
- `supporting_high_quality_source_count`
- `contradictory_source_count`
- `inference_level`

Suggested `inference_level` values:

- `direct`
- `light_inference`
- `strong_inference`

This prevents the system from flattening all outputs into equally trusted facts.

## Part V: What belongs in graph, vector, and provenance

This schema also clarifies storage separation.

### Graph layer

Should store:

- entities
- typed relationships
- claims
- inference objects

### Vector layer

Should store:

- source fragments
- embeddings
- semantic retrieval metadata

### Provenance layer

Should store:

- evidence links
- source / fragment references
- support / contradiction markers

This is why a vector DB alone is not enough.

## Part VI: Minimum implementation contract for MiroFish

Before product polish, the system should be able to do the following:

1. ingest a mixed source set
2. tag each source with quality and usage mode
3. split into fragments
4. extract entities, claims, and typed relationships
5. attach source-backed evidence links
6. build a graph from those objects
7. generate:
   - anchors
   - satellites
   - market-miss hypotheses
   - expression candidates

If MiroFish can do that reliably, it will already be genuinely useful for
structural information arbitrage.

## Part VII: Immediate repo implications

The current ontology and research-mode work are useful, but the next schema
extensions should likely be:

1. add first-class `source_class`, `source_quality`, and `usage_mode`
2. add `fragment` as a canonical object
3. add `claim_kind`
4. add `evidence_link`
5. add explicit `Subsystem`, `ProcessLayer`, `Event`, and `ExpressionCandidate`
6. extend relationship types for `PROCESSED_BY`, `REFINED_BY`, `ANCHORS`,
   `SATELLITE_TO`, and `REPRICES_VIA`

Those changes would make the research graph much closer to the problem you are
actually trying to solve.
