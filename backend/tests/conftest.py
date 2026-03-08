"""
Pytest 配置文件
提供测试所需的 fixtures 和配置
"""

import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('LLM_API_KEY', 'test-api-key')
os.environ.setdefault('ZEP_API_KEY', 'test-zep-key')
os.environ.setdefault('FLASK_DEBUG', 'false')


@pytest.fixture
def app():
    """创建 Flask 应用实例"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试 runner"""
    return app.test_cli_runner()


@pytest.fixture
def temp_upload_dir(tmp_path):
    """创建临时上传目录"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture
def sample_text_file(tmp_path):
    """创建示例文本文件"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("这是一个测试文件。\n包含多行内容。", encoding='utf-8')
    return file_path


@pytest.fixture
def sample_md_file(tmp_path):
    """创建示例 Markdown 文件"""
    file_path = tmp_path / "test.md"
    content = """# 测试文档

这是一个测试 Markdown 文件。

## 章节 1

一些内容在这里。

## 章节 2

更多内容。
"""
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def mock_project_data():
    """提供示例项目数据"""
    return {
        "project_id": "test-project-123",
        "name": "测试项目",
        "status": "created",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "files": [],
        "total_text_length": 0,
        "ontology": None,
        "analysis_summary": None,
        "graph_id": None,
        "graph_build_task_id": None,
        "simulation_requirement": None,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "error": None
    }


@pytest.fixture
def mock_task_data():
    """提供示例任务数据"""
    return {
        "task_id": "test-task-456",
        "task_type": "graph_build",
        "status": "pending",
        "progress": 0,
        "message": "等待中",
        "result": None,
        "error": None,
        "metadata": {}
    }
