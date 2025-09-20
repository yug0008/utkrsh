import os
import logging
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from supabase import Client

from models.database import get_supabase_client

logger = logging.getLogger(__name__)

async def upload_video_to_supabase(file: UploadFile, filename: str, user_id: str) -> str:
    """
    Upload a video file to Supabase Storage
    """
    supabase: Client = get_supabase_client()
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Create user-specific folder path
        file_path = f"videos/{user_id}/{filename}"
        
        # Upload to Supabase Storage
        response = supabase.storage.from_("videos").upload(
            file_path, content, file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        url_response = supabase.storage.from_("videos").get_public_url(file_path)
        
        logger.info(f"Video uploaded successfully: {file_path}")
        return url_response
        
    except Exception as e:
        logger.error(f"Failed to upload video to Supabase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )

async def download_video_from_supabase(file_path: str) -> bytes:
    """
    Download a video file from Supabase Storage
    """
    supabase: Client = get_supabase_client()
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        response = supabase.storage.from_("videos").download(file_path)
        return response
        
    except Exception as e:
        logger.error(f"Failed to download video from Supabase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download video: {str(e)}"
        )

async def delete_video_from_supabase(file_path: str) -> bool:
    """
    Delete a video file from Supabase Storage
    """
    supabase: Client = get_supabase_client()
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable"
        )
    
    try:
        response = supabase.storage.from_("videos").remove([file_path])
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete video from Supabase: {str(e)}")
        return False

def get_video_url(file_path: str) -> str:
    """
    Get public URL for a video file in Supabase Storage
    """
    supabase: Client = get_supabase_client()
    if supabase is None:
        return ""
    
    try:
        return supabase.storage.from_("videos").get_public_url(file_path)
    except Exception as e:
        logger.error(f"Failed to get video URL: {str(e)}")
        return ""
