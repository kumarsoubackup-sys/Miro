"""
Knowledge Capsule - Agent Memory Lifecycle Management
为MiroFish群体智能系统添加记忆生命周期管理
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class MemoryStage(Enum):
    """记忆生命周期阶段"""
    SPROUT = "🌱"  # 萌芽 - 新创建的记忆
    GREEN_LEAF = "🌿"  # 绿叶 - 活跃使用的记忆
    YELLOW_LEAF = "🍂"  # 黄叶 - 较少使用的记忆
    RED_LEAF = "🍁"  # 枯叶 - 准备归档的记忆
    SOIL = "🪨"  # 土壤 - 已归档

class KnowledgeCapsule:
    """知识胶囊 - 个体Agent的记忆单元"""
    
    def __init__(self, agent_id: str, content: str, source: str = "experience"):
        self.id = f"capsule_{agent_id}_{datetime.now().timestamp()}"
        self.agent_id = agent_id
        self.content = content
        self.source = source  # experience, observation, prediction, interaction
        self.stage = MemoryStage.SPROUT.value
        self.confidence = 0.7
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.tags = []
        self.connections = []  # 关联的其他胶囊
    
    def access(self):
        """访问记忆，更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        if self.access_count >= 3:
            self.stage = MemoryStage.GREEN_LEAF.value
            self.confidence = min(1.0, self.confidence + 0.05)
    
    def decay(self, days: int):
        """记忆衰减"""
        days_passed = (datetime.now() - self.last_accessed).days
        if days_passed > days:
            decay_amount = 0.01 * (days_passed - days)
            self.confidence = max(0.1, self.confidence - decay_amount)
            
            if self.confidence < 0.3:
                self.stage = MemoryStage.RED_LEAF.value
            elif self.confidence < 0.5:
                self.stage = MemoryStage.YELLOW_LEAF.value
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "content": self.content,
            "source": self.source,
            "stage": self.stage,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "tags": self.tags,
            "connections": self.connections
        }

class AgentMemorySystem:
    """Agent记忆系统 - 管理群体智能中每个Agent的记忆"""
    
    def __init__(self):
        self.agents: Dict[str, List[KnowledgeCapsule]] = {}
        self.shared_knowledge: List[KnowledgeCapsule] = []
    
    def add_memory(self, agent_id: str, content: str, source: str = "experience") -> KnowledgeCapsule:
        """Agent添加新记忆"""
        if agent_id not in self.agents:
            self.agents[agent_id] = []
        
        capsule = KnowledgeCapsule(agent_id, content, source)
        self.agents[agent_id].append(capsule)
        return capsule
    
    def get_active_memories(self, agent_id: str) -> List[KnowledgeCapsule]:
        """获取Agent的活跃记忆"""
        if agent_id not in self.agents:
            return []
        
        return [m for m in self.agents[agent_id] 
                if m.stage == MemoryStage.GREEN_LEAF.value]
    
    def get_shared_knowledge(self) -> List[KnowledgeCapsule]:
        """获取共享知识"""
        return [k for k in self.shared_knowledge 
                if k.stage in [MemoryStage.SPROUT.value, MemoryStage.GREEN_LEAF.value]]
    
    def share_to_group(self, capsule: KnowledgeCapsule):
        """将记忆分享到群体"""
        self.shared_knowledge.append(capsule)
    
    def run_decay_cycle(self):
        """运行记忆衰减周期"""
        for agent_id, capsules in self.agents.items():
            for capsule in capsules:
                capsule.decay(7)  # 7天未访问开始衰减
