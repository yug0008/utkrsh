from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models.user import User, UserRole
from models.metric import PerformanceMetric, MetricCreate, MetricType
from utils.auth import get_current_user, get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/add", response_model=PerformanceMetric)
async def add_performance_metric(
    metric: MetricCreate,
    current_user: User = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    try:
        metric_data = {
            "user_id": current_user.id,
            "metric_type": metric.metric_type.value,
            "value": metric.value,
            "unit": metric.unit,
            "recorded_at": metric.recorded_at or datetime.utcnow().isoformat(),
            "session_id": metric.session_id,
            "notes": metric.notes
        }
        
        response = supabase.table("performance_metrics").insert(metric_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add metric"
            )
        
        return PerformanceMetric(**response.data[0])
    
    except Exception as e:
        logger.error(f"Add metric error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add performance metric"
        )

@router.get("/athlete/{athlete_id}", response_model=List[PerformanceMetric])
async def get_athlete_metrics(
    athlete_id: str,
    metric_type: Optional[MetricType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    if athlete_id != current_user.id and current_user.role not in [UserRole.COACH, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these metrics"
        )
    
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("performance_metrics").select("*").eq("user_id", athlete_id)
        
        if metric_type:
            query = query.eq("metric_type", metric_type.value)
        
        if start_date:
            query = query.gte("recorded_at", start_date.isoformat())
        
        if end_date:
            query = query.lte("recorded_at", end_date.isoformat())
        
        query = query.order("recorded_at", desc=True)
        response = query.execute()
        
        return [PerformanceMetric(**metric) for metric in response.data]
    
    except Exception as e:
        logger.error(f"Get metrics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )

@router.get("/trends/{athlete_id}")
async def get_metric_trends(
    athlete_id: str,
    metric_type: MetricType,
    timeframe_days: int = 30,
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    if athlete_id != current_user.id and current_user.role not in [UserRole.COACH, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these metrics"
        )
    
    supabase = get_supabase_client()
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=timeframe_days)
    
    try:
        response = supabase.table("performance_metrics").select("*").eq("user_id", athlete_id).eq("metric_type", metric_type.value).gte("recorded_at", start_date.isoformat()).lte("recorded_at", end_date.isoformat()).order("recorded_at").execute()
        
        metrics = [PerformanceMetric(**metric) for metric in response.data]
        
        # Calculate trends
        if len(metrics) > 1:
            first_value = metrics[0].value
            last_value = metrics[-1].value
            trend = last_value - first_value
            trend_percentage = (trend / first_value) * 100 if first_value != 0 else 0
        else:
            trend = 0
            trend_percentage = 0
        
        return {
            "metrics": metrics,
            "timeframe_days": timeframe_days,
            "trend": trend,
            "trend_percentage": trend_percentage,
            "metric_count": len(metrics)
        }
    
    except Exception as e:
        logger.error(f"Get trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metric trends"
        )
