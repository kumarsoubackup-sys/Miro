"""
任务模型单元测试
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from app.models.task import Task, TaskStatus, TaskManager


class TestTask:
    """测试 Task 数据类"""

    def test_task_creation(self):
        """测试创建 Task 实例"""
        now = datetime.now()
        task = Task(
            task_id="task-123",
            task_type="graph_build",
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now
        )
        
        assert task.task_id == "task-123"
        assert task.task_type == "graph_build"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0
        assert task.message == ""
        assert task.result is None
        assert task.error is None

    def test_task_to_dict(self):
        """测试 Task 转换为字典"""
        now = datetime.now()
        task = Task(
            task_id="task-456",
            task_type="simulation",
            status=TaskStatus.PROCESSING,
            created_at=now,
            updated_at=now,
            progress=50,
            message="处理中...",
            metadata={"project_id": "proj-123"},
            progress_detail={"current_step": 5, "total_steps": 10}
        )
        
        data = task.to_dict()
        
        assert data["task_id"] == "task-456"
        assert data["task_type"] == "simulation"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["message"] == "处理中..."
        assert data["metadata"] == {"project_id": "proj-123"}
        assert data["progress_detail"] == {"current_step": 5, "total_steps": 10}

    def test_task_with_result(self):
        """测试带结果的任务"""
        now = datetime.now()
        task = Task(
            task_id="task-789",
            task_type="report",
            status=TaskStatus.COMPLETED,
            created_at=now,
            updated_at=now,
            progress=100,
            message="完成",
            result={"report_id": "rpt-001", "content": "报告内容"}
        )
        
        data = task.to_dict()
        assert data["result"]["report_id"] == "rpt-001"
        assert data["progress"] == 100

    def test_task_with_error(self):
        """测试带错误的任务"""
        now = datetime.now()
        task = Task(
            task_id="task-error",
            task_type="graph_build",
            status=TaskStatus.FAILED,
            created_at=now,
            updated_at=now,
            error="连接超时"
        )
        
        data = task.to_dict()
        assert data["status"] == "failed"
        assert data["error"] == "连接超时"


class TestTaskStatus:
    """测试 TaskStatus 枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_status_transitions(self):
        """测试状态转换"""
        # 有效状态
        statuses = [TaskStatus.PENDING, TaskStatus.PROCESSING, 
                   TaskStatus.COMPLETED, TaskStatus.FAILED]
        
        for status in statuses:
            assert TaskStatus(status.value) == status


class TestTaskManager:
    """测试 TaskManager 单例"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = TaskManager()
        manager2 = TaskManager()
        assert manager1 is manager2

    def test_create_task(self):
        """测试创建任务"""
        manager = TaskManager()
        task_id = manager.create_task("test_task", metadata={"key": "value"})
        
        assert task_id is not None
        assert len(task_id) > 0
        
        task = manager.get_task(task_id)
        assert task is not None
        assert task.task_type == "test_task"
        assert task.status == TaskStatus.PENDING
        assert task.metadata == {"key": "value"}

    def test_update_task(self):
        """测试更新任务"""
        manager = TaskManager()
        task_id = manager.create_task("update_task")
        
        # 更新任务
        manager.update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            progress=50,
            message="处理中",
            progress_detail={"step": 1}
        )
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.PROCESSING
        assert task.progress == 50
        assert task.message == "处理中"
        assert task.progress_detail == {"step": 1}

    def test_complete_task(self):
        """测试完成任务"""
        manager = TaskManager()
        task_id = manager.create_task("complete_task")
        
        result = {"output": "任务结果"}
        manager.complete_task(task_id, result)
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
        assert task.result == result

    def test_fail_task(self):
        """测试任务失败"""
        manager = TaskManager()
        task_id = manager.create_task("fail_task")
        
        manager.fail_task(task_id, "发生错误")
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "发生错误"

    def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        manager = TaskManager()
        task = manager.get_task("nonexistent-task-id")
        assert task is None

    def test_update_nonexistent_task(self):
        """测试更新不存在的任务"""
        manager = TaskManager()
        # 应该不抛出异常
        manager.update_task("nonexistent-task-id", progress=50)
        manager.complete_task("nonexistent-task-id", {})
        manager.fail_task("nonexistent-task-id", "错误")

    def test_thread_safety(self):
        """测试线程安全"""
        manager = TaskManager()
        task_ids = []
        errors = []
        
        def create_tasks():
            try:
                for i in range(10):
                    task_id = manager.create_task(f"thread_task_{i}")
                    task_ids.append(task_id)
            except Exception as e:
                errors.append(str(e))
        
        # 创建多个线程同时创建任务
        threads = [threading.Thread(target=create_tasks) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(task_ids) == 50  # 5线程 * 10任务

    def test_list_tasks(self):
        """测试列出任务"""
        manager = TaskManager()
        
        # 创建多个任务
        task_ids = []
        for i in range(5):
            task_id = manager.create_task(f"list_task_{i}")
            task_ids.append(task_id)
        
        # 列出所有任务
        tasks = manager.list_tasks()
        assert len(tasks) >= 5
        
        # 验证任务ID都在列表中
        listed_ids = {t["task_id"] for t in tasks}
        for task_id in task_ids:
            assert task_id in listed_ids

    def test_list_tasks_by_type(self):
        """测试按类型列出任务"""
        manager = TaskManager()
        
        # 创建不同类型任务
        id1 = manager.create_task("type_a")
        id2 = manager.create_task("type_b")
        id3 = manager.create_task("type_a")
        
        # 按类型过滤
        type_a_tasks = manager.list_tasks(task_type="type_a")
        type_b_tasks = manager.list_tasks(task_type="type_b")
        
        assert len([t for t in type_a_tasks if t["task_id"] in [id1, id3]]) == 2
        assert len([t for t in type_b_tasks if t["task_id"] == id2]) == 1

    def test_cleanup_old_tasks(self):
        """测试清理旧任务"""
        manager = TaskManager()
        
        # 创建一个任务并立即完成
        task_id = manager.create_task("old_task")
        manager.complete_task(task_id, {})
        
        # 修改创建时间为很久以前
        task = manager.get_task(task_id)
        task.created_at = datetime.now() - timedelta(hours=25)
        
        # 清理超过24小时的任务
        manager.cleanup_old_tasks(max_age_hours=24)
        
        # 验证任务已被清理
        assert manager.get_task(task_id) is None
