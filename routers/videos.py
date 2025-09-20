from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import logging
import uuid
from datetime import datetime

from models.user import User, UserRole
from models.video import VideoUpload, VideoAnalysis, VideoStatus
from models.gameplay import GameplayAnalysis
from utils.auth import get_current_user
from services.storage import upload_video_to_supabase
from services.ai_analysis import analyze_video
from services.cheat_detection import detect_cheating
from utils.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=VideoUpload)
async def upload_video(
    file: UploadFile = File(...),
    sport_type: str = Form(...),
    skill_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a video for analysis
    """
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video files are allowed"
        )
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    
    try:
        # Upload to Supabase Storage
        file_url = await upload_video_to_supabase(file, filename, current_user.id)
        
        # Store video metadata in database
        supabase = get_supabase_client()
        video_data = {
            "user_id": current_user.id,
            "filename": filename,
            "original_name": file.filename,
            "sport_type": sport_type,
            "skill_type": skill_type,
            "file_url": file_url,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": VideoStatus.UPLOADED.value
        }
        
        response = supabase.table("videos").insert(video_data).execute()
        video_id = response.data[0]["id"]
        
        return VideoUpload(
            id=video_id,
            user_id=current_user.id,
            filename=filename,
            original_name=file.filename,
            sport_type=sport_type,
            skill_type=skill_type,
            file_url=file_url,
            uploaded_at=video_data["uploaded_at"],
            status=VideoStatus.UPLOADED
        )
    
    except Exception as e:
        logger.error(f"Video upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload video"
        )

@router.post("/analyze/{video_id}", response_model=VideoAnalysis)
async def analyze_uploaded_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze an uploaded video using AI
    """
    try:
        # Get video metadata
        supabase = get_supabase_client()
        response = supabase.table("videos").select("*").eq("id", video_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        video_data = response.data[0]
        
        # Check if user owns the video or is admin/coach with access
        if video_data["user_id"] != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this video"
            )
        
        # Update status to processing
        supabase.table("videos").update({"status": VideoStatus.PROCESSING.value}).eq("id", video_id).execute()
        
        # Perform AI analysis
        analysis_results = await analyze_video(video_data["file_url"])
        
        # Perform cheat detection
        cheat_detection = await detect_cheating(video_data["file_url"])
        
        # Combine results
        full_analysis = {
            **analysis_results,
            "cheat_detection": cheat_detection,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Store analysis results
        supabase.table("video_analyses").insert({
            "video_id": video_id,
            "analysis_data": full_analysis,
            "analyzed_at": full_analysis["analyzed_at"]
        }).execute()
        
        # Update video status to completed
        supabase.table("videos").update({
            "status": VideoStatus.COMPLETED.value,
            "analyzed_at": full_analysis["analyzed_at"]
        }).eq("id", video_id).execute()
        
        return VideoAnalysis(**full_analysis)
    
    except Exception as e:
        logger.error(f"Video analysis error: {str(e)}")
        
        # Update status to failed
        supabase.table("videos").update({
            "status": VideoStatus.FAILED.value,
            "error_message": str(e)
        }).eq("id", video_id).execute()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze video"
        )

@router.get("/{video_id}/analysis", response_model=VideoAnalysis)
async def get_video_analysis(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get analysis results for a specific video
    """
    try:
        # Get video metadata
        supabase = get_supabase_client()
        video_response = supabase.table("videos").select("*").eq("id", video_id).execute()
        
        if not video_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        video_data = video_response.data[0]
        
        # Check if user owns the video or is admin/coach with access
        if video_data["user_id"] != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this video"
            )
        
        # Get analysis results
        analysis_response = supabase.table("video_analyses").select("*").eq("video_id", video_id).execute()
        
        if not analysis_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found for this video"
            )
        
        return VideoAnalysis(**analysis_response.data[0]["analysis_data"])
    
    except Exception as e:
        logger.error(f"Get analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis"
        )

@router.get("/{video_id}/gameplay-feedback", response_model=GameplayAnalysis)
async def get_gameplay_feedback(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed gameplay feedback for a specific video
    """
    try:
        # Get video metadata
        supabase = get_supabase_client()
        video_response = supabase.table("videos").select("*").eq("id", video_id).execute()
        
        if not video_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        video_data = video_response.data[0]
        
        # Check if user owns the video or is admin/coach with access
        if video_data["user_id"] != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this video"
            )
        
        # Get analysis results
        analysis_response = supabase.table("video_analyses").select("*").eq("video_id", video_id).execute()
        
        if not analysis_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found for this video"
            )
        
        analysis_data = analysis_response.data[0]["analysis_data"]
        
        # Check if gameplay analysis exists
        if "gameplay_analysis" not in analysis_data or not analysis_data["gameplay_analysis"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gameplay analysis not available for this video"
            )
        
        return GameplayAnalysis(**analysis_data["gameplay_analysis"])
    
    except Exception as e:
        logger.error(f"Get gameplay feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve gameplay feedback"
        )

@router.get("/athlete/{athlete_id}/gameplay-feedback")
async def get_athlete_gameplay_feedback(
    athlete_id: str,
    sport_type: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Get all gameplay feedback for a specific athlete
    """
    # Check permissions
    if athlete_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this data"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Build query to find gameplay videos
        query = supabase.table("videos").select("*, video_analyses(*)").eq("user_id", athlete_id).eq("skill_type", "gameplay")
        
        if sport_type:
            query = query.eq("sport_type", sport_type)
        
        query = query.order("uploaded_at", desc=True).limit(limit)
        response = query.execute()
        
        gameplay_feedback = []
        
        for video in response.data:
            if video["video_analyses"] and video["video_analyses"][0]["analysis_data"].get("gameplay_analysis"):
                analysis = video["video_analyses"][0]["analysis_data"]["gameplay_analysis"]
                feedback = {
                    "video_id": video["id"],
                    "uploaded_at": video["uploaded_at"],
                    "sport_type": video["sport_type"],
                    "analysis": GameplayAnalysis(**analysis)
                }
                gameplay_feedback.append(feedback)
        
        return {
            "athlete_id": athlete_id,
            "gameplay_feedback": gameplay_feedback,
            "count": len(gameplay_feedback)
        }
    
    except Exception as e:
        logger.error(f"Get athlete gameplay feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve athlete gameplay feedback"
        )
