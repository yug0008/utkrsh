from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoUpload(BaseModel):
    id: str
    user_id: str
    filename: str
    original_name: str
    sport_type: str
    skill_type: str
    file_url: str
    uploaded_at: datetime
    status: VideoStatus

class SkillAssessment(BaseModel):
    score: float  # 0-100 scale
    confidence: float  # 0-1 scale
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]

class PostureAnalysis(BaseModel):
    posture_score: float
    alignment_issues: List[str]
    recommended_corrections: List[str]

class InjuryRiskPrediction(BaseModel):
    risk_level: str  # low, medium, high
    risk_score: float  # 0-1 scale
    risk_factors: List[str]
    prevention_recommendations: List[str]

class CheatDetectionResult(BaseModel):
    is_cheating_detected: bool
    confidence: float
    detected_anomalies: List[str]
    frames_analyzed: int
    duplicate_frames: int

class VideoAnalysis(BaseModel):
    skill_assessment: SkillAssessment
    posture_analysis: PostureAnalysis
    injury_risk_prediction: InjuryRiskPrediction
    cheat_detection: CheatDetectionResult
    gameplay_analysis: Optional[Dict[str, Any]] = None  # New field for gameplay analysis
    analyzed_at: datetime
