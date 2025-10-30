"""
Judge Performance Model

Tracks historical accuracy and performance metrics for each LLM Judge.
"""

from sqlalchemy import Column, String, Integer, Float, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from mcp_bets.models.base import Base, TimestampMixin


class JudgePerformance(Base, TimestampMixin):
    """Judge Performance Tracking"""
    
    __tablename__ = "judges_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    judge_id = Column(String(50), nullable=False, index=True)  # "claude_4.5", "gpt_4o", "gemini_2.5_pro"
    week_number = Column(Integer, nullable=False, index=True)
    
    # Ultra Lock Performance
    ultra_lock_picks = Column(Integer, default=0)
    ultra_lock_hits = Column(Integer, default=0)
    ultra_lock_accuracy = Column(Float)  # Percentage (0-100)
    
    # Super Lock Performance
    super_lock_picks = Column(Integer, default=0)
    super_lock_hits = Column(Integer, default=0)
    super_lock_accuracy = Column(Float)
    
    # Standard Lock Performance
    standard_lock_picks = Column(Integer, default=0)
    standard_lock_hits = Column(Integer, default=0)
    standard_lock_accuracy = Column(Float)
    
    # Lotto Performance
    lotto_picks = Column(Integer, default=0)
    lotto_hits = Column(Integer, default=0)
    lotto_accuracy = Column(Float)
    
    # Mega Lotto Performance
    mega_lotto_picks = Column(Integer, default=0)
    mega_lotto_hits = Column(Integer, default=0)
    mega_lotto_accuracy = Column(Float)
    
    # Category-specific accuracy (JSONB)
    category_accuracy = Column(JSONB)  # {"rushing": 82%, "receiving": 88%, "passing_tds": 79%, ...}
    
    # Five Pillars validation accuracy
    five_pillars_validation_accuracy = Column(Float)
    
    # Dynamic weight multiplier
    weight_multiplier = Column(DECIMAL(5, 4), default=1.0000)  # e.g., 1.1500
    
    def __repr__(self):
        return f"<JudgePerformance {self.judge_id} Week {self.week_number} - Weight: {self.weight_multiplier}>"
    
    def calculate_weight(self):
        """
        Calculate weight based on tier-specific accuracy
        
        Ultra Lock accuracy × 1.5 (highest priority)
        Super Lock accuracy × 1.25
        Standard Lock accuracy × 1.0
        
        Final Weight = (UL_score + SL_score + STD_score) / 3
        """
        if not all([self.ultra_lock_accuracy, self.super_lock_accuracy, self.standard_lock_accuracy]):
            return 1.0000
        
        ul_component = (self.ultra_lock_accuracy / 100) * 1.5
        sl_component = (self.super_lock_accuracy / 100) * 1.25
        std_component = (self.standard_lock_accuracy / 100) * 1.0
        
        weight = (ul_component + sl_component + std_component) / 3
        return round(weight, 4)
