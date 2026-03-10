"""
Memory Tracker - 记忆追踪与溯源系统
"""

from typing import Dict, List, Optional
from datetime import datetime
import json

class MemoryTrace:
    """记忆追踪记录"""
    
    def __init__(self, capsule_id: str, memory_type: str, content: str):
        self.id = f"trace_{datetime.now().timestamp()}"
        self.capsule_id = capsule_id
        self.memory_type = memory_type  # observation, prediction, interaction, reflection
        self.content = content
        self.timestamp = datetime.now()
        self.importance = 0.5
        self.tags = []
    
    def to_dict(self):
        return {
            "id": self.id,
            "capsule_id": self.capsule_id,
            "memory_type": self.memory_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "tags": self.tags
        }

class MemoryTracker:
    """记忆追踪器 - 记录Agent的记忆轨迹"""
    
    def __init__(self):
        self.traces: Dict[str, List[MemoryTrace]] = {}  # agent_id -> traces
        self.knowledge_graph: Dict[str, List[str]] = {}  # capsule_id -> connected_ids
    
    def add_trace(self, agent_id: str, capsule_id: str, memory_type: str, content: str):
        """添加记忆追踪"""
        if agent_id not in self.traces:
            self.traces[agent_id] = []
        
        trace = MemoryTrace(capsule_id, memory_type, content)
        self.traces[agent_id].append(trace)
        
        # 更新知识图谱
        if capsule_id not in self.knowledge_graph:
            self.knowledge_graph[capsule_id] = []
    
    def link_memories(self, capsule_a: str, capsule_b: str, relation: str):
        """关联两条记忆"""
        if capsule_a in self.knowledge_graph:
            self.knowledge_graph[capsule_a].append({"id": capsule_b, "relation": relation})
    
    def get_memory_timeline(self, agent_id: str) -> List[dict]:
        """获取Agent的记忆时间线"""
        if agent_id not in self.traces:
            return []
        
        return [t.to_dict() for t in sorted(self.traces[agent_id], 
                                             key=lambda x: x.timestamp, reverse=True)]
    
    def search_memories(self, agent_id: str, query: str) -> List[dict]:
        """搜索记忆"""
        if agent_id not in self.traces:
            return []
        
        return [t.to_dict() for t in self.traces[agent_id] 
                if query.lower() in t.content.lower()]
