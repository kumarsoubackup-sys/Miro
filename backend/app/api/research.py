"""
Research-mode API routes.

These endpoints define the first stable backend surface for bottleneck-focused
research projects, without changing the existing simulation flow.
"""

import traceback
from pathlib import Path

from flask import jsonify, request

from . import research_bp
from ..models.research_project import ResearchProjectManager
from ..services import (
    MispricingCandidate,
    MispricingSignals,
    OptionsExpressionSignals,
    fetch_federal_register_policy_feed,
    build_policy_feed_source_bundle,
    build_source_acquisition_plan,
    build_research_ontology_spec,
    build_source_registry_from_docs,
    build_structural_parse_from_source_bundle,
    list_query_profiles,
    screen_candidates,
)
from ..utils.logger import get_logger

logger = get_logger("mirofish.api.research")


@research_bp.route("/ontology", methods=["GET"])
def get_research_ontology():
    """Return the canonical research ontology specification."""
    return jsonify({
        "success": True,
        "data": build_research_ontology_spec(),
    })


@research_bp.route("/project", methods=["POST"])
def create_research_project():
    """Create a research-mode project."""
    try:
        data = request.get_json() or {}
        project = ResearchProjectManager.create_project(
            name=data.get("name", "Unnamed Research Project"),
            ontology_name=data.get("ontology_name", "bottleneck_research"),
            ontology_version=data.get("ontology_version", "v1"),
            thesis_intake=data.get("thesis_intake"),
            tags=data.get("tags"),
            focus_areas=data.get("focus_areas"),
        )

        return jsonify({
            "success": True,
            "data": project.to_dict(),
        }), 201
    except Exception as e:
        logger.error(f"创建研究项目失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/list", methods=["GET"])
def list_research_projects():
    """List research-mode projects."""
    limit = request.args.get("limit", 50, type=int)
    projects = ResearchProjectManager.list_projects(limit=limit)
    return jsonify({
        "success": True,
        "data": [project.to_dict() for project in projects],
        "count": len(projects),
    })


@research_bp.route("/project/<research_project_id>", methods=["GET"])
def get_research_project(research_project_id: str):
    """Fetch a single research project."""
    project = ResearchProjectManager.get_project(research_project_id)
    if not project:
        return jsonify({
            "success": False,
            "error": f"研究项目不存在: {research_project_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict(),
    })


@research_bp.route("/project/<research_project_id>", methods=["DELETE"])
def delete_research_project(research_project_id: str):
    """Delete a research project and its artifacts."""
    success = ResearchProjectManager.delete_project(research_project_id)
    if not success:
        return jsonify({
            "success": False,
            "error": f"研究项目不存在或删除失败: {research_project_id}",
        }), 404

    return jsonify({
        "success": True,
        "message": f"研究项目已删除: {research_project_id}",
    })


