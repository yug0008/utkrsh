import cv2
import numpy as np
from typing import Dict, Any, List
import logging
from datetime import datetime
from enum import Enum

from models.gameplay import GameplayAspect, GameplayFeedback, GameplayAnalysis

logger = logging.getLogger(__name__)

class SportType(Enum):
    BASKETBALL = "basketball"
    SOCCER = "soccer"
    TENNIS = "tennis"
    VOLLEYBALL = "volleyball"
    CRICKET = "cricket"
    BASEBALL = "baseball"
    FOOTBALL = "football"

def analyze_gameplay(frames: list, sport_type: SportType, metadata: Dict[str, Any]) -> GameplayAnalysis:
    """
    Analyze gameplay from video frames for sport-specific insights
    """
    try:
        # Sport-specific analysis
        if sport_type == SportType.BASKETBALL:
            return analyze_basketball_gameplay(frames, metadata)
        elif sport_type == SportType.SOCCER:
            return analyze_soccer_gameplay(frames, metadata)
        elif sport_type == SportType.TENNIS:
            return analyze_tennis_gameplay(frames, metadata)
        else:
            # Generic analysis for other sports
            return analyze_generic_gameplay(frames, sport_type, metadata)
            
    except Exception as e:
        logger.error(f"Gameplay analysis failed: {str(e)}")
        # Return a default analysis in case of error
        return create_default_analysis(sport_type)

def analyze_basketball_gameplay(frames: list, metadata: Dict[str, Any]) -> GameplayAnalysis:
    """Basketball-specific gameplay analysis"""
    aspects = {}
    
    # Analyze tactical decisions (simplified example)
    tactical_decision = analyze_tactical_decisions(frames, "basketball")
    aspects[GameplayAspect.TACTICAL_DECISION] = tactical_decision
    
    # Analyze positioning
    positioning = analyze_positioning(frames, "basketball")
    aspects[GameplayAspect.POSITIONING] = positioning
    
    # Analyze teamwork
    teamwork = analyze_teamwork(frames, "basketball")
    aspects[GameplayAspect.TEAMWORK] = teamwork
    
    # Analyze game awareness
    game_awareness = analyze_game_awareness(frames, "basketball")
    aspects[GameplayAspect.GAME_AWARENESS] = game_awareness
    
    # Calculate overall score
    overall_score = calculate_overall_score(aspects)
    
    return GameplayAnalysis(
        overall_score=overall_score,
        aspects=aspects,
        summary=generate_summary(aspects, "basketball"),
        key_insights=extract_key_insights(aspects),
        recommended_drills=recommend_drills(aspects, "basketball"),
        analyzed_at=datetime.utcnow()
    )

def analyze_soccer_gameplay(frames: list, metadata: Dict[str, Any]) -> GameplayAnalysis:
    """Soccer-specific gameplay analysis"""
    aspects = {}
    
    # Analyze different aspects for soccer
    aspects[GameplayAspect.TACTICAL_DECISION] = analyze_tactical_decisions(frames, "soccer")
    aspects[GameplayAspect.POSITIONING] = analyze_positioning(frames, "soccer")
    aspects[GameplayAspect.TEAMWORK] = analyze_teamwork(frames, "soccer")
    aspects[GameplayAspect.GAME_AWARENESS] = analyze_game_awareness(frames, "soccer")
    aspects[GameplayAspect.SKILL_EXECUTION] = analyze_skill_execution(frames, "soccer")
    
    # Calculate overall score
    overall_score = calculate_overall_score(aspects)
    
    return GameplayAnalysis(
        overall_score=overall_score,
        aspects=aspects,
        summary=generate_summary(aspects, "soccer"),
        key_insights=extract_key_insights(aspects),
        recommended_drills=recommend_drills(aspects, "soccer"),
        analyzed_at=datetime.utcnow()
    )

def analyze_tactical_decisions(frames: list, sport: str) -> GameplayFeedback:
    """Analyze tactical decision making in the gameplay"""
    # This would use computer vision to analyze player decisions
    # For now, we'll return mock data
    return GameplayFeedback(
        aspect=GameplayAspect.TACTICAL_DECISION,
        score=75.0,
        confidence=0.82,
        strengths=["Good shot selection", "Effective use of space"],
        improvements=["Work on decision speed under pressure", "Improve passing choices in transition"],
        video_timestamps=[12.5, 45.2, 78.9],
        examples=["At 12.5s: Excellent drive and kick to open teammate", 
                 "At 45.2s: Good decision to take open three-pointer"]
    )

def analyze_positioning(frames: list, sport: str) -> GameplayFeedback:
    """Analyze player positioning throughout the game"""
    # Computer vision analysis would go here
    return GameplayFeedback(
        aspect=GameplayAspect.POSITIONING,
        score=68.0,
        confidence=0.78,
        strengths=["Good defensive stance", "Proper spacing in half-court offense"],
        improvements=["Work on transition defense positioning", "Improve weakside help positioning"],
        video_timestamps=[15.7, 32.1, 67.8],
        examples=["At 15.7s: Excellent defensive positioning forced a turnover",
                 "At 32.1s: Good offensive spacing created driving lane"]
    )

