"""
Prediction Tracker - 预测追踪与验证系统
"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class PredictionStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXPIRED = "expired"

class Prediction:
    """预测记录"""
    
    def __init__(self, agent_id: str, content: str, outcome: str = None):
        self.id = f"pred_{datetime.now().timestamp()}"
        self.agent_id = agent_id
        self.content = content
        self.outcome = outcome
        self.status = PredictionStatus.PENDING.value
        self.created_at = datetime.now()
        self.validated_at = None
        self.confidence = 0.5
        self.related_memories = []
    
    def validate(self, actual_outcome: str):
        """验证预测结果"""
        self.outcome = actual_outcome
        self.validated_at = datetime.now()
        
        # 计算预测准确度
        if self.content.lower() in actual_outcome.lower() or actual_outcome.lower() in self.content.lower():
            self.status = PredictionStatus.VALIDATED.value
            self.confidence = min(1.0, self.confidence + 0.1)
        else:
            self.status = PredictionStatus.REJECTED.value
            self.confidence = max(0.1, self.confidence - 0.1)
    
    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "content": self.content,
            "outcome": self.outcome,
            "status": self.status,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "validated_at": self.validated_at.isoformat() if self.validated_at else None
        }

class PredictionTracker:
    """预测追踪器"""
    
    def __init__(self):
        self.predictions: List[Prediction] = []
    
    def add_prediction(self, agent_id: str, content: str) -> Prediction:
        """添加新预测"""
        pred = Prediction(agent_id, content)
        self.predictions.append(pred)
        return pred
    
    def validate_prediction(self, pred_id: str, actual_outcome: str):
        """验证预测"""
        for pred in self.predictions:
            if pred.id == pred_id:
                pred.validate(actual_outcome)
                return pred
        return None
    
    def get_agent_predictions(self, agent_id: str) -> List[dict]:
        """获取Agent的所有预测"""
        return [p.to_dict() for p in self.predictions if p.agent_id == agent_id]
    
    def get_accuracy_rate(self, agent_id: str) -> float:
        """计算预测准确率"""
        agent_preds = [p for p in self.predictions if p.agent_id == agent_id]
        if not agent_preds:
            return 0.0
        
        validated = [p for p in agent_preds if p.status == PredictionStatus.VALIDATED.value]
        return len(validated) / len(agent_preds)
