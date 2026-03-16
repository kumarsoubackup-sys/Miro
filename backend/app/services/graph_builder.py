"""
图谱构建服务
接口2：使用LightRAG构建Graph
"""

import os
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from .text_processor import TextProcessor
from ..utils.logger import get_logger

logger = get_logger('mirofish.graph_builder')


@dataclass
class GraphInfo:
    """图谱信息"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    图谱构建服务
    负责调用LightRAG构建知识图谱
    """
    
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_base = workspace_dir or Config.LIGHTRAG_WORKSPACE_DIR
        self.task_manager = TaskManager()
    
    def _get_lightrag_instance(self, graph_id: str) -> LightRAG:
        """获取LightRAG实例"""
        working_dir = os.path.join(self.workspace_base, graph_id)
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

    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """
        异步构建图谱
        
        Args:
            text: 输入文本
            ontology: 本体定义
            graph_name: 图谱名称
            chunk_size: 文本块大小
            chunk_overlap: 块重叠大小
            batch_size: 每批发送的块数量
            
        Returns:
            任务ID
        """
        # 创建任务
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )
        
        # 准备实体类型
        entity_types = ["Person", "Organization", "Other"]
        if ontology and "entity_types" in ontology:
            entity_types = [t.get("name") for t in ontology.get("entity_types", [])]

        # 在后台线程中执行构建
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, entity_types, graph_name, chunk_size, chunk_overlap, batch_size)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        entity_types: List[str],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int
    ):
        """图谱构建工作线程"""
        # 定义进度回调
        def progress_callback(status: str, progress: float):
            self.task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                progress=progress,
                message=status
            )
            
        try:
            # 1. 初始化图谱 (生成图谱ID)
            progress_callback("正在初始化图谱环境...", 0.05)
            graph_id = self.create_graph(graph_name)
            
            # 更新任务的图谱ID
            task = self.task_manager.get_task(task_id)
            if task and task.metadata:
                task.metadata["graph_id"] = graph_id
            
            # 2. 设置本体 (可选在LightRAG，可以通过system prompt注入，这里简化为只插入文本)
            progress_callback("正在配置图谱本体...", 0.1)
            # LightRAG implicitly builds the ontology. We could pass the ontology as part of the LLM prompt inside lightrag if we needed strict adherence.
            
            # 3. 文本处理与分块
            progress_callback("正在处理和分块文档...", 0.15)
            
            # 4. 插入文本到LightRAG
            progress_callback("正在构建知识图谱 (可能需要几分钟)...", 0.3)
            rag = self._get_lightrag_instance(graph_id)
            
            # 确保全局提示词修改在多线程环境中是安全的
            import threading
            from lightrag.prompt import PROMPTS
            import re
            
            if not hasattr(self.__class__, '_prompt_lock'):
                self.__class__._prompt_lock = threading.Lock()

            with self.__class__._prompt_lock:
                original_prompt = PROMPTS["entity_extraction_system_prompt"]
                # 找到 types 位置并替换
                custom_types = ", ".join([f'"{t}"' for t in entity_types])

                custom_prompt = re.sub(
                    r'categorize the entity using one of the following types: \{entity_types\}',
                    f'categorize the entity using one of the following types: {custom_types}',
                    original_prompt
                )

                # Inject to LightRAG via monkey patch for this instance specifically
                PROMPTS["entity_extraction_system_prompt"] = custom_prompt

                try:
                    rag.insert(text)
                finally:
                    # Restore prompt
                    PROMPTS["entity_extraction_system_prompt"] = original_prompt
            
            # 5. 获取图谱信息
            progress_callback("正在获取图谱统计信息...", 0.9)
            graph_info = self._get_graph_info(graph_id)
            
            # 更新任务完成状态
            self.task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                progress=1.0,
                message=f"图谱构建完成! 共包含 {graph_info.node_count} 个节点和 {graph_info.edge_count} 条边。",
                result=graph_info.to_dict()
            )
            logger.info(f"Task {task_id} completed. Graph ID: {graph_id}")
            
        except Exception as e:
            logger.error(f"图谱构建失败: {e}", exc_info=True)
            self.task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.FAILED,
                message=f"构建失败: {str(e)}"
            )

    def create_graph(self, name: str) -> str:
        """创建新图谱并返回其ID"""
        return str(uuid.uuid4())

    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """获取图谱信息"""
        try:
            rag = self._get_lightrag_instance(graph_id)
            # 读取底层的 NetworkX 图获取节点和边
            import networkx as nx
            graph_path = os.path.join(rag.working_dir, "graph_chunk_entity_relation.graphml")
            if os.path.exists(graph_path):
                G = nx.read_graphml(graph_path)
                return GraphInfo(
                    graph_id=graph_id,
                    node_count=G.number_of_nodes(),
                    edge_count=G.number_of_edges(),
                    entity_types=[] # LightRAG nodes might not have explicit Zep-like types without parsing attributes
                )
        except Exception as e:
            logger.warning(f"Error getting graph info: {e}")
            
        return GraphInfo(
            graph_id=graph_id,
            node_count=0,
            edge_count=0,
            entity_types=[]
        )
    
    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        获取完整图谱数据（包含详细信息）
        """
        nodes_data = []
        edges_data = []
        try:
            rag = self._get_lightrag_instance(graph_id)
            import networkx as nx
            graph_path = os.path.join(rag.working_dir, "graph_chunk_entity_relation.graphml")
            if os.path.exists(graph_path):
                G = nx.read_graphml(graph_path)

                for node, data in G.nodes(data=True):
                    nodes_data.append({
                        "uuid": str(node), # Node names act as UUIDs in LightRAG
                        "name": str(node),
                        "labels": ["Entity"],
                        "summary": data.get("description", ""),
                        "attributes": data,
                        "created_at": None,
                    })

                for u, v, data in G.edges(data=True):
                    edges_data.append({
                        "uuid": f"{u}-{v}",
                        "name": data.get("label", "RELATED_TO"),
                        "fact": data.get("description", ""),
                        "fact_type": data.get("label", "RELATED_TO"),
                        "source_node_uuid": str(u),
                        "target_node_uuid": str(v),
                        "source_node_name": str(u),
                        "target_node_name": str(v),
                        "attributes": data,
                    })
        except Exception as e:
            logger.error(f"Error getting graph data: {e}")
            
        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }
    
    def delete_graph(self, graph_id: str):
        """删除图谱"""
        import shutil
        working_dir = os.path.join(self.workspace_base, graph_id)
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
