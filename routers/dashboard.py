from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

from models.user import User, UserRole
from models.metric import PerformanceMetric
from models.video import VideoAnalysis
from models.gameplay import GameplayAnalysis
from utils.auth import get_current_user, get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/athlete/{athlete_id}")
async def get_athlete_dashboard(
    athlete_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    if athlete_id != current_user.id and current_user.role not in [UserRole.COACH, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this dashboard"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Get basic athlete info
        athlete_response = supabase.table("users").select("*").eq("id", athlete_id).execute()
        if not athlete_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Athlete not found"
            )
        
        athlete = athlete_response.data[0]
        
        # Get recent metrics
        metrics_response = supabase.table("performance_metrics").select("*").eq("user_id", athlete_id).order("recorded_at", desc=True).limit(10).execute()
        recent_metrics = [PerformanceMetric(**metric) for metric in metrics_response.data]
        
        # Get recent video analyses
        videos_response = supabase.table("videos").select("*, video_analyses(*)").eq("user_id", athlete_id).order("uploaded_at", desc=True).limit(5).execute()
        recent_analyses = []
        
        for video in videos_response.data:
            if video["video_analyses"]:
                analysis_data = video["video_analyses"][0]["analysis_data"]
                recent_analyses.append(VideoAnalysis(**analysis_data))
        
        # Get recent gameplay analyses
        gameplay_response = supabase.table("videos").select("*, video_analyses(*)").eq("user_id", athlete_id).eq("skill_type", "gameplay").order("uploaded_at", desc=True).limit(3).execute()
        recent_gameplay = []
        
        for video in gameplay_response.data:
            if video["video_analyses"] and video["video_analyses"][0]["analysis_data"].get("gameplay_analysis"):
                analysis_data = video["video_analyses"][0]["analysis_data"]["gameplay_analysis"]
                recent_gameplay.append(GameplayAnalysis(**analysis_data))
        
        # Calculate performance summary (enhanced with gameplay data)
        performance_summary = calculate_performance_summary(athlete_id, recent_metrics, recent_analyses, recent_gameplay)
        
        # Get injury risk alerts
        injury_alerts = get_injury_alerts(recent_analyses)
        
        # Get gameplay insights
        gameplay_insights = get_gameplay_insights(recent_gameplay)
        
        return {
            "athlete_info": athlete,
            "recent_metrics": recent_metrics,
            "recent_analyses": recent_analyses,
            "recent_gameplay": recent_gameplay,
            "performance_summary": performance_summary,
            "injury_alerts": injury_alerts,
            "gameplay_insights": gameplay_insights,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Athlete dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve athlete dashboard"
        )

@router.get("/coach/{coach_id}/team")
async def get_coach_dashboard(
    coach_id: str,
    current_user: User = Depends(get_current_user)
):
    # Verify coach identity and permissions
    if coach_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this dashboard"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Get coach's athletes (simplified - would need a coach-athlete relationship table)
        athletes_response = supabase.table("users").select("*").eq("role", UserRole.ATHLETE.value).limit(20).execute()
        athletes = athletes_response.data
        
        # Get team analytics
        team_analytics = await get_team_analytics([athlete["id"] for athlete in athletes])
        
        # Get alerts (injuries, poor performance, etc.)
        alerts = await get_team_alerts([athlete["id"] for athlete in athletes])
        
        return {
            "team_members": athletes,
            "team_analytics": team_analytics,
            "alerts": alerts,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Coach dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve coach dashboard"
        )

def calculate_performance_summary(athlete_id: str, metrics: List[PerformanceMetric], analyses: List[VideoAnalysis], gameplay: List[GameplayAnalysis]) -> Dict[str, Any]:
    """Calculate a summary of athlete performance including gameplay"""
    # Enhanced implementation with gameplay data
    if not metrics and not analyses and not gameplay:
        return {"overall_score": 0, "trend": "neutral", "areas_to_improve": []}
    
    # Calculate scores from different sources
    metric_scores = [m.value for m in metrics if hasattr(m, 'value')]
    analysis_scores = [a.skill_assessment.score for a in analyses if hasattr(a, 'skill_assessment')]
    gameplay_scores = [g.overall_score for g in gameplay if hasattr(g, 'overall_score')]
    
    all_scores = metric_scores + analysis_scores + gameplay_scores
    
    if not all_scores:
        return {"overall_score": 0, "trend": "neutral", "areas_to_improve": []}
    
    overall_score = sum(all_scores) / len(all_scores)
    
    # Determine trend (consider gameplay in trend analysis)
    trend = "neutral"
    if len(metric_scores) > 1:
        trend = "improving" if metric_scores[-1] > metric_scores[0] else "declining"
    elif len(gameplay) > 1:
        trend = "improving" if gameplay[-1].overall_score > gameplay[0].overall_score else "declining"
    
    # Get areas to improve from analyses and gameplay
    areas_to_improve = []
    for analysis in analyses:
        if hasattr(analysis, 'skill_assessment') and hasattr(analysis.skill_assessment, 'areas_for_improvement'):
            areas_to_improve.extend(analysis.skill_assessment.areas_for_improvement)
    
    for game in gameplay:
        for aspect in game.aspects.values():
            areas_to_improve.extend(aspect.improvements)
    
    return {
        "overall_score": overall_score,
        "trend": trend,
        "areas_to_improve": list(set(areas_to_improve))[:5]  # Top 5 unique areas
    }

def get_injury_alerts(analyses: List[VideoAnalysis]) -> List[Dict[str, Any]]:
    """Get injury risk alerts from video analyses"""
    alerts = []
    
    for analysis in analyses:
        if (hasattr(analysis, 'injury_risk_prediction') and 
            hasattr(analysis.injury_risk_prediction, 'risk_level') and
            analysis.injury_risk_prediction.risk_level in ["medium", "high"]):
            
            alerts.append({
                "risk_level": analysis.injury_risk_prediction.risk_level,
                "risk_score": analysis.injury_risk_prediction.risk_score,
                "risk_factors": analysis.injury_risk_prediction.risk_factors,
                "recommendations": analysis.injury_risk_prediction.prevention_recommendations
            })
    
    return alerts

def get_gameplay_insights(gameplay_analyses: List[GameplayAnalysis]) -> List[Dict[str, Any]]:
    """Extract key insights from gameplay analyses"""
    insights = []
    
    for analysis in gameplay_analyses:
        insights.extend(analysis.key_insights)
    
    # Return unique insights, limited to 5
    return list(set(insights))[:5]

async def get_team_analytics(athlete_ids: List[str]) -> Dict[str, Any]:
    """Get analytics for the entire team"""
    # Simplified implementation
    supabase = get_supabase_client()
    
    # Get recent metrics for all athletes
    metrics_response = supabase.table("performance_metrics").select("*").in_("user_id", athlete_ids).order("recorded_at", desc=True).limit(100).execute()
    
    # Calculate team averages (simplified)
    if metrics_response.data:
        avg_performance = sum(metric["value"] for metric in metrics_response.data) / len(metrics_response.data)
    else:
        avg_performance = 0
    
    return {
        "team_size": len(athlete_ids),
        "average_performance": avg_performance,
        "top_performers": athlete_ids[:3],  # Simplified
        "needs_attention": athlete_ids[-2:] if len(athlete_ids) > 5 else []  # Simplified
    }

async def get_team_alerts(athlete_ids: List[str]) -> List[Dict[str, Any]]:
    """Get alerts for the team"""
    # Simplified implementation
    supabase = get_supabase_client()
    
    alerts = []
    
    # Check for high injury risk
    videos_response = supabase.table("videos").select("*, video_analyses(*)").in_("user_id", athlete_ids).order("uploaded_at", desc=True).limit(50).execute()
    
    for video in videos_response.data:
        if video["video_analyses"]:
            analysis_data = video["video_analyses"][0]["analysis_data"]
            if analysis_data["injury_risk_prediction"]["risk_level"] in ["high"]:
                alerts.append({
                    "type": "injury_risk",
                    "severity": "high",
                    "athlete_id": video["user_id"],
                    "message": f"High injury risk detected for athlete",
                    "details": analysis_data["injury_risk_prediction"]
                })
    
    return alerts
