from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

from models.user import User, UserRole
from models.achievement import Achievement, Badge, LeaderboardEntry
from utils.auth import get_current_user, get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    sport_type: str = None,
    time_frame: str = "month",  # day, week, month, all_time
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    try:
        # Calculate date range based on time_frame
        now = datetime.utcnow()
        if time_frame == "day":
            start_date = now - timedelta(days=1)
        elif time_frame == "week":
            start_date = now - timedelta(weeks=1)
        elif time_frame == "month":
            start_date = now - timedelta(days=30)
        else:  # all_time
            start_date = None
        
        # Build query for leaderboard
        # This is a simplified implementation - a real implementation would
        # need to calculate scores based on multiple factors
        
        query = supabase.table("users").select("id, full_name, sport, position")
        
        if sport_type:
            query = query.eq("sport", sport_type)
        
        # For a real implementation, we would join with performance data
        # and calculate scores. This is a placeholder.
        query = query.limit(limit)
        
        response = query.execute()
        
        # Convert to leaderboard entries with placeholder scores
        leaderboard = []
        for i, user in enumerate(response.data):
            leaderboard.append(LeaderboardEntry(
                user_id=user["id"],
                username=user["full_name"],
                sport=user["sport"],
                position=user["position"],
                score=100 - i,  # Placeholder score
                rank=i + 1
            ))
        
        return leaderboard
    
    except Exception as e:
        logger.error(f"Leaderboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve leaderboard"
        )

@router.get("/achievements/{user_id}", response_model=List[Achievement])
async def get_user_achievements(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    if user_id != current_user.id and current_user.role not in [UserRole.COACH, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these achievements"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Get user achievements
        response = supabase.table("user_achievements").select("*, achievements(*)").eq("user_id", user_id).execute()
        
        achievements = []
        for item in response.data:
            achievement_data = item["achievements"]
            if achievement_data:
                achievements.append(Achievement(
                    id=achievement_data["id"],
                    name=achievement_data["name"],
                    description=achievement_data["description"],
                    badge_url=achievement_data["badge_url"],
                    earned_at=item["earned_at"]
                ))
        
        return achievements
    
    except Exception as e:
        logger.error(f"Achievements error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve achievements"
        )

@router.get("/badges/{user_id}", response_model=List[Badge])
async def get_user_badges(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    if user_id != current_user.id and current_user.role not in [UserRole.COACH, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these badges"
        )
    
    supabase = get_supabase_client()
    
    try:
        # In a real implementation, this would calculate badges based on achievements
        # and performance milestones. This is a simplified version.
        
        # Get user's sport
        user_response = supabase.table("users").select("sport").eq("id", user_id).execute()
        sport = user_response.data[0]["sport"] if user_response.data else None
        
        # Placeholder badges based on sport
        badge_templates = {
            "basketball": [
                {"name": "Three-Point Specialist", "description": "Made 50+ three-pointers"},
                {"name": "Defensive Stopper", "description": "50+ steals or blocks"},
                {"name": "Team Player", "description": "100+ assists"}
            ],
            "soccer": [
                {"name": "Goal Scorer", "description": "Scored 20+ goals"},
                {"name": "Playmaker", "description": "30+ assists"},
                {"name": "Defensive Wall", "description": "50+ tackles"}
            ],
            "default": [
                {"name": "Consistency", "description": "10+ training sessions"},
                {"name": "Improver", "description": "10%+ performance increase"},
                {"name": "Dedication", "description": "30+ days of activity"}
            ]
        }
        
        badges = []
        template = badge_templates.get(sport, badge_templates["default"])
        
        for i, temp in enumerate(template):
            badges.append(Badge(
                id=f"badge_{i+1}",
                name=temp["name"],
                description=temp["description"],
                image_url=f"/static/badges/{sport or 'default'}_{i+1}.png",
                earned=True  # Placeholder - would check actual criteria
            ))
        
        return badges
    
    except Exception as e:
        logger.error(f"Badges error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve badges"
        )

@router.post("/award-achievement/{user_id}")
async def award_achievement(
    user_id: str,
    achievement_id: str,
    current_user: User = Depends(get_current_user)
):
    # Only coaches and admins can award achievements
    if current_user.role not in [UserRole.COACH, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to award achievements"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Check if achievement exists
        achievement_response = supabase.table("achievements").select("*").eq("id", achievement_id).execute()
        if not achievement_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Achievement not found"
            )
        
        # Check if user already has this achievement
        existing_response = supabase.table("user_achievements").select("*").eq("user_id", user_id).eq("achievement_id", achievement_id).execute()
        if existing_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has this achievement"
            )
        
        # Award achievement
        award_data = {
            "user_id": user_id,
            "achievement_id": achievement_id,
            "awarded_by": current_user.id,
            "earned_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("user_achievements").insert(award_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to award achievement"
            )
        
        return {"message": "Achievement awarded successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Award achievement error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to award achievement"
        )
