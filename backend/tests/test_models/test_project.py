"""
项目模型单元测试
"""

import pytest
from datetime import datetime
from app.models.project import Project, ProjectStatus, ProjectManager


class TestProject:
    """测试 Project 数据类"""

    def test_project_creation(self):
        """测试创建 Project 实例"""
        project = Project(
            project_id="test-123",
            name="测试项目",
            status=ProjectStatus.CREATED,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        assert project.project_id == "test-123"
        assert project.name == "测试项目"
        assert project.status == ProjectStatus.CREATED
        assert project.files == []
        assert project.total_text_length == 0
        assert project.chunk_size == 500
        assert project.chunk_overlap == 50

    def test_project_to_dict(self):
        """测试 Project 转换为字典"""
        project = Project(
            project_id="test-123",
            name="测试项目",
            status=ProjectStatus.ONTOLOGY_GENERATED,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T12:00:00",
            files=[{"filename": "test.txt", "path": "/tmp/test.txt", "size": "100"}],
            total_text_length=1000,
            ontology={"entities": [], "relations": []},
            analysis_summary="测试摘要"
        )
        
        data = project.to_dict()
        
        assert data["project_id"] == "test-123"
        assert data["name"] == "测试项目"
        assert data["status"] == "ontology_generated"
        assert data["total_text_length"] == 1000
        assert data["ontology"] == {"entities": [], "relations": []}
        assert data["analysis_summary"] == "测试摘要"

    def test_project_from_dict(self):
        """测试从字典创建 Project"""
        data = {
            "project_id": "test-456",
            "name": "从字典创建",
            "status": "graph_completed",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
            "files": [{"filename": "doc.pdf", "path": "/tmp/doc.pdf"}],
            "graph_id": "graph-789",
            "chunk_size": 1000,
            "chunk_overlap": 100
        }
        
        project = Project.from_dict(data)
        
        assert project.project_id == "test-456"
        assert project.name == "从字典创建"
        assert project.status == ProjectStatus.GRAPH_COMPLETED
        assert project.graph_id == "graph-789"
        assert project.chunk_size == 1000
        assert project.chunk_overlap == 100

    def test_project_from_dict_with_enum_status(self):
        """测试从字典创建时使用枚举状态"""
        data = {
            "project_id": "test-789",
            "name": "枚举状态测试",
            "status": ProjectStatus.FAILED,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "error": "测试错误信息"
        }
        
        project = Project.from_dict(data)
        
        assert project.status == ProjectStatus.FAILED
        assert project.error == "测试错误信息"

    def test_project_default_values(self):
        """测试 Project 默认值"""
        project = Project(
            project_id="test-default",
            name="默认测试",
            status=ProjectStatus.CREATED,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        assert project.ontology is None
        assert project.analysis_summary is None
        assert project.graph_id is None
        assert project.simulation_requirement is None
        assert project.error is None


class TestProjectStatus:
    """测试 ProjectStatus 枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert ProjectStatus.CREATED.value == "created"
        assert ProjectStatus.ONTOLOGY_GENERATED.value == "ontology_generated"
        assert ProjectStatus.GRAPH_BUILDING.value == "graph_building"
        assert ProjectStatus.GRAPH_COMPLETED.value == "graph_completed"
        assert ProjectStatus.FAILED.value == "failed"

    def test_status_comparison(self):
        """测试状态比较"""
        assert ProjectStatus.CREATED == ProjectStatus("created")
        assert ProjectStatus.FAILED != ProjectStatus.CREATED


class TestProjectManager:
    """测试 ProjectManager 类方法"""

    def test_create_and_get_project(self, tmp_path, monkeypatch):
        """测试创建和获取项目"""
        # 使用临时目录作为项目存储
        import app.models.project as project_module
        monkeypatch.setattr(ProjectManager, 'PROJECTS_DIR', str(tmp_path / 'projects'))
        
        # 测试创建项目
        project = ProjectManager.create_project("测试项目")
        assert project is not None
        assert project.name == "测试项目"
        assert project.status == ProjectStatus.CREATED
        
        project_id = project.project_id
        
        # 测试获取项目
        retrieved = ProjectManager.get_project(project_id)
        assert retrieved is not None
        assert retrieved.project_id == project_id
        assert retrieved.name == "测试项目"

    def test_save_and_get_project(self, tmp_path, monkeypatch):
        """测试保存和获取项目"""
        monkeypatch.setattr(ProjectManager, 'PROJECTS_DIR', str(tmp_path / 'projects'))
        
        # 创建项目
        project = ProjectManager.create_project("保存测试")
        project_id = project.project_id
        
        # 修改项目
        project.name = "更新后的名称"
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        
        # 保存
        ProjectManager.save_project(project)
        
        # 重新获取
        updated = ProjectManager.get_project(project_id)
        assert updated.name == "更新后的名称"
        assert updated.status == ProjectStatus.ONTOLOGY_GENERATED

    def test_list_projects(self, tmp_path, monkeypatch):
        """测试列出项目"""
        monkeypatch.setattr(ProjectManager, 'PROJECTS_DIR', str(tmp_path / 'projects'))
        
        # 创建多个项目
        project_ids = []
        for i in range(3):
            project = ProjectManager.create_project(f"项目{i}")
            project_ids.append(project.project_id)
        
        # 列出项目
        projects = ProjectManager.list_projects()
        
        # 验证
        listed_ids = {p.project_id for p in projects}
        for pid in project_ids:
            assert pid in listed_ids

    def test_delete_project(self, tmp_path, monkeypatch):
        """测试删除项目"""
        monkeypatch.setattr(ProjectManager, 'PROJECTS_DIR', str(tmp_path / 'projects'))
        
        # 创建项目
        project = ProjectManager.create_project("待删除")
        project_id = project.project_id
        
        # 验证存在
        assert ProjectManager.get_project(project_id) is not None
        
        # 删除
        result = ProjectManager.delete_project(project_id)
        assert result is True
        
        # 验证已删除
        assert ProjectManager.get_project(project_id) is None

    def test_get_nonexistent_project(self, tmp_path, monkeypatch):
        """测试获取不存在的项目"""
        monkeypatch.setattr(ProjectManager, 'PROJECTS_DIR', str(tmp_path / 'projects'))
        
        project = ProjectManager.get_project("nonexistent-id")
        assert project is None

    def test_delete_nonexistent_project(self, tmp_path, monkeypatch):
        """测试删除不存在的项目"""
        monkeypatch.setattr(ProjectManager, 'PROJECTS_DIR', str(tmp_path / 'projects'))
        
        result = ProjectManager.delete_project("nonexistent-id")
        assert result is False
