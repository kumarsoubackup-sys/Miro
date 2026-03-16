#!/usr/bin/env python3
"""
Generate pick-pipeline candidate rows from graduated structural parses.

Only promoted parses are eligible:
- watchlist_candidate
- pick_candidate
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


STATUS_ORDER = {
    "exploratory_only": 0,
    "watchlist_candidate": 1,
    "pick_candidate": 2,
}

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT / "research"
WATCHLIST_PATH = RESEARCH_ROOT / "watchlists" / "2026-03-15-leaps-watchlist-v1.json"
RESALE_SCENARIOS_PATH = RESEARCH_ROOT / "analysis" / "2026-03-16-leaps-resale-scenarios-v1.json"
STRIKE_RESCREEN_PATH = RESEARCH_ROOT / "analysis" / "2026-03-16-leaps-strike-rescreen-v1.json"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    return _load_json(path)


def _normalize_rows(payload: Dict[str, Any] | List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise ValueError("manifest must be a list or an object with a 'rows' list")


def _status_allowed(status: str, minimum_status: str) -> bool:
    return STATUS_ORDER.get(status, -1) >= STATUS_ORDER[minimum_status]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _avg(values: Iterable[float], default: float = 0.0) -> float:
    values = [float(value) for value in values]
    if not values:
        return default
    return sum(values) / len(values)


def _score_from_counts(count: int, target: int) -> float:
    if target <= 0:
        return 0.0
    return _clamp(_ratio(count, target) * 100.0)


def _score_from_inverse(value: float, good_max: float, bad_max: float) -> float:
    if value <= good_max:
        return 100.0
    if value >= bad_max:
        return 0.0
    span = bad_max - good_max
    if span <= 0:
        return 0.0
    return _clamp((1.0 - ((value - good_max) / span)) * 100.0)


def _statement_marker_score(statement: str, markers: Iterable[str]) -> float:
    lowered = statement.lower()
    markers = list(markers)
    hits = sum(1 for marker in markers if marker in lowered)
    return _score_from_counts(hits, max(1, len(markers)))


def _find_entities(structural_parse: Dict[str, Any], entity_type: str) -> List[Dict[str, Any]]:
    return [
        entity for entity in structural_parse.get("entities", [])
        if entity.get("entity_type") == entity_type
    ]


def _find_relationships(structural_parse: Dict[str, Any], relationship_type: str) -> List[Dict[str, Any]]:
    return [
        relationship for relationship in structural_parse.get("relationships", [])
        if relationship.get("relationship_type") == relationship_type
    ]


def _entity_map(structural_parse: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        entity["entity_id"]: entity for entity in structural_parse.get("entities", [])
    }


def _first_expression(structural_parse: Dict[str, Any]) -> Dict[str, Any] | None:
    expressions = _find_entities(structural_parse, "ExpressionCandidate")
    if not expressions:
        return None
    expressions.sort(key=lambda entity: entity.get("canonical_name", ""))
    return expressions[0]


def _extract_underlying(expression: Dict[str, Any] | None, structural_parse: Dict[str, Any]) -> str:
    if expression:
        name = expression.get("canonical_name", "")
        if ":" in name:
            maybe = name.split(":", 1)[1].strip()
            if maybe:
                return maybe
    companies = _find_entities(structural_parse, "PublicCompany")
    if companies:
        companies.sort(key=lambda entity: entity.get("canonical_name", ""))
        return companies[0].get("canonical_name", "")
    return "UNKNOWN"


def _expression_for_underlying(
    structural_parse: Dict[str, Any],
    underlying: str,
    preferred_expression_ids: Iterable[str] | None = None,
) -> Dict[str, Any] | None:
    expressions = _find_entities(structural_parse, "ExpressionCandidate")
    if not expressions:
        return None

    preferred_ids = set(preferred_expression_ids or [])
    if preferred_ids:
        for expression in expressions:
            if expression.get("entity_id") in preferred_ids:
                return expression

    preferred_name = f"Shares: {underlying}".lower()
    for expression in expressions:
        if expression.get("canonical_name", "").strip().lower() == preferred_name:
            return expression

    return _first_expression(structural_parse)


def _choose_theme(structural_parse: Dict[str, Any], expression: Dict[str, Any] | None) -> str:
    entities = _entity_map(structural_parse)
    if expression:
        for relationship in _find_relationships(structural_parse, "CANDIDATE_EXPRESSION_FOR"):
            if relationship.get("source_entity_id") == expression.get("entity_id"):
                target = entities.get(relationship.get("target_entity_id"))
                if target and target.get("entity_type") in {"Theme", "BottleneckLayer", "ProcessLayer"}:
                    return target.get("canonical_name", "")
    themes = _find_entities(structural_parse, "Theme")
    if themes:
        return themes[0].get("canonical_name", "")
    return ""


def _choose_bottleneck_layer(structural_parse: Dict[str, Any], underlying: str) -> str:
    entities = _entity_map(structural_parse)
    process_layers = _find_entities(structural_parse, "ProcessLayer")
    if not process_layers:
        return ""

    scores: Dict[str, int] = {entity["entity_id"]: 0 for entity in process_layers}
    for relationship in structural_parse.get("relationships", []):
        rel_type = relationship.get("relationship_type")
        source_id = relationship.get("source_entity_id")
        target_id = relationship.get("target_entity_id")
        source = entities.get(source_id, {})
        target = entities.get(target_id, {})

        if source_id in scores and rel_type in {"AFFECTED_BY_EVENT", "SUPPLIED_BY", "EXPANDS_CAPACITY_FOR"}:
            scores[source_id] += 2
        if target_id in scores and rel_type in {"DEPENDS_ON", "CANDIDATE_EXPRESSION_FOR"}:
            scores[target_id] += 2
        if source.get("entity_type") == "ProcessLayer" and target.get("entity_type") == "PublicCompany":
            if target.get("canonical_name") == underlying:
                scores[source_id] += 4
        if source.get("entity_type") == "Component" and target.get("entity_type") == "ProcessLayer":
            scores[target_id] += 1

    best_id = max(scores, key=lambda entity_id: scores[entity_id])
    return entities[best_id].get("canonical_name", "")


def _choose_value_capture_layer(structural_parse: Dict[str, Any], underlying: str) -> str:
    entities = _entity_map(structural_parse)
    for relationship in _find_relationships(structural_parse, "SUPPLIED_BY"):
        target = entities.get(relationship.get("target_entity_id"), {})
        source = entities.get(relationship.get("source_entity_id"), {})
        if target.get("canonical_name") == underlying and source.get("entity_type") == "ProcessLayer":
            return source.get("canonical_name", "")
    return _choose_bottleneck_layer(structural_parse, underlying)


def _choose_catalysts(structural_parse: Dict[str, Any], expression: Dict[str, Any] | None) -> List[str]:
    entities = _entity_map(structural_parse)
    catalysts: List[str] = []
    if expression:
        for relationship in _find_relationships(structural_parse, "REPRICES_VIA"):
            if relationship.get("source_entity_id") == expression.get("entity_id"):
                target = entities.get(relationship.get("target_entity_id"))
                if target:
                    catalysts.append(target.get("canonical_name", ""))
    if not catalysts:
        for event in _find_entities(structural_parse, "Event"):
            catalysts.append(event.get("canonical_name", ""))
    deduped = []
    for catalyst in catalysts:
        if catalyst and catalyst not in deduped:
            deduped.append(catalyst)
    return deduped[:5]


def _choose_invalidations(graduation: Dict[str, Any], structural_parse: Dict[str, Any]) -> List[str]:
    inferences = structural_parse.get("inferences", [])
    if inferences:
        falsifiers = inferences[0].get("falsifiers", [])
        if falsifiers:
            return falsifiers[:5]
    return [
        "independent corroboration fails to improve",
        "market-miss thesis loses structural support",
    ]


def _market_miss_statement(structural_parse: Dict[str, Any]) -> str:
    inferences = structural_parse.get("inferences", [])
    if inferences:
        return inferences[0].get("statement", "")
    claims = structural_parse.get("claims", [])
    if claims:
        return claims[0].get("claim_text", "")
    return ""


def _why_missed_from_statement(statement: str, graduation_status: str) -> List[str]:
    reasons = ["market framing appears stale relative to the structural role"]
    lowered = statement.lower()
    if "upstream" in lowered:
        reasons.append("upstream supplier role is not obvious from headline narratives")
    if "mining story" in lowered:
        reasons.append("the market may still anchor on an outdated business description")
    if graduation_status == "watchlist_candidate":
        reasons.append("the thesis still needs more independent corroboration")
    return reasons


def _rescale(score: float) -> float:
    return round(max(0.5, min(5.0, score / 20.0)), 1)


def _relative_spread(bid: float, ask: float) -> float | None:
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return None
    return (ask - bid) / mid


def _find_source(source_bundle: Dict[str, Any], source_id: str) -> Dict[str, Any] | None:
    for source in source_bundle.get("sources", []):
        if source.get("source_id") == source_id:
            return source
    return None


def _parse_evidence_summary(
    source_bundle: Dict[str, Any],
    structural_parse: Dict[str, Any],
    graduation: Dict[str, Any],
    underlying: str,
    catalysts: List[str],
    invalidations: List[str],
    decomposition_entry: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    sources = list(source_bundle.get("sources", []))
    entities = list(structural_parse.get("entities", []))
    relationships = list(structural_parse.get("relationships", []))
    claims = list(structural_parse.get("claims", []))
    evidence_links = list(structural_parse.get("evidence_links", []))
    inferences = list(structural_parse.get("inferences", []))

    total_sources = len(sources)
    evidence_sources = sum(1 for source in sources if source.get("usage_mode") == "evidence")
    high_quality_sources = sum(1 for source in sources if source.get("source_quality") == "high")
    independent_sources = sum(
        1
        for source in sources
        if source.get("source_class") not in {"company_release", "earnings_transcript"}
    )
    company_driven_sources = sum(
        1
        for source in sources
        if source.get("source_class") in {"company_release", "earnings_transcript"}
    )
    source_classes = sorted({source.get("source_class", "unknown") for source in sources})

    entity_types = {}
    for entity in entities:
        entity_type = entity.get("entity_type", "unknown")
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    relationship_types = {}
    for relationship in relationships:
        relationship_type = relationship.get("relationship_type", "unknown")
        relationship_types[relationship_type] = relationship_types.get(relationship_type, 0) + 1

    supporting_source_ids = {
        evidence_link.get("source_id")
        for evidence_link in evidence_links
        if evidence_link.get("source_id")
    }
    supporting_source_classes = sorted(
        {
            (_find_source(source_bundle, source_id) or {}).get("source_class", "unknown")
            for source_id in supporting_source_ids
        }
    )

    public_companies = [
        entity.get("canonical_name")
        for entity in entities
        if entity.get("entity_type") == "PublicCompany"
    ]
    related_companies = sorted(
        company for company in public_companies
        if company and company != underlying
    )

    market_miss_detail = graduation["dimensions"]["market_miss_quality"]["detail"]
    confidence = market_miss_detail.get("confidence", "low")
    confidence_score = {"low": 40.0, "medium": 70.0, "high": 100.0}.get(confidence, 40.0)
    statement = market_miss_detail.get("statement", "")

    summary = {
        "total_sources": total_sources,
        "evidence_sources": evidence_sources,
        "high_quality_sources": high_quality_sources,
        "independent_sources": independent_sources,
        "company_driven_sources": company_driven_sources,
        "source_class_diversity": len(source_classes),
        "source_classes": source_classes,
        "supporting_source_classes": supporting_source_classes,
        "entity_count": len(entities),
        "relationship_count": len(relationships),
        "claim_count": len(claims),
        "evidence_link_count": len(evidence_links),
        "inference_count": len(inferences),
        "evidence_links_per_claim": round(_ratio(len(evidence_links), max(len(claims), 1)), 2),
        "process_layer_count": entity_types.get("ProcessLayer", 0),
        "event_count": entity_types.get("Event", 0),
        "expression_count": entity_types.get("ExpressionCandidate", 0),
        "public_company_count": entity_types.get("PublicCompany", 0),
        "related_company_count": len(related_companies),
        "related_companies": related_companies,
        "supplied_by_count": relationship_types.get("SUPPLIED_BY", 0),
        "depends_on_count": relationship_types.get("DEPENDS_ON", 0),
        "constrained_by_count": relationship_types.get("CONSTRAINED_BY", 0),
        "reprices_via_count": relationship_types.get("REPRICES_VIA", 0),
        "affected_by_event_count": relationship_types.get("AFFECTED_BY_EVENT", 0),
        "part_of_count": relationship_types.get("PART_OF", 0),
        "market_miss_confidence": confidence,
        "market_miss_confidence_score_0_to_100": confidence_score,
        "market_miss_derived_claim_count": market_miss_detail.get("derived_claim_count", 0),
        "market_miss_derived_relationship_count": market_miss_detail.get("derived_relationship_count", 0),
        "catalyst_count": len(catalysts),
        "invalidation_count": len(invalidations),
        "statement": statement,
        "upstream_marker_score_0_to_100": _statement_marker_score(
            statement,
            ["upstream", "supplier", "not obvious", "hidden", "indirect"],
        ),
        "stale_frame_marker_score_0_to_100": _statement_marker_score(
            statement,
            ["frame", "framing", "too narrowly", "treat", "story"],
        ),
        "messy_small_marker_score_0_to_100": _statement_marker_score(
            statement,
            ["messy", "small", "nordic", "undiscovered", "underfollowed"],
        ),
    }
    if decomposition_entry:
        summary.update(
            {
                "decomposition_company_role": decomposition_entry.get("company_role"),
                "decomposition_linked_process_count": len(decomposition_entry.get("linked_process_layers", [])),
                "decomposition_linked_component_count": len(decomposition_entry.get("linked_components", [])),
                "decomposition_linked_material_count": len(decomposition_entry.get("linked_materials", [])),
                "decomposition_supporting_claim_count": len(decomposition_entry.get("supporting_claim_ids", [])),
                "decomposition_supporting_relationship_count": len(decomposition_entry.get("supporting_relationship_ids", [])),
                "decomposition_market_miss_alignment_score_0_to_100": float(
                    decomposition_entry.get("market_miss_alignment_score_0_to_100") or 0.0
                ),
                "decomposition_value_capture_alignment_score_0_to_100": float(
                    decomposition_entry.get("value_capture_alignment_score_0_to_100") or 0.0
                ),
                "decomposition_expression_readiness_score_0_to_100": float(
                    decomposition_entry.get("expression_readiness_score_0_to_100") or 0.0
                ),
                "decomposition_confidence": float(decomposition_entry.get("decomposition_confidence") or 0.0),
            }
        )
    return summary


def _iter_option_snapshot_paths(symbol: str) -> List[Path]:
    options_root = RESEARCH_ROOT / "options-data"
    if not options_root.exists():
        return []
    return sorted(options_root.rglob(f"{symbol}-chain-*.json"))


def _summarize_option_snapshots(symbol: str) -> Dict[str, Any]:
    snapshot_paths = _iter_option_snapshot_paths(symbol)
    if not snapshot_paths:
        return {
            "snapshot_count": 0,
            "has_long_dated_options": False,
            "quoted_contract_count": 0,
            "liquid_contract_count": 0,
            "best_open_interest": 0,
            "best_relative_spread": None,
            "best_implied_volatility": None,
            "latest_snapshot_path": None,
        }

    quoted_contract_count = 0
    liquid_contract_count = 0
    best_open_interest = 0
    best_relative_spread = None
    best_implied_volatility = None
    latest_snapshot_path = str(snapshot_paths[-1].relative_to(ROOT))

    for path in snapshot_paths:
        payload = _load_json(path)
        for expiry_payload in payload.get("expiries", []):
            for contract in expiry_payload.get("contracts", []):
                if contract.get("right") != "call":
                    continue
                bid = float(contract.get("bid") or 0.0)
                ask = float(contract.get("ask") or 0.0)
                if bid > 0 and ask > 0:
                    quoted_contract_count += 1
                relative_spread = _relative_spread(bid, ask)
                open_interest = int(contract.get("open_interest") or 0)
                implied_volatility = float(contract.get("implied_volatility") or 0.0)
                if (
                    bid > 0
                    and ask > 0
                    and open_interest >= 100
                    and implied_volatility > 0
                    and relative_spread is not None
                    and relative_spread <= 0.09
                ):
                    liquid_contract_count += 1
                    best_open_interest = max(best_open_interest, open_interest)
                    if best_relative_spread is None or relative_spread < best_relative_spread:
                        best_relative_spread = relative_spread
                        best_implied_volatility = implied_volatility

    return {
        "snapshot_count": len(snapshot_paths),
        "has_long_dated_options": quoted_contract_count > 0,
        "quoted_contract_count": quoted_contract_count,
        "liquid_contract_count": liquid_contract_count,
        "best_open_interest": best_open_interest,
        "best_relative_spread": round(best_relative_spread, 4) if best_relative_spread is not None else None,
        "best_implied_volatility": round(best_implied_volatility, 4) if best_implied_volatility is not None else None,
        "latest_snapshot_path": latest_snapshot_path,
    }


def _load_watchlist_entry(symbol: str) -> Dict[str, Any] | None:
    payload = _load_optional_json(WATCHLIST_PATH)
    if not payload:
        return None
    for entry in payload.get("entries", []):
        if entry.get("symbol") == symbol:
            return entry
    return None


def _load_resale_entry(symbol: str) -> Dict[str, Any] | None:
    payload = _load_optional_json(RESALE_SCENARIOS_PATH)
    if not payload:
        return None
    for entry in payload.get("entries", []):
        if entry.get("symbol") == symbol:
            return entry
    return None


def _load_rescreen_rows(symbol: str) -> List[Dict[str, Any]]:
    payload = _load_optional_json(STRIKE_RESCREEN_PATH)
    if not payload:
        return []
    return list((payload.get("symbols") or {}).get(symbol, []))


def _market_data_checks(symbol: str) -> Dict[str, Any]:
    snapshot_summary = _summarize_option_snapshots(symbol)
    watchlist_entry = _load_watchlist_entry(symbol)
    resale_entry = _load_resale_entry(symbol)
    rescreen_rows = _load_rescreen_rows(symbol)

    latest_watchlist = (watchlist_entry or {}).get("latest_observation", {})
    watchlist_relative_spread = latest_watchlist.get("relative_spread")
    watchlist_open_interest = latest_watchlist.get("open_interest")
    watchlist_iv = latest_watchlist.get("implied_volatility")

    resale_scenarios = list((resale_entry or {}).get("scenarios", []))
    positive_scenarios = [
        scenario for scenario in resale_scenarios
        if float(scenario.get("estimated_pnl_per_contract") or 0.0) > 0
    ]
    flat_iv_up_positive = any(
        scenario.get("scenario_name") == "stock_flat_iv_up_10pts_90d"
        and float(scenario.get("estimated_pnl_per_contract") or 0.0) > 0
        for scenario in resale_scenarios
    )
    bullish_returns = [
        float(scenario.get("estimated_return_pct") or 0.0)
        for scenario in resale_scenarios
        if float(scenario.get("spot_change_pct") or 0.0) > 0
    ]

    positive_rescreen_rows = [
        row for row in rescreen_rows
        if float(row.get("bullish_excess_vs_stock_mean") or 0.0) > 0
    ]
    best_rescreen = positive_rescreen_rows[0] if positive_rescreen_rows else (rescreen_rows[0] if rescreen_rows else None)

    liquidity_components = []
    if snapshot_summary["liquid_contract_count"] > 0:
        liquidity_components.append(_score_from_counts(snapshot_summary["liquid_contract_count"], 6))
    if snapshot_summary["best_open_interest"] > 0:
        liquidity_components.append(_score_from_counts(snapshot_summary["best_open_interest"], 5000))
    if snapshot_summary["best_relative_spread"] is not None:
        liquidity_components.append(
            _score_from_inverse(snapshot_summary["best_relative_spread"], 0.03, 0.12)
        )
    if watchlist_relative_spread is not None:
        liquidity_components.append(_score_from_inverse(float(watchlist_relative_spread), 0.03, 0.12))
    liquidity_quality = round(_avg(liquidity_components, default=0.0), 2)

    return {
        "snapshot_count": snapshot_summary["snapshot_count"],
        "latest_snapshot_path": snapshot_summary["latest_snapshot_path"],
        "has_long_dated_options": snapshot_summary["has_long_dated_options"],
        "quoted_contract_count": snapshot_summary["quoted_contract_count"],
        "liquid_contract_count": snapshot_summary["liquid_contract_count"],
        "best_open_interest": snapshot_summary["best_open_interest"],
        "best_relative_spread": snapshot_summary["best_relative_spread"],
        "best_implied_volatility": snapshot_summary["best_implied_volatility"],
        "watchlist_entry_present": bool(watchlist_entry),
        "watchlist_option_symbol": (watchlist_entry or {}).get("option_symbol"),
        "watchlist_mid": latest_watchlist.get("mid"),
        "watchlist_open_interest": watchlist_open_interest,
        "watchlist_relative_spread": watchlist_relative_spread,
        "watchlist_implied_volatility": watchlist_iv,
        "resale_scenario_count": len(resale_scenarios),
        "positive_resale_scenario_count": len(positive_scenarios),
        "positive_resale_scenario_ratio": round(
            _ratio(len(positive_scenarios), max(len(resale_scenarios), 1)),
            2,
        ),
        "flat_iv_up_positive": flat_iv_up_positive,
        "best_bullish_return_pct": round(max(bullish_returns), 2) if bullish_returns else None,
        "mean_bullish_return_pct": round(_avg(bullish_returns), 2) if bullish_returns else None,
        "rescreen_candidate_count": len(rescreen_rows),
        "positive_rescreen_count": len(positive_rescreen_rows),
        "best_bullish_excess_vs_stock_mean": (
            round(float(best_rescreen.get("bullish_excess_vs_stock_mean") or 0.0), 2)
            if best_rescreen else None
        ),
        "best_same_capital_contract": (
            {
                "option_symbol": best_rescreen.get("option_symbol"),
                "strike": best_rescreen.get("strike"),
                "open_interest": best_rescreen.get("open_interest"),
                "relative_spread": best_rescreen.get("relative_spread"),
                "bullish_excess_vs_stock_mean": best_rescreen.get("bullish_excess_vs_stock_mean"),
            }
            if best_rescreen
            else None
        ),
        "long_dated_liquidity_quality_score_0_to_100": liquidity_quality,
    }


def _keyword_hits(texts: Iterable[str], markers: Iterable[str]) -> float:
    lowered = " ".join(text.lower() for text in texts if text)
    markers = list(markers)
    hits = sum(1 for marker in markers if marker in lowered)
    return _score_from_counts(hits, max(1, len(markers)))


def _build_signal_blocks(
    source_bundle: Dict[str, Any],
    structural_parse: Dict[str, Any],
    graduation: Dict[str, Any],
    parse_evidence_summary: Dict[str, Any],
    market_data_checks: Dict[str, Any],
    decomposition_entry: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, float]]:
    source_mix = graduation["dimensions"]["source_mix"]["score_0_to_100"]
    structure_quality = graduation["dimensions"]["structure_quality"]["score_0_to_100"]
    market_miss_quality = graduation["dimensions"]["market_miss_quality"]["score_0_to_100"]
    expression_readiness = graduation["dimensions"]["expression_readiness"]["score_0_to_100"]
    statement = parse_evidence_summary["statement"]
    decomposition_market_miss = float(
        parse_evidence_summary.get("decomposition_market_miss_alignment_score_0_to_100") or 0.0
    )
    decomposition_value_capture = float(
        parse_evidence_summary.get("decomposition_value_capture_alignment_score_0_to_100") or 0.0
    )
    decomposition_expression = float(
        parse_evidence_summary.get("decomposition_expression_readiness_score_0_to_100") or 0.0
    )
    decomposition_confidence = float(parse_evidence_summary.get("decomposition_confidence") or 0.0)

    independent_ratio_score = _clamp(
        _ratio(parse_evidence_summary["independent_sources"], max(parse_evidence_summary["total_sources"], 1)) * 100.0
    )
    company_source_concentration = _clamp(
        _ratio(parse_evidence_summary["company_driven_sources"], max(parse_evidence_summary["total_sources"], 1)) * 100.0
    )
    event_richness = _score_from_counts(parse_evidence_summary["event_count"], 4)
    repricing_path = _score_from_counts(parse_evidence_summary["reprices_via_count"], 3)
    dependency_density = _score_from_counts(
        parse_evidence_summary["depends_on_count"]
        + parse_evidence_summary["supplied_by_count"]
        + parse_evidence_summary["constrained_by_count"]
        + parse_evidence_summary["part_of_count"],
        8,
    )
    process_depth = _score_from_counts(parse_evidence_summary["process_layer_count"], 3)
    related_company_score = _score_from_counts(parse_evidence_summary["related_company_count"], 3)
    evidence_density = _clamp(parse_evidence_summary["evidence_links_per_claim"] / 3.0 * 100.0)
    transformation_marker_score = _statement_marker_score(
        statement,
        ["becoming", "platform", "scale", "rerated", "re-rated"],
    )
    invalidation_penalty = _keyword_hits(
        structural_parse.get("inferences", [{}])[0].get("falsifiers", []) if structural_parse.get("inferences") else [],
        ["dilution", "debt", "execution", "delay", "insufficient"],
    )

    hiddenness_0_to_100 = _avg([
        company_source_concentration,
        100.0 - independent_ratio_score,
        market_miss_quality,
        parse_evidence_summary["upstream_marker_score_0_to_100"],
        parse_evidence_summary["messy_small_marker_score_0_to_100"],
        decomposition_market_miss,
    ])
    recognition_gap_0_to_100 = _avg([
        market_miss_quality,
        parse_evidence_summary["market_miss_confidence_score_0_to_100"],
        parse_evidence_summary["stale_frame_marker_score_0_to_100"],
        parse_evidence_summary["upstream_marker_score_0_to_100"],
        decomposition_market_miss,
    ])
    catalyst_clarity_0_to_100 = _avg([
        expression_readiness,
        event_richness,
        repricing_path,
        _score_from_counts(parse_evidence_summary["catalyst_count"], 4),
        decomposition_expression,
    ])
    propagation_asymmetry_0_to_100 = _avg([
        structure_quality,
        dependency_density,
        process_depth,
        related_company_score,
        decomposition_value_capture,
    ])
    duration_mismatch_0_to_100 = _avg([
        recognition_gap_0_to_100,
        structure_quality,
        catalyst_clarity_0_to_100,
        parse_evidence_summary["market_miss_confidence_score_0_to_100"],
        decomposition_confidence,
    ])
    evidence_quality_0_to_100 = _avg([
        source_mix,
        evidence_density,
        _score_from_counts(parse_evidence_summary["claim_count"], 6),
        _score_from_counts(parse_evidence_summary["high_quality_sources"], max(parse_evidence_summary["total_sources"], 1)),
        decomposition_confidence,
    ])
    crowding_inverse_0_to_100 = _avg([
        hiddenness_0_to_100,
        company_source_concentration,
        100.0 - independent_ratio_score,
    ])
    valuation_nonlinearity_0_to_100 = _avg([
        structure_quality,
        market_miss_quality,
        related_company_score,
        parse_evidence_summary["upstream_marker_score_0_to_100"],
        transformation_marker_score,
        decomposition_market_miss,
    ])

    hiddenness_0_to_100 = max(hiddenness_0_to_100, market_miss_quality * 0.45)
    recognition_gap_0_to_100 = max(recognition_gap_0_to_100, market_miss_quality * 0.8)
    catalyst_clarity_0_to_100 = max(catalyst_clarity_0_to_100, expression_readiness * 0.6)
    propagation_asymmetry_0_to_100 = max(propagation_asymmetry_0_to_100, structure_quality * 0.65)
    duration_mismatch_0_to_100 = max(duration_mismatch_0_to_100, _avg([market_miss_quality, structure_quality]))
    valuation_nonlinearity_0_to_100 = max(valuation_nonlinearity_0_to_100, market_miss_quality * 0.55)

    ecosystem_centrality_0_to_100 = _avg([
        propagation_asymmetry_0_to_100,
        structure_quality,
        related_company_score,
        process_depth,
    ])
    downstream_valuation_gap_0_to_100 = _avg([
        valuation_nonlinearity_0_to_100,
        market_miss_quality,
        parse_evidence_summary["upstream_marker_score_0_to_100"],
        related_company_score,
    ])
    microcap_rerating_potential_0_to_100 = _avg([
        hiddenness_0_to_100,
        parse_evidence_summary["messy_small_marker_score_0_to_100"],
        company_source_concentration,
    ])

    liquidity_quality = float(market_data_checks["long_dated_liquidity_quality_score_0_to_100"])
    has_options = bool(market_data_checks["has_long_dated_options"])
    positive_resale_ratio = float(market_data_checks["positive_resale_scenario_ratio"] or 0.0) * 100.0
    flat_iv_up_bonus = 100.0 if market_data_checks["flat_iv_up_positive"] else 20.0
    best_rescreen_advantage = float(market_data_checks["best_bullish_excess_vs_stock_mean"] or 0.0)
    rescreen_advantage_score = _clamp((best_rescreen_advantage + 500.0) / 12.5)
    best_iv = market_data_checks["watchlist_implied_volatility"] or market_data_checks["best_implied_volatility"]
    if best_iv is None:
        iv_score = 10.0 if not has_options else 30.0
    else:
        iv_score = _score_from_inverse(float(best_iv), 0.55, 1.15)

    convexity_need_0_to_100 = _avg([
        valuation_nonlinearity_0_to_100,
        downstream_valuation_gap_0_to_100,
        hiddenness_0_to_100,
    ])
    tenor_alignment_0_to_100 = _avg([
        catalyst_clarity_0_to_100,
        duration_mismatch_0_to_100,
        80.0 if has_options else 25.0,
    ])
    vol_expansion_potential_0_to_100 = _avg([
        catalyst_clarity_0_to_100,
        recognition_gap_0_to_100,
        flat_iv_up_bonus,
    ])
    downside_definedness_0_to_100 = _avg([
        80.0 if has_options else 25.0,
        rescreen_advantage_score if has_options else 25.0,
    ])
    liquidity_path_0_to_100 = liquidity_quality
    implementation_simplicity_0_to_100 = _avg([
        liquidity_quality,
        85.0 if has_options else 20.0,
    ])
    catalyst_timing_specificity_0_to_100 = _avg([
        catalyst_clarity_0_to_100,
        repricing_path,
    ])

    market_accessibility_0_to_100 = _avg([
        85.0,
        source_mix,
        80.0 if market_data_checks["snapshot_count"] > 0 else 65.0,
    ])
    implementation_simplicity_stock_0_to_100 = _avg([
        90.0,
        source_mix,
    ])
    balance_sheet_resilience_0_to_100 = _avg([
        source_mix,
        80.0 if "refinanc" in statement.lower() else 65.0,
        100.0 - invalidation_penalty,
        decomposition_confidence,
    ])
    dilution_risk_inverse_0_to_100 = _avg([
        100.0 - _keyword_hits(
            structural_parse.get("inferences", [{}])[0].get("falsifiers", []) if structural_parse.get("inferences") else [],
            ["dilution", "debt", "term loan", "convertible"],
        ),
        80.0 if "refinanc" in statement.lower() else 60.0,
    ])
    thesis_linearity_0_to_100 = _avg([
        propagation_asymmetry_0_to_100,
        _score_from_counts(parse_evidence_summary["public_company_count"], 2),
        decomposition_value_capture,
    ])
    duration_tolerance_0_to_100 = _avg([
        source_mix,
        parse_evidence_summary["market_miss_confidence_score_0_to_100"],
        catalyst_clarity_0_to_100,
        decomposition_confidence,
    ])
    listing_quality_0_to_100 = _avg([
        90.0 if market_data_checks["snapshot_count"] > 0 else 65.0,
        80.0 if parse_evidence_summary["public_company_count"] > 0 else 0.0,
        decomposition_expression,
    ])

    iv_cheapness_0_to_100 = _avg([
        iv_score,
        100.0 if market_data_checks["positive_rescreen_count"] > 0 else 25.0,
        100.0 if market_data_checks["flat_iv_up_positive"] else 20.0,
    ]) if has_options else 10.0
    surface_staleness_0_to_100 = _avg([
        recognition_gap_0_to_100,
        100.0 if market_data_checks["flat_iv_up_positive"] else 20.0,
        hiddenness_0_to_100,
    ]) if has_options else 10.0
    pre_expiration_repricing_potential_0_to_100 = _avg([
        positive_resale_ratio if market_data_checks["resale_scenario_count"] > 0 else 15.0,
        _clamp((float(market_data_checks["best_bullish_return_pct"] or 0.0) + 20.0) * 2.0),
        catalyst_clarity_0_to_100,
    ]) if has_options else 15.0
    stock_vs_call_convexity_advantage_0_to_100 = _avg([
        rescreen_advantage_score,
        _score_from_counts(market_data_checks["positive_rescreen_count"], 3),
    ]) if has_options else 10.0
    long_dated_liquidity_quality_0_to_100 = liquidity_quality if has_options else 5.0

    mispricing_signals = {
        "hiddenness": _rescale(hiddenness_0_to_100),
        "recognition_gap": _rescale(recognition_gap_0_to_100),
        "catalyst_clarity": _rescale(catalyst_clarity_0_to_100),
        "propagation_asymmetry": _rescale(propagation_asymmetry_0_to_100),
        "duration_mismatch": _rescale(duration_mismatch_0_to_100),
        "evidence_quality": _rescale(evidence_quality_0_to_100),
        "crowding_inverse": _rescale(crowding_inverse_0_to_100),
        "valuation_nonlinearity": _rescale(valuation_nonlinearity_0_to_100),
    }

    asymmetry_signals = {
        "ecosystem_centrality": _rescale(ecosystem_centrality_0_to_100),
        "downstream_valuation_gap": _rescale(downstream_valuation_gap_0_to_100),
        "microcap_rerating_potential": _rescale(microcap_rerating_potential_0_to_100),
    }

    options_expression_signals = {
        "convexity_need": _rescale(convexity_need_0_to_100),
        "tenor_alignment": _rescale(tenor_alignment_0_to_100),
        "vol_expansion_potential": _rescale(vol_expansion_potential_0_to_100),
        "downside_definedness": _rescale(downside_definedness_0_to_100),
        "liquidity_path": _rescale(liquidity_path_0_to_100),
        "implementation_simplicity": _rescale(implementation_simplicity_0_to_100),
        "catalyst_timing_specificity": _rescale(catalyst_timing_specificity_0_to_100),
    }

    stock_expression_signals = {
        "market_accessibility": _rescale(market_accessibility_0_to_100),
        "implementation_simplicity": _rescale(implementation_simplicity_stock_0_to_100),
        "balance_sheet_resilience": _rescale(balance_sheet_resilience_0_to_100),
        "dilution_risk_inverse": _rescale(dilution_risk_inverse_0_to_100),
        "thesis_linearity": _rescale(thesis_linearity_0_to_100),
        "duration_tolerance": _rescale(duration_tolerance_0_to_100),
        "listing_quality": _rescale(listing_quality_0_to_100),
    }

    leaps_bias_signals = {
        "iv_cheapness": _rescale(iv_cheapness_0_to_100),
        "surface_staleness": _rescale(surface_staleness_0_to_100),
        "pre_expiration_repricing_potential": _rescale(pre_expiration_repricing_potential_0_to_100),
        "stock_vs_call_convexity_advantage": _rescale(stock_vs_call_convexity_advantage_0_to_100),
        "long_dated_liquidity_quality": _rescale(long_dated_liquidity_quality_0_to_100),
    }

    return {
        "mispricing_signals": mispricing_signals,
        "asymmetry_signals": asymmetry_signals,
        "options_expression_signals": options_expression_signals,
        "stock_expression_signals": stock_expression_signals,
        "leaps_bias_signals": leaps_bias_signals,
    }


def _candidate_name(underlying: str, theme: str, graduation_status: str, company_role: str | None = None) -> str:
    suffix = {
        "pick_candidate": "promoted structural pick",
        "watchlist_candidate": "structural watchlist",
    }.get(graduation_status, "structural thesis")
    if company_role:
        return f"{underlying} {company_role} {suffix} on {theme}"
    return f"{underlying} {suffix} on {theme}"


def build_candidate_row(
    source_bundle: Dict[str, Any],
    structural_parse: Dict[str, Any],
    graduation: Dict[str, Any],
    decomposition_entry: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if decomposition_entry:
        underlying = decomposition_entry["underlying"]
        expression = _expression_for_underlying(
            structural_parse,
            underlying,
            preferred_expression_ids=decomposition_entry.get("direct_expression_ids", []),
        )
        theme = decomposition_entry.get("theme") or _choose_theme(structural_parse, expression)
        linked_process_layers = list(decomposition_entry.get("linked_process_layers", []))
        bottleneck_layer = linked_process_layers[0] if linked_process_layers else _choose_bottleneck_layer(structural_parse, underlying)
        value_capture_layer = linked_process_layers[0] if linked_process_layers else _choose_value_capture_layer(structural_parse, underlying)
    else:
        expression = _first_expression(structural_parse)
        underlying = _extract_underlying(expression, structural_parse)
        theme = _choose_theme(structural_parse, expression)
        bottleneck_layer = _choose_bottleneck_layer(structural_parse, underlying)
        value_capture_layer = _choose_value_capture_layer(structural_parse, underlying)
    thesis = _market_miss_statement(structural_parse)
    catalysts = _choose_catalysts(structural_parse, expression)
    invalidations = _choose_invalidations(graduation, structural_parse)
    linked_companies = [
        entity.get("canonical_name")
        for entity in _find_entities(structural_parse, "PublicCompany")
    ]
    parse_evidence_summary = _parse_evidence_summary(
        source_bundle,
        structural_parse,
        graduation,
        underlying,
        catalysts,
        invalidations,
        decomposition_entry=decomposition_entry,
    )
    market_data_checks = _market_data_checks(underlying)
    signal_blocks = _build_signal_blocks(
        source_bundle,
        structural_parse,
        graduation,
        parse_evidence_summary,
        market_data_checks,
        decomposition_entry=decomposition_entry,
    )
    time_horizon = "12-24m"
    preferred_expression = expression.get("attributes", {}).get("expression_type") if expression else None
    if preferred_expression == "shares":
        mispricing_type = "structural_information_arbitrage"
    else:
        mispricing_type = "hidden_bottleneck"

    return {
        "name": _candidate_name(
            underlying,
            theme or bottleneck_layer or "theme",
            graduation["graduation_status"],
            company_role=(decomposition_entry or {}).get("company_role"),
        ),
        "market_theme": theme,
        "thesis": thesis,
        "underlying": underlying,
        "mispricing_type": mispricing_type,
        "time_horizon": time_horizon,
        "linked_companies": linked_companies,
        "bottleneck_layer": bottleneck_layer,
        "value_capture_layer": value_capture_layer,
        "why_missed": _why_missed_from_statement(thesis, graduation["graduation_status"]),
        "catalysts": catalysts,
        "invalidations": invalidations,
        "promotion_status": graduation["graduation_status"],
        "promotion_score_0_to_100": graduation["weighted_score_0_to_100"],
        "theme_equity_decomposition": decomposition_entry,
        "parse_evidence_summary": parse_evidence_summary,
        "market_data_checks": market_data_checks,
        **signal_blocks,
        "notes": [
            "Auto-generated from promoted structural parse.",
            f"Promotion status: {graduation['graduation_status']}.",
            *(([decomposition_entry["candidate_summary"]] if decomposition_entry and decomposition_entry.get("candidate_summary") else [])),
            (
                "Local options-chain evidence detected."
                if market_data_checks["has_long_dated_options"]
                else "No usable long-dated options evidence detected locally."
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON list/object describing parse bundles")
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument(
        "--min-status",
        choices=sorted(STATUS_ORDER, key=STATUS_ORDER.get),
        default="watchlist_candidate",
        help="Minimum graduation status allowed into output rows.",
    )
    args = parser.parse_args()

    manifest = _normalize_rows(_load_json(args.manifest))
    rows: List[Dict[str, Any]] = []

    for item in manifest:
        source_bundle = _load_json(Path(item["source_bundle"]))
        structural_parse = _load_json(Path(item["structural_parse"]))
        graduation = _load_json(Path(item["graduation"]))
        if not _status_allowed(graduation["graduation_status"], args.min_status):
            continue
        decomposition_payload = None
        if item.get("theme_equity_decomposition"):
            decomposition_payload = _load_json(Path(item["theme_equity_decomposition"]))

        decomposition_rows = list((decomposition_payload or {}).get("rows", []))
        if decomposition_rows:
            for decomposition_entry in decomposition_rows:
                rows.append(build_candidate_row(source_bundle, structural_parse, graduation, decomposition_entry=decomposition_entry))
            continue

        rows.append(build_candidate_row(source_bundle, structural_parse, graduation))

    output = {
        "method": "promoted structural parses -> auto-generated pick candidates",
        "minimum_status": args.min_status,
        "rows": rows,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
