"""
Live Federal Register feed retrieval and normalization.

This service fetches recent document metadata from the Federal Register API and
normalizes the result into the `policy_feed` contract consumed by the policy
feed connector.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FEDERAL_REGISTER_API_URL = "https://www.federalregister.gov/api/v1/documents.json"
DEFAULT_FIELDS = [
    "abstract",
    "agencies",
    "document_number",
    "excerpts",
    "html_url",
    "publication_date",
    "title",
    "topics",
    "type",
]


def _normalize_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_federal_register_documents_url(
    *,
    query: str = "",
    agencies: Iterable[str] | None = None,
    document_types: Iterable[str] | None = None,
    published_gte: str | None = None,
    published_lte: str | None = None,
    per_page: int = 20,
    page: int = 1,
    order: str = "newest",
    fields: Iterable[str] | None = None,
) -> str:
    params: List[tuple[str, str]] = []
    selected_fields = list(fields or DEFAULT_FIELDS)
    for field in selected_fields:
        params.append(("fields[]", field))
    if query:
        params.append(("conditions[term]", query))
    for agency in _normalize_list(agencies):
        params.append(("conditions[agencies][]", str(agency)))
    for doc_type in _normalize_list(document_types):
        params.append(("conditions[type][]", str(doc_type)))
    if published_gte:
        params.append(("conditions[publication_date][gte]", published_gte))
    if published_lte:
        params.append(("conditions[publication_date][lte]", published_lte))
    params.append(("per_page", str(per_page)))
    params.append(("page", str(page)))
    params.append(("order", order))
    return f"{FEDERAL_REGISTER_API_URL}?{urlencode(params, doseq=True)}"


def _fetch_json(url: str, *, timeout_seconds: int = 20) -> Dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "MiroFish FederalRegisterConnector/1.0",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("results"), list):
        return payload["results"]
    if isinstance(payload.get("documents"), list):
        return payload["documents"]
    return []


def _agency_names(document: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for agency in _normalize_list(document.get("agencies")):
        if isinstance(agency, dict):
            name = agency.get("name") or agency.get("raw_name")
            if name:
                names.append(str(name))
        elif agency:
            names.append(str(agency))
    return names


def _normalize_document_to_policy_feed(
    document: Dict[str, Any],
    *,
    source_target_id: str,
    target_themes: Iterable[str],
    focus_process_layers: Iterable[str],
    focus_geographies: Iterable[str],
    ticker_refs: Iterable[str],
    policy_scope: Iterable[str],
) -> Dict[str, Any]:
    title = document.get("title") or "Untitled Federal Register document"
    document_number = str(document.get("document_number") or title)
    event_name = title
    process_layers = [str(value) for value in _normalize_list(focus_process_layers)]
    geographies = [str(value) for value in _normalize_list(focus_geographies)]
    themes = [str(value) for value in _normalize_list(target_themes)]
    agencies = _agency_names(document)

    relationship_hints: List[Dict[str, Any]] = []
    for process_layer in process_layers:
        relationship_hints.append(
            {
                "key": f"{document_number}_affected_{process_layer}",
                "relationship_type": "AFFECTED_BY_EVENT",
                "source_type": "ProcessLayer",
                "source_name": process_layer,
                "target_type": "Event",
                "target_name": event_name,
                "relationship_strength": "high",
                "confidence": "medium",
            }
        )
        for geography in geographies:
            relationship_hints.append(
                {
                    "key": f"{document_number}_constrained_{process_layer}_{geography}",
                    "relationship_type": "CONSTRAINED_BY",
                    "source_type": "ProcessLayer",
                    "source_name": process_layer,
                    "target_type": "Geography",
                    "target_name": geography,
                    "relationship_strength": "medium",
                    "confidence": "medium",
                }
            )

    entity_hints: List[Dict[str, Any]] = [
        {
            "entity_type": "Event",
            "canonical_name": event_name,
            "attributes": {
                "event_type": "policy_notice",
                "document_number": document.get("document_number"),
                "document_type": document.get("type"),
                "agencies": agencies,
            },
            "confidence": "high",
        }
    ]
    entity_hints.extend(
        {
            "entity_type": "ProcessLayer",
            "canonical_name": process_layer,
            "attributes": {"process_stage": "policy_affected"},
            "confidence": "medium",
        }
        for process_layer in process_layers
    )
    entity_hints.extend(
        {
            "entity_type": "Geography",
            "canonical_name": geography,
            "confidence": "medium",
        }
        for geography in geographies
    )
    entity_hints.extend(
        {
            "entity_type": "Theme",
            "canonical_name": theme.replace("_", " ").title(),
            "confidence": "medium",
        }
        for theme in themes
    )

    abstract = document.get("abstract") or ""
    excerpts = " ".join(str(value) for value in _normalize_list(document.get("excerpts")))
    summary = abstract or excerpts or title
    claim_candidates = []
    if process_layers:
        claim_candidates.append(
            {
                "claim_key": f"claim_{document_number}_policy_notice_affects_process_layers",
                "claim_type": "policy_transmission_assertion",
                "claim_text": (
                    f"{title} may affect {', '.join(process_layers)} before downstream market narratives update."
                ),
                "claim_status": "supported",
                "claim_kind": "inferential",
                "confidence": "medium",
                "entity_names": [event_name, *process_layers, *geographies],
                "relationship_keys": [relationship["key"] for relationship in relationship_hints],
            }
        )

    return {
        "document_id": f"federal_register_{document_number}",
        "source_target_id": source_target_id,
        "source_target_name": "Federal Register Notices",
        "source_class": "government_policy_enforcement",
        "publisher": "Federal Register",
        "title": title,
        "canonical_url": document.get("html_url") or FEDERAL_REGISTER_API_URL,
        "published_at": document.get("publication_date", ""),
        "retrieved_at": _iso_now(),
        "source_quality": "high",
        "source_reliability_score": 0.95,
        "usage_mode": "evidence",
        "attachment_type": "html",
        "jurisdiction": "US",
        "language": "en",
        "ticker_refs": [str(value).upper() for value in _normalize_list(ticker_refs)],
        "theme_refs": themes,
        "policy_scope": [str(value) for value in _normalize_list(policy_scope)],
        "summary": summary,
        "excerpt": excerpts or abstract or title,
        "research_tags": {
            "themes": [theme.replace("_", " ").title() for theme in themes],
            "process_layers": process_layers,
            "geographies": geographies,
        },
        "entity_hints": entity_hints,
        "relationship_hints": relationship_hints,
        "claim_candidates": claim_candidates,
        "notes": [
            "Normalized from live Federal Register API response.",
            *([f"Agencies: {', '.join(agencies)}"] if agencies else []),
        ],
    }


def fetch_federal_register_policy_feed(
    *,
    query: str = "",
    agencies: Iterable[str] | None = None,
    document_types: Iterable[str] | None = None,
    published_gte: str | None = None,
    published_lte: str | None = None,
    per_page: int = 20,
    page: int = 1,
    target_themes: Iterable[str] | None = None,
    focus_process_layers: Iterable[str] | None = None,
    focus_geographies: Iterable[str] | None = None,
    ticker_refs: Iterable[str] | None = None,
    policy_scope: Iterable[str] | None = None,
) -> Dict[str, Any]:
    url = build_federal_register_documents_url(
        query=query,
        agencies=agencies,
        document_types=document_types,
        published_gte=published_gte,
        published_lte=published_lte,
        per_page=per_page,
        page=page,
    )
    payload = _fetch_json(url)
    results = _extract_results(payload)
    documents = [
        _normalize_document_to_policy_feed(
            result,
            source_target_id="src_target_federal_register_notices",
            target_themes=target_themes or [],
            focus_process_layers=focus_process_layers or [],
            focus_geographies=focus_geographies or [],
            ticker_refs=ticker_refs or [],
            policy_scope=policy_scope or [],
        )
        for result in results
    ]
    return {
        "name": "federal_register_policy_feed_live_v1",
        "theme": next(iter(target_themes or []), ""),
        "synthetic_sample": False,
        "notes": [
            "Fetched from Federal Register API.",
            *( [f"Query: {query}"] if query else [] ),
        ],
        "feed_documents": documents,
        "fetch_metadata": {
            "api_url": url,
            "result_count": len(results),
            "retrieved_at": _iso_now(),
            "agencies": list(_normalize_list(agencies)),
            "document_types": list(_normalize_list(document_types)),
        },
    }

