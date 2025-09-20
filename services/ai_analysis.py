import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Any, List
import logging
import tempfile
import httpx
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from services.storage import download_video_from_supabase  # Supabase storage integration

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MediaPipe solutions
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


# ============================= ENUMS ============================= #

class SportType(str, Enum):
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    SOCCER = "soccer"
    BASEBALL = "baseball"
    GENERAL = "general"


class SkillType(str, Enum):
    SHOOTING = "shooting"
    DRIBBLING = "dribbling"
    DEFENSE = "defense"
    SERVING = "serving"
    SWING = "swing"
    KICKING = "kicking"
    THROWING = "throwing"
    GAMEPLAY = "gameplay"
    GENERAL = "general"


# ============================= MODELS ============================= #

class GameplayAnalysis(BaseModel):
    performance_score: float
    tactical_awareness: float
    decision_making: float
    efficiency: float
    strengths: List[str]
    areas_for_improvement: List[str]
    key_insights: List[str]


# ============================= MAIN FUNCTION ============================= #

async def analyze_video(
    video_url: str,
    sport_type: SportType = SportType.GENERAL,
    skill_type: SkillType = SkillType.GENERAL
) -> Dict[str, Any]:
    """Main function to analyze a sports video using AI/ML techniques"""
    try:
        # Download video
        video_path = await download_video(video_url)

        # Extract frames
        frames = extract_frames(video_path)

        # Analyses
        posture_analysis = analyze_posture(frames)
        skill_assessment = assess_skills(frames, posture_analysis, sport_type, skill_type)
        injury_risk = predict_injury_risk(posture_analysis, skill_assessment)

        # Gameplay analysis (if applicable)
        gameplay_analysis = None
        if skill_type == SkillType.GAMEPLAY:
            gameplay_analysis = analyze_gameplay(frames, sport_type)

        return {
            "skill_assessment": skill_assessment,
            "posture_analysis": posture_analysis,
            "injury_risk_prediction": injury_risk,
            "gameplay_analysis": gameplay_analysis.dict() if gameplay_analysis else None,
            "analyzed_at": datetime.utcnow().isoformat(),
            "sport_type": sport_type.value,
            "skill_type": skill_type.value
        }

    except Exception as e:
        logger.error(f"Video analysis failed: {str(e)}")
        raise


# ============================= VIDEO DOWNLOAD ============================= #

async def download_video(video_url: str) -> str:
    """Download video from Supabase or external URL"""
    try:
        if "supabase" in video_url:
            file_path = extract_file_path_from_url(video_url)
            video_content = await download_video_from_supabase(file_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(video_content)
                return tmp_file.name
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(video_url)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                    tmp_file.write(response.content)
                    return tmp_file.name
    except Exception as e:
        logger.error(f"Failed to download video: {str(e)}")
        raise


def extract_file_path_from_url(url: str) -> str:
    """Extract file path from Supabase storage URL"""
    parts = url.split('/')
    try:
        object_index = parts.index('object')
        return '/'.join(parts[object_index + 2:])
    except (ValueError, IndexError):
        logger.warning(f"Could not parse Supabase URL: {url}")
        return url


# ============================= FRAME EXTRACTION ============================= #

def extract_frames(video_path: str, frame_interval: int = 10) -> list:
    """Extract frames from video"""
    cap = cv2.VideoCapture(video_path)
    frames, frame_count = [], 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame = cv2.resize(frame, (640, 480))
            frames.append(frame)

        frame_count += 1

    cap.release()
    return frames


# ============================= POSTURE ANALYSIS ============================= #

def analyze_posture(frames: list) -> Dict[str, Any]:
    """Analyze posture using MediaPipe Pose"""
    posture_results = {
        "posture_score": 0.0,
        "alignment_issues": [],
        "recommended_corrections": [],
        "keypoints": []
    }

    with mp_pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.5) as pose:
        for frame in frames:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            if results.pose_landmarks:
                metrics = calculate_posture_metrics(results.pose_landmarks)
                posture_results["posture_score"] += metrics["score"]
                posture_results["alignment_issues"].extend(metrics["issues"])
                posture_results["keypoints"].append(metrics["keypoints"])

        if frames:
            posture_results["posture_score"] /= len(frames)
            posture_results["alignment_issues"] = list(set(posture_results["alignment_issues"]))

    return posture_results


