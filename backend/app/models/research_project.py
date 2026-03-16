"""
Research project persistence for bottleneck-focused research mode.

This mirrors the existing file-backed project model but stores research-first
artifacts such as thesis intake, claims audit, and scorecards.
"""

import csv
import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config import Config


class ResearchProjectStatus(str, Enum):
    """Lifecycle for research-mode projects."""

    CREATED = "created"
    INTAKE_DEFINED = "intake_defined"
    SOURCES_INGESTED = "sources_ingested"
    STRUCTURE_PARSED = "structure_parsed"
    CLAIMS_AUDITED = "claims_audited"
    SCORED = "scored"
    MISPRICING_SCREENED = "mispricing_screened"
    REPORTED = "reported"
    FAILED = "failed"


@dataclass
class ResearchProject:
    """File-backed research project model."""

    research_project_id: str
    name: str
    status: ResearchProjectStatus
    created_at: str
    updated_at: str
    ontology_name: str
    ontology_version: str
    thesis_intake: Dict[str, Any] = field(default_factory=dict)
    source_count: int = 0
    fragment_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0
    claim_count: int = 0
    evidence_link_count: int = 0
    inference_count: int = 0
    claims_audit_count: int = 0
    scorecard_count: int = 0
    mispricing_candidate_count: int = 0
    source_registry_count: int = 0
    source_acquisition_plan_count: int = 0
    tags: List[str] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)
    source_files: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "research_project_id": self.research_project_id,
            "name": self.name,
            "status": self.status.value
            if isinstance(self.status, ResearchProjectStatus)
            else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ontology_name": self.ontology_name,
            "ontology_version": self.ontology_version,
            "thesis_intake": self.thesis_intake,
            "source_count": self.source_count,
            "fragment_count": self.fragment_count,
            "entity_count": self.entity_count,
            "relationship_count": self.relationship_count,
            "claim_count": self.claim_count,
            "evidence_link_count": self.evidence_link_count,
            "inference_count": self.inference_count,
            "claims_audit_count": self.claims_audit_count,
            "scorecard_count": self.scorecard_count,
            "mispricing_candidate_count": self.mispricing_candidate_count,
            "source_registry_count": self.source_registry_count,
            "source_acquisition_plan_count": self.source_acquisition_plan_count,
            "tags": self.tags,
            "focus_areas": self.focus_areas,
            "source_files": self.source_files,
            "notes": self.notes,
            "summary": self.summary,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchProject":
        status = data.get("status", ResearchProjectStatus.CREATED.value)
        if isinstance(status, str):
            status = ResearchProjectStatus(status)

        return cls(
            research_project_id=data["research_project_id"],
            name=data.get("name", "Unnamed Research Project"),
            status=status,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            ontology_name=data.get("ontology_name", "bottleneck_research"),
            ontology_version=data.get("ontology_version", "v1"),
            thesis_intake=data.get("thesis_intake", {}),
            source_count=data.get("source_count", 0),
            fragment_count=data.get("fragment_count", 0),
            entity_count=data.get("entity_count", 0),
            relationship_count=data.get("relationship_count", 0),
            claim_count=data.get("claim_count", 0),
            evidence_link_count=data.get("evidence_link_count", 0),
            inference_count=data.get("inference_count", 0),
            claims_audit_count=data.get("claims_audit_count", 0),
            scorecard_count=data.get("scorecard_count", 0),
            mispricing_candidate_count=data.get("mispricing_candidate_count", 0),
            source_registry_count=data.get("source_registry_count", 0),
            source_acquisition_plan_count=data.get("source_acquisition_plan_count", 0),
            tags=data.get("tags", []),
            focus_areas=data.get("focus_areas", []),
            source_files=data.get("source_files", []),
            notes=data.get("notes", []),
            summary=data.get("summary", {}),
            error=data.get("error"),
        )


