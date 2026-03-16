"""
LightRAG 实体读取服务
接口3：读取图谱中的所有实体，按需过滤
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.graph_entity_reader')


@dataclass
class EntityNode:
    """实体节点模型"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]

    # 关联数据（在需要时填充）
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)

    def get_entity_type(self) -> Optional[str]:
        """获取实体的具体类型（非'Entity'或'Node'的标签）"""
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "type": self.get_entity_type(),
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes
        }


@dataclass
class FilteredEntities:
    """过滤后的实体结果"""
    entities: List[EntityNode]
    total_count: int
    entity_types: Dict[str, int]  # 类型及其数量分布


class GraphEntityReader:
    """
    图谱实体读取服务
    从LightRAG(NetworkX)获取实体，支持丰富的过滤条件
    """

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_base = workspace_dir or Config.LIGHTRAG_WORKSPACE_DIR

    def read_and_filter_entities(
        self,
        graph_id: str,
        entity_types: Optional[List[str]] = None,
        min_degree: int = 1,
        include_related_info: bool = True
    ) -> FilteredEntities:
        """
        读取并过滤图谱实体

        Args:
            graph_id: 图谱ID
            entity_types: 要保留的实体类型列表，如果为空则保留所有（除了忽略的类型）
            min_degree: 最小度数（包含该实体的边数），低于此值的实体将被忽略
            include_related_info: 是否包含相关的边和邻居节点信息

        Returns:
            FilteredEntities: 过滤后的实体结果
        """
        logger.info(f"开始读取图谱 {graph_id} 的实体...")

        # 1. 获取所有节点和边
        all_nodes = self.get_all_nodes(graph_id)
        all_edges = self.get_all_edges(graph_id)

        logger.info(f"获取到 {len(all_nodes)} 个节点，{len(all_edges)} 条边")

        # 2. 计算每个节点的度数和相关边
        node_degrees = {node["uuid"]: 0 for node in all_nodes}
        node_edges = {node["uuid"]: [] for node in all_nodes}
        node_neighbors = {node["uuid"]: set() for node in all_nodes}

        for edge in all_edges:
            source = edge.get("source_node_uuid")
            target = edge.get("target_node_uuid")

            if source and source in node_degrees:
                node_degrees[source] += 1
                node_edges[source].append(edge)
                if target:
                    node_neighbors[source].add(target)

            if target and target in node_degrees:
                node_degrees[target] += 1
                node_edges[target].append(edge)
                if source:
                    node_neighbors[target].add(source)

        # 3. 过滤节点并构建EntityNode对象
        node_dict = {n["uuid"]: n for n in all_nodes}
        filtered_entities = []
        entity_type_counts = {}

        # 将传入的类型转为小写以便比较
        target_types_lower = [t.lower() for t in entity_types] if entity_types else []

        for node in all_nodes:
            node_uuid = node["uuid"]
            labels = node.get("labels", [])

            # 获取具体类型
            entity_type = None
            for label in labels:
                if label not in ["Entity", "Node"]:
                    entity_type = label
                    break

            # 使用一个默认值以便处理未分类节点
            safe_type = entity_type or "Unknown"

            # 过滤条件1: 节点度数
            if node_degrees.get(node_uuid, 0) < min_degree:
                continue

            # 过滤条件2: 实体类型
            if target_types_lower:
                # 如果指定了类型，则只保留指定类型的实体
                type_match = False
                for t in target_types_lower:
                    if t in safe_type.lower() or t in node["name"].lower():
                        type_match = True
                        break

                if not type_match:
                    continue
            else:
                pass

            # 通过过滤，构建EntityNode
            entity = EntityNode(
                uuid=node_uuid,
                name=node.get("name", ""),
                labels=labels,
                summary=node.get("summary", ""),
                attributes=node.get("attributes", {})
            )

            # 添加关联信息
            if include_related_info:
                # 添加相关的边
                for edge in node_edges.get(node_uuid, []):
                    rel_edge = {
                        "uuid": edge.get("uuid"),
                        "edge_name": edge.get("name"),
                        "fact": edge.get("fact"),
                        "direction": "outgoing" if edge.get("source_node_uuid") == node_uuid else "incoming",
                        "other_node_uuid": edge.get("target_node_uuid") if edge.get("source_node_uuid") == node_uuid else edge.get("source_node_uuid")
                    }
                    entity.related_edges.append(rel_edge)

                # 添加邻居节点简要信息
                for neighbor_uuid in node_neighbors.get(node_uuid, set()):
                    neighbor = node_dict.get(neighbor_uuid)
                    if neighbor:
                        entity.related_nodes.append({
                            "uuid": neighbor.get("uuid"),
                            "name": neighbor.get("name"),
                            "labels": neighbor.get("labels", []),
                            "summary": neighbor.get("summary", "")[:100]  # 截断摘要
                        })

            filtered_entities.append(entity)

            # 统计类型分布
            entity_type_counts[safe_type] = entity_type_counts.get(safe_type, 0) + 1

        logger.info(f"过滤后保留 {len(filtered_entities)} 个实体")

        return FilteredEntities(
            entities=filtered_entities,
            total_count=len(filtered_entities),
            entity_types=entity_type_counts
        )

    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """获取图谱的所有节点"""
        result = []
        try:
            working_dir = os.path.join(self.workspace_base, graph_id)
            import networkx as nx
            graph_path = os.path.join(working_dir, "graph_chunk_entity_relation.graphml")
            if os.path.exists(graph_path):
                G = nx.read_graphml(graph_path)
                for node, data in G.nodes(data=True):
                    result.append({
                        "uuid": str(node),
                        "name": str(node),
                        "labels": ["Entity"],
                        "summary": data.get("description", ""),
                        "attributes": data
                    })
        except Exception as e:
            logger.warning(f"获取节点失败: {e}")

        return result

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """获取图谱的所有边"""
        result = []
        try:
            working_dir = os.path.join(self.workspace_base, graph_id)
            import networkx as nx
            graph_path = os.path.join(working_dir, "graph_chunk_entity_relation.graphml")
            if os.path.exists(graph_path):
                G = nx.read_graphml(graph_path)
                for u, v, data in G.edges(data=True):
                    result.append({
                        "uuid": f"{u}-{v}",
                        "name": data.get("label", "RELATED_TO"),
                        "fact": data.get("description", ""),
                        "source_node_uuid": str(u),
                        "target_node_uuid": str(v),
                    })
        except Exception as e:
            logger.warning(f"获取边失败: {e}")

        return result