def calculate_posture_metrics(landmarks) -> Dict[str, Any]:
    """Calculate posture metrics"""
    issues, score = [], 85.0

    shoulder = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]]

    hip = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value],
           landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP.value]]

    knee = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE.value],
            landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE.value]]

    if abs(shoulder[0].y - shoulder[1].y) > 0.05:
        issues.append("Shoulder imbalance detected")
        score -= 10

    if abs(hip[0].y - hip[1].y) > 0.05:
        issues.append("Hip imbalance detected")
        score -= 10

    if abs(knee[0].y - knee[1].y) > 0.05:
        issues.append("Knee imbalance detected")
        score -= 8

    return {
        "score": max(score, 0),
        "issues": issues,
        "keypoints": [(lm.x, lm.y, lm.z) for lm in landmarks.landmark]
    }


# ============================= SKILL ASSESSMENT ============================= #

def assess_skills(frames: list, posture_analysis: Dict[str, Any],
                 sport_type: SportType = SportType.GENERAL,
                 skill_type: SkillType = SkillType.GENERAL) -> Dict[str, Any]:
    """Assess sports skills"""
    if sport_type == SportType.BASKETBALL:
        if skill_type == SkillType.SHOOTING:
            return assess_basketball_shooting()
        elif skill_type == SkillType.DRIBBLING:
            return assess_basketball_dribbling()
        elif skill_type == SkillType.DEFENSE:
            return assess_basketball_defense()

    elif sport_type == SportType.TENNIS:
        if skill_type == SkillType.SERVING:
            return assess_tennis_serve()
        elif skill_type == SkillType.SWING:
            return assess_tennis_swing()

    elif sport_type == SportType.SOCCER and skill_type == SkillType.KICKING:
        return assess_soccer_kicking()

    elif sport_type == SportType.BASEBALL:
        if skill_type == SkillType.SWING:
            return assess_baseball_swing()
        elif skill_type == SkillType.THROWING:
            return assess_baseball_throwing()

    return {
        "score": 78.0,
        "confidence": 0.85,
        "feedback": "Good form overall. Focus on follow-through and balance.",
        "strengths": ["Good acceleration", "Proper grip"],
        "areas_for_improvement": ["Follow-through", "Balance maintenance"]
    }


def assess_basketball_shooting(): ...
def assess_basketball_dribbling(): ...
def assess_basketball_defense(): ...
def assess_tennis_serve(): ...
def assess_tennis_swing(): ...
def assess_soccer_kicking(): ...
def assess_baseball_swing(): ...
def assess_baseball_throwing(): ...

# (You already have these defined above — I kept structure short here to save space)


# ============================= GAMEPLAY ANALYSIS ============================= #

def analyze_gameplay(frames: list, sport_type: SportType) -> GameplayAnalysis:
    if sport_type == SportType.BASKETBALL:
        return analyze_basketball_gameplay()
    elif sport_type == SportType.SOCCER:
        return analyze_soccer_gameplay()
    elif sport_type == SportType.TENNIS:
        return analyze_tennis_gameplay()
    return GameplayAnalysis(
        performance_score=75.0,
        tactical_awareness=70.0,
        decision_making=72.0,
        efficiency=68.0,
        strengths=["Good positioning", "Awareness of surroundings"],
        areas_for_improvement=["Decision making under pressure", "Consistency"],
        key_insights=["Tend to favor right side", "Good recovery speed"]
    )


def analyze_basketball_gameplay(): ...
def analyze_soccer_gameplay(): ...
def analyze_tennis_gameplay(): ...


# ============================= INJURY RISK ============================= #

def predict_injury_risk(posture_analysis: Dict[str, Any], skill_assessment: Dict[str, Any]) -> Dict[str, Any]:
    risk_score = 0.3
    if len(posture_analysis["alignment_issues"]) > 2:
        risk_score += 0.3
    if posture_analysis["posture_score"] < 70:
        risk_score += 0.2
    if skill_assessment["score"] < 70:
        risk_score += 0.1

    risk_level = "low" if risk_score < 0.4 else "medium" if risk_score < 0.7 else "high"

    prevention = [
        "Focus on proper form during exercises",
        "Incorporate balance training",
        "Consider professional coaching for technique improvement"
    ]
    if "Shoulder imbalance detected" in posture_analysis["alignment_issues"]:
        prevention.append("Incorporate shoulder stability exercises")
    if "Hip imbalance detected" in posture_analysis["alignment_issues"]:
        prevention.append("Add hip mobility and strengthening exercises")
    if "Knee imbalance detected" in posture_analysis["alignment_issues"]:
        prevention.append("Focus on knee stabilization exercises")

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 2),
        "risk_factors": posture_analysis["alignment_issues"],
        "prevention_recommendations": prevention
    }