class ResearchProjectManager:
    """Persistence manager for research-mode projects."""

    RESEARCH_PROJECTS_DIR = os.path.join(Config.UPLOAD_FOLDER, "research_projects")

    @classmethod
    def _ensure_root_dir(cls) -> None:
        os.makedirs(cls.RESEARCH_PROJECTS_DIR, exist_ok=True)

    @classmethod
    def _get_project_dir(cls, research_project_id: str) -> str:
        return os.path.join(cls.RESEARCH_PROJECTS_DIR, research_project_id)

    @classmethod
    def _get_meta_path(cls, research_project_id: str) -> str:
        return os.path.join(cls._get_project_dir(research_project_id), "research_project.json")

    @classmethod
    def _get_artifacts_dir(cls, research_project_id: str) -> str:
        return os.path.join(cls._get_project_dir(research_project_id), "artifacts")

    @classmethod
    def _get_files_dir(cls, research_project_id: str) -> str:
        return os.path.join(cls._get_project_dir(research_project_id), "files")

    @classmethod
    def _get_artifact_path(cls, research_project_id: str, filename: str) -> str:
        return os.path.join(cls._get_artifacts_dir(research_project_id), filename)

    @staticmethod
    def _count_items(payload: Any, key: str) -> int:
        value = payload.get(key, []) if isinstance(payload, dict) else []
        return len(value) if isinstance(value, list) else 0

    @classmethod
    def create_project(
        cls,
        name: str = "Unnamed Research Project",
        ontology_name: str = "bottleneck_research",
        ontology_version: str = "v1",
        thesis_intake: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> ResearchProject:
        cls._ensure_root_dir()

        research_project_id = f"rproj_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        intake = thesis_intake or {}

        project = ResearchProject(
            research_project_id=research_project_id,
            name=name,
            status=(
                ResearchProjectStatus.INTAKE_DEFINED
                if intake
                else ResearchProjectStatus.CREATED
            ),
            created_at=now,
            updated_at=now,
            ontology_name=ontology_name,
            ontology_version=ontology_version,
            thesis_intake=intake,
            tags=tags or [],
            focus_areas=focus_areas or [],
        )

        os.makedirs(cls._get_project_dir(research_project_id), exist_ok=True)
        os.makedirs(cls._get_artifacts_dir(research_project_id), exist_ok=True)
        os.makedirs(cls._get_files_dir(research_project_id), exist_ok=True)

        cls.save_project(project)
        if intake:
            cls.save_thesis_intake(research_project_id, intake)

        return project

    @classmethod
    def save_project(cls, project: ResearchProject) -> None:
        project.updated_at = datetime.now().isoformat()
        with open(cls._get_meta_path(project.research_project_id), "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_project(cls, research_project_id: str) -> Optional[ResearchProject]:
        meta_path = cls._get_meta_path(research_project_id)
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, "r", encoding="utf-8") as f:
            return ResearchProject.from_dict(json.load(f))

    @classmethod
    def list_projects(cls, limit: int = 50) -> List[ResearchProject]:
        cls._ensure_root_dir()
        projects: List[ResearchProject] = []
        for research_project_id in os.listdir(cls.RESEARCH_PROJECTS_DIR):
            project = cls.get_project(research_project_id)
            if project:
                projects.append(project)

        projects.sort(key=lambda p: p.created_at, reverse=True)
        return projects[:limit]

    @classmethod
    def delete_project(cls, research_project_id: str) -> bool:
        project_dir = cls._get_project_dir(research_project_id)
        if not os.path.exists(project_dir):
            return False
        shutil.rmtree(project_dir)
        return True

    @classmethod
    def save_thesis_intake(
        cls, research_project_id: str, thesis_intake: Dict[str, Any]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        project.thesis_intake = thesis_intake
        if thesis_intake and project.status == ResearchProjectStatus.CREATED:
            project.status = ResearchProjectStatus.INTAKE_DEFINED

        with open(
            cls._get_artifact_path(research_project_id, "thesis_intake.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(thesis_intake, f, ensure_ascii=False, indent=2)

        cls.save_project(project)
        return project

    @classmethod
    def get_thesis_intake(cls, research_project_id: str) -> Optional[Dict[str, Any]]:
        path = cls._get_artifact_path(research_project_id, "thesis_intake.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_source_bundle(
        cls, research_project_id: str, source_bundle: Dict[str, Any]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "source_bundle.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(source_bundle, f, ensure_ascii=False, indent=2)

        project.source_count = cls._count_items(source_bundle, "sources")
        project.fragment_count = cls._count_items(source_bundle, "fragments")
        if project.source_count or project.fragment_count:
            project.status = ResearchProjectStatus.SOURCES_INGESTED
        cls.save_project(project)
        return project

    @classmethod
    def get_source_bundle(cls, research_project_id: str) -> Dict[str, Any]:
        path = cls._get_artifact_path(research_project_id, "source_bundle.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_structural_parse(
        cls, research_project_id: str, structural_parse: Dict[str, Any]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "structural_parse.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(structural_parse, f, ensure_ascii=False, indent=2)

        project.entity_count = cls._count_items(structural_parse, "entities")
        project.relationship_count = cls._count_items(structural_parse, "relationships")
        project.claim_count = cls._count_items(structural_parse, "claims")
        project.evidence_link_count = cls._count_items(structural_parse, "evidence_links")
        project.inference_count = cls._count_items(structural_parse, "inferences")
        if (
            project.entity_count
            or project.relationship_count
            or project.claim_count
            or project.evidence_link_count
            or project.inference_count
        ):
            project.status = ResearchProjectStatus.STRUCTURE_PARSED
        cls.save_project(project)
        return project

    @classmethod
    def get_structural_parse(cls, research_project_id: str) -> Dict[str, Any]:
        path = cls._get_artifact_path(research_project_id, "structural_parse.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_claims_audit(
        cls, research_project_id: str, claims_audit_rows: List[Dict[str, Any]]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        json_path = cls._get_artifact_path(research_project_id, "claims_audit.json")
        csv_path = cls._get_artifact_path(research_project_id, "claims_audit.csv")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(claims_audit_rows, f, ensure_ascii=False, indent=2)

        fieldnames: List[str] = []
        for row in claims_audit_rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(claims_audit_rows)
            else:
                f.write("")

        project.claims_audit_count = len(claims_audit_rows)
        if claims_audit_rows:
            project.status = ResearchProjectStatus.CLAIMS_AUDITED
        cls.save_project(project)
        return project

    @classmethod
    def get_claims_audit(cls, research_project_id: str) -> List[Dict[str, Any]]:
        path = cls._get_artifact_path(research_project_id, "claims_audit.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_scorecards(
        cls, research_project_id: str, scorecards: List[Dict[str, Any]]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "scorecards.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(scorecards, f, ensure_ascii=False, indent=2)

        project.scorecard_count = len(scorecards)
        if scorecards:
            project.status = ResearchProjectStatus.SCORED
        cls.save_project(project)
        return project

    @classmethod
    def get_scorecards(cls, research_project_id: str) -> List[Dict[str, Any]]:
        path = cls._get_artifact_path(research_project_id, "scorecards.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_summary(
        cls, research_project_id: str, summary: Dict[str, Any]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "summary.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        project.summary = summary
        if summary:
            project.status = ResearchProjectStatus.REPORTED
        cls.save_project(project)
        return project

    @classmethod
    def save_source_registry(
        cls, research_project_id: str, source_registry: Dict[str, Any]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "source_registry.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(source_registry, f, ensure_ascii=False, indent=2)

        project.source_registry_count = cls._count_items(source_registry, "rows")
        cls.save_project(project)
        return project

    @classmethod
    def get_source_registry(cls, research_project_id: str) -> Dict[str, Any]:
        path = cls._get_artifact_path(research_project_id, "source_registry.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_source_acquisition_plan(
        cls, research_project_id: str, source_acquisition_plan: Dict[str, Any]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "source_acquisition_plan.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(source_acquisition_plan, f, ensure_ascii=False, indent=2)

        top_recommendations = cls._count_items(source_acquisition_plan, "top_recommendations")
        monitoring_queue = cls._count_items(source_acquisition_plan, "monitoring_queue")
        project.source_acquisition_plan_count = top_recommendations + monitoring_queue
        cls.save_project(project)
        return project

    @classmethod
    def get_source_acquisition_plan(cls, research_project_id: str) -> Dict[str, Any]:
        path = cls._get_artifact_path(research_project_id, "source_acquisition_plan.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_mispricing_candidates(
        cls, research_project_id: str, mispricing_candidates: List[Dict[str, Any]]
    ) -> ResearchProject:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        with open(
            cls._get_artifact_path(research_project_id, "mispricing_candidates.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(mispricing_candidates, f, ensure_ascii=False, indent=2)

        project.mispricing_candidate_count = len(mispricing_candidates)
        if mispricing_candidates:
            project.status = ResearchProjectStatus.MISPRICING_SCREENED
        cls.save_project(project)
        return project

    @classmethod
    def get_mispricing_candidates(cls, research_project_id: str) -> List[Dict[str, Any]]:
        path = cls._get_artifact_path(research_project_id, "mispricing_candidates.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_summary(cls, research_project_id: str) -> Dict[str, Any]:
        path = cls._get_artifact_path(research_project_id, "summary.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_artifacts(cls, research_project_id: str) -> Dict[str, Any]:
        project = cls.get_project(research_project_id)
        if not project:
            raise ValueError(f"research project not found: {research_project_id}")

        return {
            "research_project": project.to_dict(),
            "thesis_intake": cls.get_thesis_intake(research_project_id) or {},
            "source_bundle": cls.get_source_bundle(research_project_id),
            "structural_parse": cls.get_structural_parse(research_project_id),
            "claims_audit": cls.get_claims_audit(research_project_id),
            "scorecards": cls.get_scorecards(research_project_id),
            "mispricing_candidates": cls.get_mispricing_candidates(research_project_id),
            "source_registry": cls.get_source_registry(research_project_id),
            "source_acquisition_plan": cls.get_source_acquisition_plan(research_project_id),
            "summary": cls.get_summary(research_project_id),
        }
