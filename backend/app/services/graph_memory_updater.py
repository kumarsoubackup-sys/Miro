"""
LightRAG 图谱记忆更新服务
在模拟过程中，收集Agent的行动、对话和事件，
并周期性地将这些作为新的文本插入到LightRAG中以更新图谱
"""

import threading
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.graph_memory_updater')


@dataclass
class SimulationAction:
    """模拟行动记录"""
    agent_id: int
    agent_name: str
    action_type: str
    content: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    platform: str = "unknown"
    round_num: int = 0
    timestamp: str = ""

    def to_text(self) -> str:
        """转换为适合写入图谱的文本格式"""
        text = f"在第{self.round_num}轮 ({self.timestamp})，在{self.platform}平台上: "

        if self.action_type == "post":
            text += f"{self.agent_name} 发布了帖子: '{self.content}'"
        elif self.action_type == "comment":
            target = f"对 {self.target_name} " if self.target_name else ""
            text += f"{self.agent_name} {target}发表了评论: '{self.content}'"
        elif self.action_type == "like":
            target = f" {self.target_name} 的" if self.target_name else ""
            text += f"{self.agent_name} 点赞了{target}内容。"
        elif self.action_type == "repost":
            target = f" {self.target_name} 的" if self.target_name else ""
            text += f"{self.agent_name} 转发了{target}内容，并说: '{self.content}'"
        else:
            text += f"{self.agent_name} 执行了 {self.action_type} 行动: '{self.content}'"

        return text


class GraphMemoryUpdater:
    """
    LightRAG图谱记忆更新器（针对单一模拟）
    """

    def __init__(self, simulation_id: str, graph_id: str, workspace_dir: Optional[str] = None):
        self.simulation_id = simulation_id
        self.graph_id = graph_id
        self.workspace_base = workspace_dir or Config.LIGHTRAG_WORKSPACE_DIR

        # 内部状态
        self.pending_actions: List[SimulationAction] = []
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # 配置
        self.batch_size = 10  # 累积多少条行动后更新一次
        self.update_interval = 60  # 最长更新间隔(秒)

        logger.info(f"GraphMemoryUpdater 初始化: simulation={simulation_id}, graph={graph_id}")

    def _get_lightrag_instance(self) -> LightRAG:
        """获取LightRAG实例"""
        working_dir = os.path.join(self.workspace_base, self.graph_id)
        os.makedirs(working_dir, exist_ok=True)

        # Configure the LightRAG LLM with OpenRouter
        async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return await openai_complete_if_cache(
                Config.LLM_MODEL_NAME or "openai/gpt-4o-mini",
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=Config.LLM_API_KEY,
                base_url=Config.LLM_BASE_URL or "https://openrouter.ai/api/v1",
                **kwargs
            )

        # Use centralized global embedding function
        from ..utils.embeddings import get_lightrag_embedding_func

        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=llm_model_func,
            embedding_func=get_lightrag_embedding_func(),
        )
        return rag

    def start(self):
        """启动后台更新线程"""
        if self.is_running:
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._update_loop, name=f"MemoryUpdater-{self.simulation_id}")
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"图谱记忆更新线程已启动: {self.simulation_id}")

    def stop(self):
        """停止后台更新线程"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            # 强制执行最后一次更新
            self._flush_pending_actions()
            self.thread.join(timeout=2.0)
        logger.info(f"图谱记忆更新线程已停止: {self.simulation_id}")

    def add_action(self, action: SimulationAction):
        """添加一个模拟行动到待处理队列"""
        with self.lock:
            self.pending_actions.append(action)

            # 如果达到批次大小，可以唤醒线程提前处理（简化实现：依赖定时循环）
            if len(self.pending_actions) >= self.batch_size:
                logger.debug(f"行动队列达到批次大小 ({self.batch_size})")

    def record_agent_action(
        self,
        agent_id: int,
        agent_name: str,
        action_type: str,
        content: str,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        platform: str = "unknown",
        round_num: int = 0
    ):
        """便捷方法：记录Agent行动"""
        action = SimulationAction(
            agent_id=agent_id,
            agent_name=agent_name,
            action_type=action_type,
            content=content,
            target_id=target_id,
            target_name=target_name,
            platform=platform,
            round_num=round_num,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.add_action(action)

    def _update_loop(self):
        """后台循环，定期更新图谱"""
        last_update_time = time.time()

        while self.is_running:
            current_time = time.time()

            # 检查是否需要更新（队列达到批次大小，或达到时间间隔）
            should_update = False
            with self.lock:
                queue_size = len(self.pending_actions)
                if queue_size > 0:
                    if queue_size >= self.batch_size or (current_time - last_update_time) >= self.update_interval:
                        should_update = True

            if should_update:
                self._flush_pending_actions()
                last_update_time = time.time()

            # 短暂休眠，避免占用CPU
            time.sleep(1.0)

    def _flush_pending_actions(self):
        """将待处理的行动刷新到图谱"""
        # 取出当前所有的行动
        actions_to_process = []
        with self.lock:
            if not self.pending_actions:
                return
            actions_to_process = self.pending_actions.copy()
            self.pending_actions.clear()

        logger.info(f"开始更新图谱记忆，共 {len(actions_to_process)} 条记录...")

        # 将行动转换为文本
        texts_to_insert = [action.to_text() for action in actions_to_process]

        try:
            rag = self._get_lightrag_instance()
            combined_text = "\n".join(texts_to_insert)

            # 将新收集的行动文本插入到LightRAG中
            rag.insert(combined_text)

            logger.info(f"成功更新了 {len(texts_to_insert)} 条图谱记忆")

        except Exception as e:
            logger.error(f"更新图谱记忆失败: {e}")
            # 如果失败，放回队列以便下次重试（可选）
            # with self.lock:
            #     self.pending_actions = actions_to_process + self.pending_actions


class GraphMemoryManager:
    """
    全局图谱记忆管理器，管理所有活跃的更新器
    """

    _updaters: Dict[str, GraphMemoryUpdater] = {}
    _lock = threading.Lock()

    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> GraphMemoryUpdater:
        """创建并启动一个更新器"""
        with cls._lock:
            if simulation_id in cls._updaters:
                logger.warning(f"模拟 {simulation_id} 的记忆更新器已存在")
                return cls._updaters[simulation_id]

            updater = GraphMemoryUpdater(simulation_id, graph_id)
            updater.start()
            cls._updaters[simulation_id] = updater
            return updater

    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[GraphMemoryUpdater]:
        """获取现有的更新器"""
        with cls._lock:
            return cls._updaters.get(simulation_id)

    @classmethod
    def stop_updater(cls, simulation_id: str):
        """停止并移除更新器"""
        with cls._lock:
            updater = cls._updaters.pop(simulation_id, None)
            if updater:
                updater.stop()

    @classmethod
    def stop_all(cls):
        """停止所有更新器"""
        with cls._lock:
            for simulation_id, updater in list(cls._updaters.items()):
                updater.stop()
            cls._updaters.clear()