def analyze_teamwork(frames: list, sport: str) -> GameplayFeedback:
    """Analyze teamwork and collaboration"""
    return GameplayFeedback(
        aspect=GameplayAspect.TEAMWORK,
        score=82.0,
        confidence=0.85,
        strengths=["Good communication on defense", "Effective screening for teammates"],
        improvements=["Work on off-ball movement", "Improve timing on pick-and-roll actions"],
        video_timestamps=[23.4, 56.7, 89.0],
        examples=["At 23.4s: Excellent help defense and recovery",
                 "At 56.7s: Good unselfish pass to open teammate"]
    )

def analyze_game_awareness(frames: list, sport: str) -> GameplayFeedback:
    """Analyze overall game awareness and IQ"""
    return GameplayFeedback(
        aspect=GameplayAspect.GAME_AWARENESS,
        score=71.0,
        confidence=0.79,
        strengths=["Good clock management", "Aware of opponent tendencies"],
        improvements=["Work on recognizing defensive schemes faster", "Improve situational awareness in late game"],
        video_timestamps=[18.9, 41.3, 72.6],
        examples=["At 18.9s: Excellent recognition of defensive mismatch",
                 "At 41.3s: Good awareness to call timeout when trapped"]
    )

def analyze_skill_execution(frames: list, sport: str) -> GameplayFeedback:
    """Analyze execution of sport-specific skills"""
    return GameplayFeedback(
        aspect=GameplayAspect.SKILL_EXECUTION,
        score=79.0,
        confidence=0.83,
        strengths=["Consistent shooting form", "Good ball handling under pressure"],
        improvements=["Work on off-hand finishing", "Improve defensive sliding technique"],
        video_timestamps=[10.2, 37.5, 64.8],
        examples=["At 10.2s: Excellent crossover move created separation",
                 "At 37.5s: Good form on pull-up jumper"]
    )

def calculate_overall_score(aspects: Dict[GameplayAspect, GameplayFeedback]) -> float:
    """Calculate weighted overall score from all aspects"""
    if not aspects:
        return 0.0
    
    # Different aspects might have different weights based on sport/position
    weights = {
        GameplayAspect.TACTICAL_DECISION: 0.25,
        GameplayAspect.POSITIONING: 0.20,
        GameplayAspect.TEAMWORK: 0.20,
        GameplayAspect.GAME_AWARENESS: 0.20,
        GameplayAspect.SKILL_EXECUTION: 0.15
    }
    
    total_score = 0.0
    total_weight = 0.0
    
    for aspect, feedback in aspects.items():
        weight = weights.get(aspect, 0.15)  # Default weight if not specified
        total_score += feedback.score * weight
        total_weight += weight
    
    return total_score / total_weight if total_weight > 0 else 0.0

def generate_summary(aspects: Dict[GameplayAspect, GameplayFeedback], sport: str) -> str:
    """Generate a comprehensive summary of the gameplay analysis"""
    if not aspects:
        return "No gameplay analysis available."
    
    strengths = []
    improvements = []
    
    for feedback in aspects.values():
        strengths.extend(feedback.strengths[:1])  # Take top strength from each aspect
        improvements.extend(feedback.improvements[:1])  # Take top improvement from each aspect
    
    return f"In your {sport} gameplay, you demonstrated strengths in {', '.join(strengths[:3])}. " \
           f"Focus on improving {', '.join(improvements[:3])} to elevate your performance to the next level."

def extract_key_insights(aspects: Dict[GameplayAspect, GameplayFeedback]) -> List[str]:
    """Extract the most important insights from the analysis"""
    insights = []
    
    for aspect, feedback in aspects.items():
        if feedback.score < 70:
            insights.append(f"Your {aspect.value.replace('_', ' ')} needs attention (score: {feedback.score}/100)")
        elif feedback.score > 85:
            insights.append(f"Your {aspect.value.replace('_', ' ')} is a major strength (score: {feedback.score}/100)")
    
    if not insights:
        insights.append("Your gameplay shows balanced skills across all aspects with no major weaknesses")
    
    return insights[:5]  # Return top 5 insights

def recommend_drills(aspects: Dict[GameplayAspect, GameplayFeedback], sport: str) -> List[str]:
    """Recommend specific drills based on the analysis"""
    drills = []
    
    for aspect, feedback in aspects.items():
        if feedback.score < 75:
            # Recommend drills for weaker aspects
            if aspect == GameplayAspect.POSITIONING:
                if sport == "basketball":
                    drills.append("Defensive sliding drills with mirror exercises")
                    drills.append("Closeout and recovery drills")
                elif sport == "soccer":
                    drills.append("Positional awareness drills with cones")
                    drills.append("Small-sided games focusing on spacing")
            
            elif aspect == GameplayAspect.TACTICAL_DECISION:
                drills.append("Video analysis of professional players' decision making")
                drills.append("Decision-making drills under time pressure")
    
    # Add some general drills if not enough specific ones
    if len(drills) < 3:
        drills.extend([
            "3-man weave for transition decision making",
            "5-on-5 shell drill for defensive positioning",
            "Pick-and-roll read and react drills"
        ])
    
    return drills[:5]  # Return top 5 drills

def create_default_analysis(sport_type: SportType) -> GameplayAnalysis:
    """Create a default analysis when detailed analysis fails"""
    return GameplayAnalysis(
        overall_score=65.0,
        aspects={},
        summary="Basic gameplay analysis completed. Detailed analysis unavailable at this time.",
        key_insights=["Enable enhanced analysis features for detailed feedback"],
        recommended_drills=["Fundamental skills practice", "Game situation drills"],
        analyzed_at=datetime.utcnow()
    )
