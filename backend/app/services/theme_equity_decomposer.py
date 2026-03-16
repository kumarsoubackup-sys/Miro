"""
Theme-to-equity decomposition for promoted structural parses.

This layer turns a promoted thematic parse into explicit per-name candidate
entries. It is intentionally deterministic and graph-driven so the handoff to
the pick engine does not rely on ad hoc basket text alone.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Set


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _avg(values: Iterable[float], default: float = 0.0) -> float:
    values = [float(value) for value in values]
    if not values:
        return default
    return sum(values) / len(values)


def _score_from_counts(count: int, target: int) -> float:
    if target <= 0:
        return 0.0
    return _clamp((count / target) * 100.0)


def _entity_map(structural_parse: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        entity["entity_id"]: entity
        for entity in structural_parse.get("entities", [])
        if entity.get("entity_id")
    }


def _company_entities(structural_parse: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        entity
        for entity in structural_parse.get("entities", [])
        if entity.get("entity_type") == "PublicCompany"
    ]


def _expressions(structural_parse: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        entity
        for entity in structural_parse.get("entities", [])
        if entity.get("entity_type") == "ExpressionCandidate"
    ]


def _first_theme(structural_parse: Dict[str, Any]) -> str:
    for entity in structural_parse.get("entities", []):
        if entity.get("entity_type") == "Theme":
            return entity.get("canonical_name", "")
    return ""


def _basket_members(expression_name: str) -> List[str]:
    if ":" not in expression_name:
        return []
    label, payload = expression_name.split(":", 1)
    if "basket" not in label.lower():
        return []
    return [
        part.strip().upper()
        for part in payload.replace(",", "/").split("/")
        if part.strip()
    ]


def _share_symbol(expression_name: str) -> str | None:
    if ":" not in expression_name:
        return None
    label, payload = expression_name.split(":", 1)
    if "shares" not in label.lower():
        return None
    symbol = payload.strip().upper()
    return symbol or None


def _resolve_company_expressions(structural_parse: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
    result: Dict[str, Dict[str, List[str]]] = {}
    for expression in _expressions(structural_parse):
        expression_id = expression.get("entity_id")
        expression_name = expression.get("canonical_name", "")
        for symbol in _basket_members(expression_name):
            row = result.setdefault(symbol, {"basket_expression_ids": [], "share_expression_ids": []})
            if expression_id:
                row["basket_expression_ids"].append(expression_id)
        share_symbol = _share_symbol(expression_name)
        if share_symbol:
            row = result.setdefault(share_symbol, {"basket_expression_ids": [], "share_expression_ids": []})
            if expression_id:
                row["share_expression_ids"].append(expression_id)
    return result


def _claim_map(structural_parse: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        claim["claim_id"]: claim
        for claim in structural_parse.get("claims", [])
        if claim.get("claim_id")
    }


def _relationship_map(structural_parse: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        relationship["relationship_id"]: relationship
        for relationship in structural_parse.get("relationships", [])
        if relationship.get("relationship_id")
    }


def _relationships_touching(
    structural_parse: Dict[str, Any],
    *,
    entity_ids: Set[str],
    relationship_types: Set[str] | None = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for relationship in structural_parse.get("relationships", []):
        if relationship_types and relationship.get("relationship_type") not in relationship_types:
            continue
        if (
            relationship.get("source_entity_id") in entity_ids
            or relationship.get("target_entity_id") in entity_ids
        ):
            results.append(relationship)
    return results


def _names_for_entity_ids(entity_map: Dict[str, Dict[str, Any]], entity_ids: Iterable[str], entity_type: str) -> List[str]:
    names: List[str] = []
    for entity_id in entity_ids:
        entity = entity_map.get(entity_id)
        if entity and entity.get("entity_type") == entity_type:
            name = entity.get("canonical_name", "")
            if name and name not in names:
                names.append(name)
    return names


def _linked_process_ids(
    structural_parse: Dict[str, Any],
    company_entity_id: str,
    share_expression_ids: List[str],
) -> List[str]:
    process_ids: List[str] = []
    for relationship in structural_parse.get("relationships", []):
        rel_type = relationship.get("relationship_type")
        source_id = relationship.get("source_entity_id")
        target_id = relationship.get("target_entity_id")
        if rel_type == "SUPPLIED_BY" and target_id == company_entity_id and source_id not in process_ids:
            process_ids.append(source_id)
        if rel_type == "CANDIDATE_EXPRESSION_FOR" and source_id in share_expression_ids and target_id not in process_ids:
            process_ids.append(target_id)
    return process_ids


def _linked_material_ids(structural_parse: Dict[str, Any], process_ids: Set[str]) -> List[str]:
    material_ids: List[str] = []
    for relationship in structural_parse.get("relationships", []):
        if relationship.get("relationship_type") == "PROCESSED_BY" and relationship.get("target_entity_id") in process_ids:
            source_id = relationship.get("source_entity_id")
            if source_id not in material_ids:
                material_ids.append(source_id)
    return material_ids


def _linked_component_ids(structural_parse: Dict[str, Any], material_ids: Set[str], process_ids: Set[str]) -> List[str]:
    component_ids: List[str] = []
    candidate_targets = set(material_ids) | set(process_ids)
    for relationship in structural_parse.get("relationships", []):
        if relationship.get("relationship_type") != "DEPENDS_ON":
            continue
        if relationship.get("target_entity_id") in candidate_targets:
            source_id = relationship.get("source_entity_id")
            if source_id not in component_ids:
                component_ids.append(source_id)
    return component_ids


def _claims_for_company(
    structural_parse: Dict[str, Any],
    *,
    company_entity_id: str,
    share_expression_ids: Set[str],
    basket_expression_ids: Set[str],
    linked_process_ids: Set[str],
    supporting_relationship_ids: Set[str],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    tracked_entity_ids = {company_entity_id} | share_expression_ids | basket_expression_ids | linked_process_ids
    for claim in structural_parse.get("claims", []):
        entity_refs = set(claim.get("entity_refs", []))
        relationship_refs = set(claim.get("relationship_refs", []))
        if tracked_entity_ids & entity_refs or supporting_relationship_ids & relationship_refs:
            results.append(claim)
    return results


def _claim_type_score(claims: List[Dict[str, Any]], claim_type: str, target: int) -> float:
    count = sum(1 for claim in claims if claim.get("claim_type") == claim_type)
    return _score_from_counts(count, target)


def _inference(structural_parse: Dict[str, Any]) -> Dict[str, Any] | None:
    inferences = structural_parse.get("inferences", [])
    return inferences[0] if inferences else None


def build_theme_equity_decomposition(
    source_bundle: Dict[str, Any],
    structural_parse: Dict[str, Any],
    graduation: Dict[str, Any],
) -> Dict[str, Any]:
    entity_map = _entity_map(structural_parse)
    relationship_map = _relationship_map(structural_parse)
    company_expressions = _resolve_company_expressions(structural_parse)
    inference = _inference(structural_parse) or {}

    rows: List[Dict[str, Any]] = []
    theme = _first_theme(structural_parse)
    inference_claim_ids = set(inference.get("derived_from_claim_ids", []))
    inference_relationship_ids = set(inference.get("derived_from_relationship_ids", []))

    for company in sorted(_company_entities(structural_parse), key=lambda entity: entity.get("canonical_name", "")):
        symbol = company.get("canonical_name", "")
        company_entity_id = company.get("entity_id", "")
        expression_refs = company_expressions.get(symbol, {"basket_expression_ids": [], "share_expression_ids": []})
        share_expression_ids = list(dict.fromkeys(expression_refs["share_expression_ids"]))
        basket_expression_ids = list(dict.fromkeys(expression_refs["basket_expression_ids"]))
        process_ids = _linked_process_ids(structural_parse, company_entity_id, share_expression_ids)
        material_ids = _linked_material_ids(structural_parse, set(process_ids))
        component_ids = _linked_component_ids(structural_parse, set(material_ids), set(process_ids))

        tracked_entity_ids = {company_entity_id} | set(share_expression_ids) | set(basket_expression_ids) | set(process_ids)
        supporting_relationships = _relationships_touching(
            structural_parse,
            entity_ids=tracked_entity_ids,
        )
        supporting_relationship_ids = {
            relationship.get("relationship_id")
            for relationship in supporting_relationships
            if relationship.get("relationship_id")
        }
        claims = _claims_for_company(
            structural_parse,
            company_entity_id=company_entity_id,
            share_expression_ids=set(share_expression_ids),
            basket_expression_ids=set(basket_expression_ids),
            linked_process_ids=set(process_ids),
            supporting_relationship_ids=supporting_relationship_ids,
        )
        claim_ids = [claim["claim_id"] for claim in claims if claim.get("claim_id")]

        direct_value_capture_rels = [
            relationship for relationship in supporting_relationships
            if relationship.get("relationship_type") in {"SUPPLIED_BY", "EXPANDS_CAPACITY_FOR", "QUALIFIED_BY"}
        ]
        inference_support_claims = inference_claim_ids & set(claim_ids)
        inference_support_relationships = inference_relationship_ids & supporting_relationship_ids

        graph_centrality_score = _avg([
            _score_from_counts(len(process_ids), 2),
            _score_from_counts(len(component_ids), 2),
            _score_from_counts(len(claim_ids), 3),
            _score_from_counts(len(supporting_relationship_ids), 6),
        ])
        market_miss_alignment_score = _avg([
            graph_centrality_score,
            _score_from_counts(len(inference_support_claims), 2),
            _score_from_counts(len(inference_support_relationships), 4),
            _claim_type_score(claims, "valuation_gap_assertion", 1),
        ])
        value_capture_alignment_score = _avg([
            _score_from_counts(len(direct_value_capture_rels), 3),
            _claim_type_score(claims, "value_capture_assertion", 1),
            _score_from_counts(len(process_ids), 2),
            graph_centrality_score,
        ])
        expression_readiness_score = _avg([
            95.0 if share_expression_ids else 25.0,
            80.0 if basket_expression_ids else 20.0,
            _score_from_counts(len(process_ids), 2),
            _score_from_counts(len(share_expression_ids) + len(basket_expression_ids), 2),
        ])
        decomposition_confidence = _avg([
            graph_centrality_score,
            value_capture_alignment_score,
            expression_readiness_score,
            100.0 if inference_support_claims or inference_support_relationships else 40.0,
        ])

        if graph_centrality_score >= 78.0 or len(process_ids) >= 2:
            company_role = "anchor"
        elif value_capture_alignment_score >= 55.0 or len(claim_ids) >= 1:
            company_role = "satellite"
        else:
            company_role = "weak_mention"

        linked_process_layers = _names_for_entity_ids(entity_map, process_ids, "ProcessLayer")
        linked_materials = _names_for_entity_ids(entity_map, material_ids, "MaterialInput")
        linked_components = _names_for_entity_ids(entity_map, component_ids, "Component")

        process_fragment = ", ".join(linked_process_layers[:2]) if linked_process_layers else "the relevant process layer"
        summary = (
            f"{symbol} is treated as a {company_role} expression for {theme.lower() if theme else 'the theme'} "
            f"through {process_fragment}."
        )

        rows.append(
            {
                "underlying": symbol,
                "theme": theme,
                "company_role": company_role,
                "linked_process_layers": linked_process_layers,
                "linked_components": linked_components,
                "linked_materials": linked_materials,
                "supporting_claim_ids": sorted(claim_ids),
                "supporting_relationship_ids": sorted(supporting_relationship_ids),
                "direct_expression_ids": share_expression_ids,
                "basket_expression_ids": basket_expression_ids,
                "graph_centrality_score_0_to_100": round(graph_centrality_score, 2),
                "market_miss_alignment_score_0_to_100": round(market_miss_alignment_score, 2),
                "value_capture_alignment_score_0_to_100": round(value_capture_alignment_score, 2),
                "expression_readiness_score_0_to_100": round(expression_readiness_score, 2),
                "decomposition_confidence": round(decomposition_confidence, 2),
                "candidate_summary": summary,
                "company_attributes": company.get("attributes", {}),
            }
        )

    rows.sort(
        key=lambda row: (
            row["market_miss_alignment_score_0_to_100"],
            row["value_capture_alignment_score_0_to_100"],
            row["expression_readiness_score_0_to_100"],
            row["decomposition_confidence"],
        ),
        reverse=True,
    )

    return {
        "decomposer_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_bundle_name": source_bundle.get("name"),
        "graduation_status": graduation.get("graduation_status"),
        "theme": theme,
        "row_count": len(rows),
        "rows": rows,
        "market_miss_statement": inference.get("statement", ""),
        "summary": {
            "public_company_count": len(_company_entities(structural_parse)),
            "resolved_company_count": len(rows),
            "top_underlyings": [row["underlying"] for row in rows[:5]],
        },
    }