@research_bp.route("/project/<research_project_id>/artifacts", methods=["GET"])
def get_research_project_artifacts(research_project_id: str):
    """Return the current persisted artifact bundle."""
    try:
        return jsonify({
            "success": True,
            "data": ResearchProjectManager.get_artifacts(research_project_id),
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404


@research_bp.route("/project/<research_project_id>/thesis-intake", methods=["POST"])
def save_thesis_intake(research_project_id: str):
    """Persist thesis-intake data for a research project."""
    try:
        thesis_intake = request.get_json() or {}
        project = ResearchProjectManager.save_thesis_intake(
            research_project_id, thesis_intake
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "thesis_intake": thesis_intake,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 thesis intake 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/source-bundle", methods=["POST"])
def save_source_bundle(research_project_id: str):
    """Persist normalized source-ingestion artifacts for a research project."""
    try:
        source_bundle = request.get_json() or {}
        if not isinstance(source_bundle, dict):
            return jsonify({
                "success": False,
                "error": "source bundle payload must be an object",
            }), 400

        project = ResearchProjectManager.save_source_bundle(
            research_project_id, source_bundle
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "source_bundle": source_bundle,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 source bundle 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/source-bundle/policy-feed-import", methods=["POST"])
def import_policy_feed_source_bundle(research_project_id: str):
    """Normalize a Federal Register/BIS style feed payload into a source bundle."""
    try:
        payload = request.get_json() or {}
        policy_feed = payload.get("policy_feed")
        if not isinstance(policy_feed, dict):
            return jsonify({
                "success": False,
                "error": "policy_feed must be an object",
            }), 400

        merge_existing = bool(payload.get("merge_existing", True))
        existing_source_bundle = None
        if merge_existing:
            existing_source_bundle = ResearchProjectManager.get_source_bundle(research_project_id)
            if not isinstance(existing_source_bundle, dict):
                existing_source_bundle = None

        source_bundle = build_policy_feed_source_bundle(
            policy_feed,
            existing_source_bundle=existing_source_bundle,
        )
        project = ResearchProjectManager.save_source_bundle(research_project_id, source_bundle)
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "source_bundle": source_bundle,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"导入 policy feed source bundle 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/federal-register/query-profiles", methods=["GET"])
def get_federal_register_query_profiles():
    """List available Federal Register query profiles."""
    return jsonify({
        "success": True,
        "data": list_query_profiles(),
    })


@research_bp.route("/project/<research_project_id>/source-bundle/federal-register-fetch", methods=["POST"])
def fetch_federal_register_into_source_bundle(research_project_id: str):
    """Fetch live Federal Register policy documents and merge them into a source bundle."""
    try:
        payload = request.get_json() or {}
        merge_existing = bool(payload.get("merge_existing", True))
        existing_source_bundle = None
        if merge_existing:
            existing_source_bundle = ResearchProjectManager.get_source_bundle(research_project_id)
            if not isinstance(existing_source_bundle, dict):
                existing_source_bundle = None

        policy_feed = fetch_federal_register_policy_feed(
            query_profile=payload.get("query_profile"),
            query=payload.get("query", ""),
            agencies=payload.get("agencies"),
            document_types=payload.get("document_types"),
            published_gte=payload.get("published_gte"),
            published_lte=payload.get("published_lte"),
            per_page=int(payload.get("per_page", 20)),
            page=int(payload.get("page", 1)),
            target_themes=payload.get("target_themes"),
            focus_process_layers=payload.get("focus_process_layers"),
            focus_geographies=payload.get("focus_geographies"),
            ticker_refs=payload.get("ticker_refs"),
            policy_scope=payload.get("policy_scope"),
        )
        source_bundle = build_policy_feed_source_bundle(
            policy_feed,
            existing_source_bundle=existing_source_bundle,
        )
        project = ResearchProjectManager.save_source_bundle(research_project_id, source_bundle)
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "policy_feed": policy_feed,
                "source_bundle": source_bundle,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"抓取 Federal Register 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/source-registry", methods=["GET"])
def get_source_registry(research_project_id: str):
    """Return the saved source registry for a research project."""
    project = ResearchProjectManager.get_project(research_project_id)
    if not project:
        return jsonify({
            "success": False,
            "error": f"研究项目不存在: {research_project_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": ResearchProjectManager.get_source_registry(research_project_id),
    })


@research_bp.route("/project/<research_project_id>/source-registry", methods=["POST"])
def save_source_registry(research_project_id: str):
    """Persist a structured source registry for a research project."""
    try:
        source_registry = request.get_json() or {}
        if not isinstance(source_registry, dict):
            return jsonify({
                "success": False,
                "error": "source registry payload must be an object",
            }), 400

        project = ResearchProjectManager.save_source_registry(
            research_project_id, source_registry
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "source_registry": source_registry,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 source registry 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/source-registry/import", methods=["POST"])
def import_source_registry(research_project_id: str):
    """Seed a source registry from the current canonical docs."""
    try:
        payload = request.get_json(silent=True) or {}
        matrix_path = payload.get("matrix_path")
        investigation_path = payload.get("investigation_path")
        source_registry = build_source_registry_from_docs(
            investigation_path=Path(investigation_path) if investigation_path else None,
            matrix_path=Path(matrix_path) if matrix_path else None,
        )
        project = ResearchProjectManager.save_source_registry(
            research_project_id, source_registry
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "source_registry": source_registry,
            },
        })
    except FileNotFoundError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"导入 source registry 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/source-acquisition-plan", methods=["GET"])
