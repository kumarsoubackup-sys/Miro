import json
from pathlib import Path

from app.models.research_project import (
    ResearchProjectManager,
    ResearchProjectStatus,
)


def test_research_project_manager_round_trip(tmp_path):
    original_dir = ResearchProjectManager.RESEARCH_PROJECTS_DIR
    ResearchProjectManager.RESEARCH_PROJECTS_DIR = str(tmp_path / "research_projects")
    try:
        project = ResearchProjectManager.create_project(
            name="HBM Research",
            thesis_intake={"theme": "HBM / advanced packaging"},
            tags=["ai", "memory"],
            focus_areas=["packaging", "hbm"],
        )

        assert project.status == ResearchProjectStatus.INTAKE_DEFINED

        ResearchProjectManager.save_source_bundle(
            project.research_project_id,
            {
                "sources": [
                    {
                        "source_id": "src_1",
                        "source_class": "company_filing",
                        "usage_mode": "evidence",
                    }
                ],
                "fragments": [
                    {
                        "fragment_id": "frag_1",
                        "source_id": "src_1",
                        "excerpt": "CoWoS capacity remains constrained.",
                    }
                ],
            },
        )
        ResearchProjectManager.save_structural_parse(
            project.research_project_id,
            {
                "entities": [
                    {
                        "entity_id": "ent_1",
                        "entity_type": "ProcessLayer",
                        "canonical_name": "CoWoS packaging",
                    }
                ],
                "relationships": [
                    {
                        "relationship_id": "rel_1",
                        "relationship_type": "DEPENDS_ON",
                    }
                ],
                "claims": [
                    {
                        "claim_id": "claim_1",
                        "claim_type": "bottleneck_assertion",
                    }
                ],
                "evidence_links": [
                    {
                        "evidence_link_id": "ev_1",
                        "fragment_id": "frag_1",
                        "supports_object_type": "claim",
                        "supports_object_id": "claim_1",
                    }
                ],
                "inferences": [
                    {
                        "inference_id": "inf_1",
                        "inference_type": "dependency_bridge",
                    }
                ],
            },
        )
        ResearchProjectManager.save_claims_audit(
            project.research_project_id,
            [{"claim_text": "CoWoS is constrained", "status": "supported"}],
        )
        ResearchProjectManager.save_scorecards(
            project.research_project_id,
            [{"candidate_name": "CoWoS", "severity": {"score_0_to_100": 90.8}}],
        )
        ResearchProjectManager.save_source_registry(
            project.research_project_id,
            {
                "rows": [
                    {
                        "source_target_id": "src_target_sec_edgar",
                        "name": "SEC EDGAR",
                        "source_class": "company_filing",
                    }
                ]
            },
        )
        ResearchProjectManager.save_source_acquisition_plan(
            project.research_project_id,
            {
                "top_recommendations": [
                    {
                        "source_target_id": "src_target_sec_edgar",
                        "recommendation": "ingest_now",
                    }
                ],
                "monitoring_queue": [
                    {
                        "source_target_id": "src_target_bis",
                        "recommendation": "monitor_event_driven",
                    }
                ],
            },
        )
        ResearchProjectManager.save_mispricing_candidates(
            project.research_project_id,
            [{"candidate_name": "MU LEAPS", "mispricing": {"score_0_to_100": 82.4}}],
        )
        ResearchProjectManager.save_summary(
            project.research_project_id,
            {"top_severity_layer": "CoWoS-class packaging"},
        )

        loaded = ResearchProjectManager.get_project(project.research_project_id)
        artifacts = ResearchProjectManager.get_artifacts(project.research_project_id)

        assert loaded is not None
        assert loaded.status == ResearchProjectStatus.REPORTED
        assert loaded.source_count == 1
        assert loaded.fragment_count == 1
        assert loaded.entity_count == 1
        assert loaded.relationship_count == 1
        assert loaded.claim_count == 1
        assert loaded.evidence_link_count == 1
        assert loaded.inference_count == 1
        assert loaded.claims_audit_count == 1
        assert loaded.scorecard_count == 1
        assert loaded.source_registry_count == 1
        assert loaded.source_acquisition_plan_count == 2
        assert loaded.mispricing_candidate_count == 1
        assert artifacts["thesis_intake"]["theme"] == "HBM / advanced packaging"
        assert artifacts["source_bundle"]["sources"][0]["source_id"] == "src_1"
        assert artifacts["structural_parse"]["claims"][0]["claim_id"] == "claim_1"
        assert artifacts["source_registry"]["rows"][0]["source_target_id"] == "src_target_sec_edgar"
        assert (
            artifacts["source_acquisition_plan"]["top_recommendations"][0]["source_target_id"]
            == "src_target_sec_edgar"
        )
        assert artifacts["mispricing_candidates"][0]["candidate_name"] == "MU LEAPS"
        assert artifacts["summary"]["top_severity_layer"] == "CoWoS-class packaging"

        csv_path = (
            Path(ResearchProjectManager.RESEARCH_PROJECTS_DIR)
            / project.research_project_id
            / "artifacts"
            / "claims_audit.csv"
        )
        assert csv_path.exists()
        assert "claim_text" in csv_path.read_text(encoding="utf-8")

        meta_path = (
            Path(ResearchProjectManager.RESEARCH_PROJECTS_DIR)
            / project.research_project_id
            / "research_project.json"
        )
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["ontology_name"] == "bottleneck_research"
    finally:
        ResearchProjectManager.RESEARCH_PROJECTS_DIR = original_dir
