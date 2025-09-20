from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class GameplayAspect(str, Enum):
    TACTICAL_DECISION = "tactical_decision"
    POSITIONING = "positioning"
    TEAMWORK = "teamwork"
    GAME_AWARENESS = "game_awareness"
    SKILL_EXECUTION = "skill_execution"

class GameplayFeedback(BaseModel):
    aspect: GameplayAspect
    score: float  # 0-100 scale
    confidence: float  # 0-1 scale
    strengths: List[str]
    improvements: List[str]
    video_timestamps: List[float]  # Timestamps where this aspect is demonstrated
    examples: List[str]  # Specific examples from the gameplay

class GameplayAnalysis(BaseModel):
    overall_score: float
    aspects: Dict[GameplayAspect, GameplayFeedback]
    summary: str
    key_insights: List[str]
    recommended_drills: List[str]
    analyzed_at: datetime