def get_source_acquisition_plan(research_project_id: str):
    """Return the saved source acquisition plan for a research project."""
    project = ResearchProjectManager.get_project(research_project_id)
    if not project:
        return jsonify({
            "success": False,
            "error": f"研究项目不存在: {research_project_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": ResearchProjectManager.get_source_acquisition_plan(research_project_id),
    })


@research_bp.route("/project/<research_project_id>/source-acquisition-plan", methods=["POST"])
def save_source_acquisition_plan(research_project_id: str):
    """Persist a source acquisition plan for a research project."""
    try:
        source_acquisition_plan = request.get_json() or {}
        if not isinstance(source_acquisition_plan, dict):
            return jsonify({
                "success": False,
                "error": "source acquisition plan payload must be an object",
            }), 400

        project = ResearchProjectManager.save_source_acquisition_plan(
            research_project_id, source_acquisition_plan
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "source_acquisition_plan": source_acquisition_plan,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 source acquisition plan 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route(
    "/project/<research_project_id>/source-acquisition-plan/generate",
    methods=["POST"],
)
def generate_source_acquisition_plan(research_project_id: str):
    """Generate and persist a source acquisition plan for a research project."""
    try:
        payload = request.get_json(silent=True) or {}
        thesis_intake = payload.get("thesis_intake")
        if thesis_intake is None:
            thesis_intake = ResearchProjectManager.get_thesis_intake(research_project_id) or {}

        source_registry = payload.get("source_registry")
        if source_registry is None:
            source_registry = ResearchProjectManager.get_source_registry(research_project_id)
        if not source_registry:
            return jsonify({
                "success": False,
                "error": "no source registry available for source acquisition plan generation",
            }), 400

        source_bundle = payload.get("source_bundle")
        if source_bundle is None:
            source_bundle = ResearchProjectManager.get_source_bundle(research_project_id)

        structural_parse = payload.get("structural_parse")
        if structural_parse is None:
            structural_parse = ResearchProjectManager.get_structural_parse(research_project_id)

        graduation = payload.get("graduation") or {}
        limit = payload.get("limit", 10)

        source_acquisition_plan = build_source_acquisition_plan(
            source_registry,
            thesis_intake=thesis_intake,
            source_bundle=source_bundle,
            structural_parse=structural_parse,
            graduation=graduation,
            limit=limit,
        )
        project = ResearchProjectManager.save_source_acquisition_plan(
            research_project_id, source_acquisition_plan
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "source_acquisition_plan": source_acquisition_plan,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"生成 source acquisition plan 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/structural-parse", methods=["POST"])
def save_structural_parse(research_project_id: str):
    """Persist structural parsing artifacts for a research project."""
    try:
        structural_parse = request.get_json() or {}
        if not isinstance(structural_parse, dict):
            return jsonify({
                "success": False,
                "error": "structural parse payload must be an object",
            }), 400

        project = ResearchProjectManager.save_structural_parse(
            research_project_id, structural_parse
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "structural_parse": structural_parse,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 structural parse 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route(
    "/project/<research_project_id>/structural-parse/generate",
    methods=["POST"],
)
def generate_structural_parse(research_project_id: str):
    """Generate and persist a structural parse from the stored source bundle."""
    try:
        payload = request.get_json(silent=True) or {}
        source_bundle = payload.get("source_bundle")
        if source_bundle is None:
            source_bundle = ResearchProjectManager.get_source_bundle(research_project_id)
        if not source_bundle:
            return jsonify({
                "success": False,
                "error": "no source bundle available for structural parse generation",
            }), 400
        if not isinstance(source_bundle, dict):
            return jsonify({
                "success": False,
                "error": "source bundle payload must be an object",
            }), 400

        structural_parse = build_structural_parse_from_source_bundle(source_bundle)
        project = ResearchProjectManager.save_structural_parse(
            research_project_id, structural_parse
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "structural_parse": structural_parse,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"生成 structural parse 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/claims-audit", methods=["POST"])
def save_claims_audit(research_project_id: str):
    """Persist structured claims-audit rows for a research project."""
    try:
        payload = request.get_json() or {}
        claims_audit = payload.get("rows")
        if claims_audit is None:
            claims_audit = payload if isinstance(payload, list) else []
        if not isinstance(claims_audit, list):
            return jsonify({
                "success": False,
                "error": "claims audit payload must be a list or {\"rows\": [...]}",
            }), 400

        project = ResearchProjectManager.save_claims_audit(
            research_project_id, claims_audit
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "claims_audit_count": len(claims_audit),
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 claims audit 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/scorecards", methods=["POST"])
def save_scorecards(research_project_id: str):
    """Persist scorecard rows for a research project."""
    try:
        payload = request.get_json() or {}
        scorecards = payload.get("rows")
        if scorecards is None:
            scorecards = payload if isinstance(payload, list) else []
        if not isinstance(scorecards, list):
            return jsonify({
                "success": False,
                "error": "scorecards payload must be a list or {\"rows\": [...]}",
            }), 400

        project = ResearchProjectManager.save_scorecards(
            research_project_id, scorecards
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "scorecard_count": len(scorecards),
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 scorecards 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/summary", methods=["POST"])
def save_summary(research_project_id: str):
    """Persist summary/report metadata for a research project."""
    try:
        summary = request.get_json() or {}
        project = ResearchProjectManager.save_summary(research_project_id, summary)
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "summary": summary,
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 summary 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route("/project/<research_project_id>/mispricing-candidates", methods=["POST"])
def save_mispricing_candidates(research_project_id: str):
    """Persist already-scored or externally prepared mispricing candidates."""
    try:
        payload = request.get_json() or {}
        candidates = payload.get("rows")
        if candidates is None:
            candidates = payload if isinstance(payload, list) else []
        if not isinstance(candidates, list):
            return jsonify({
                "success": False,
                "error": "mispricing candidates payload must be a list or {\"rows\": [...]}",
            }), 400

        project = ResearchProjectManager.save_mispricing_candidates(
            research_project_id, candidates
        )
        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "mispricing_candidate_count": len(candidates),
            },
        })
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"保存 mispricing candidates 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@research_bp.route(
    "/project/<research_project_id>/mispricing-candidates/screen",
    methods=["POST"],
)
def screen_mispricing_candidates(research_project_id: str):
    """Score structured mispricing candidates and persist the results."""
    try:
        payload = request.get_json() or {}
        rows = payload.get("rows")
        if rows is None:
            rows = payload if isinstance(payload, list) else []
        if not isinstance(rows, list):
            return jsonify({
                "success": False,
                "error": "screen payload must be a list or {\"rows\": [...]}",
            }), 400

        candidates = []
        for row in rows:
            candidates.append(
                MispricingCandidate(
                    name=row["name"],
                    thesis=row["thesis"],
                    underlying=row["underlying"],
                    mispricing_type=row["mispricing_type"],
                    posture=row["posture"],
                    preferred_expression=row["preferred_expression"],
                    time_horizon=row["time_horizon"],
                    mispricing_signals=MispricingSignals(**row["mispricing_signals"]),
                    options_expression_signals=OptionsExpressionSignals(
                        **row["options_expression_signals"]
                    ),
                    linked_companies=row.get("linked_companies", []),
                    catalysts=row.get("catalysts", []),
                    invalidations=row.get("invalidations", []),
                    structural_reference=row.get("structural_reference", {}),
                    notes=row.get("notes", []),
                )
            )

        results = [scorecard.to_dict() for scorecard in screen_candidates(candidates)]
        project = ResearchProjectManager.save_mispricing_candidates(
            research_project_id, results
        )

        return jsonify({
            "success": True,
            "data": {
                "research_project": project.to_dict(),
                "rows": results,
                "mispricing_candidate_count": len(results),
            },
        })
    except KeyError as e:
        return jsonify({
            "success": False,
            "error": f"missing required field: {str(e)}",
        }), 400
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 404
    except Exception as e:
        logger.error(f"筛选 mispricing candidates 失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500
