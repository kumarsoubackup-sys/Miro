"""
图谱 API 单元测试
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO


class TestGraphAPI:
    """测试图谱相关 API"""

    def test_allowed_file_function(self):
        """测试允许的文件检查函数"""
        from app.api.graph import allowed_file
        
        assert allowed_file("test.txt") == True
        assert allowed_file("test.md") == True
        assert allowed_file("test.pdf") == True
        assert allowed_file("test.markdown") == True
        assert allowed_file("test.doc") == False
        assert allowed_file("test") == False
        assert allowed_file("") == False


class TestGraphAPIProject:
    """测试项目管理 API"""

    def test_get_project_success(self, client):
        """测试获取项目成功"""
        with patch('app.api.graph.ProjectManager') as mock_manager:
            mock_project = Mock()
            mock_project.to_dict.return_value = {
                "project_id": "test-123",
                "name": "测试项目"
            }
            mock_manager.get_project.return_value = mock_project
            
            response = client.get('/api/graph/project/test-123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert data["data"]["project_id"] == "test-123"

    def test_get_project_not_found(self, client):
        """测试获取不存在的项目"""
        with patch('app.api.graph.ProjectManager') as mock_manager:
            mock_manager.get_project.return_value = None
            
            response = client.get('/api/graph/project/nonexistent')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["success"] == False

    def test_list_projects(self, client):
        """测试列出项目"""
        with patch('app.api.graph.ProjectManager') as mock_manager:
            mock_project1 = Mock()
            mock_project1.to_dict.return_value = {"project_id": "p1", "name": "项目1"}
            mock_project2 = Mock()
            mock_project2.to_dict.return_value = {"project_id": "p2", "name": "项目2"}
            mock_manager.list_projects.return_value = [mock_project1, mock_project2]
            
            response = client.get('/api/graph/project/list')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert len(data["data"]) == 2
            assert data["count"] == 2

    def test_delete_project_success(self, client):
        """测试删除项目成功"""
        with patch('app.api.graph.ProjectManager') as mock_manager:
            mock_manager.delete_project.return_value = True
            
            response = client.delete('/api/graph/project/test-123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True

    def test_delete_project_not_found(self, client):
        """测试删除不存在的项目"""
        with patch('app.api.graph.ProjectManager') as mock_manager:
            mock_manager.delete_project.return_value = False
            
            response = client.delete('/api/graph/project/nonexistent')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["success"] == False


class TestGraphAPITask:
    """测试任务相关 API"""

    def test_get_task_status_success(self, client):
        """测试获取任务状态成功"""
        # 需要 patch TaskManager 类本身，因为它在函数内实例化
        with patch('app.api.graph.TaskManager') as mock_manager_class:
            from app.models.task import Task, TaskStatus
            from datetime import datetime
            
            mock_task = Task(
                task_id="task-123",
                task_type="graph_build",
                status=TaskStatus.PROCESSING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                progress=50
            )
            
            mock_instance = Mock()
            mock_instance.get_task.return_value = mock_task
            mock_manager_class.return_value = mock_instance
            
            response = client.get('/api/graph/task/task-123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert data["data"]["task_id"] == "task-123"

    def test_get_task_status_not_found(self, client):
        """测试获取不存在的任务"""
        with patch('app.api.graph.TaskManager') as mock_manager_class:
            mock_instance = Mock()
            mock_instance.get_task.return_value = None
            mock_manager_class.return_value = mock_instance
            
            response = client.get('/api/graph/task/nonexistent')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["success"] == False


class TestGraphAPIHealth:
    """测试健康检查 API"""

    def test_api_endpoints_exist(self, client):
        """测试 API 端点存在"""
        # 测试一些已知的端点
        endpoints = [
            '/api/graph/project/list',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # 只要返回不是 404，说明端点存在
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
