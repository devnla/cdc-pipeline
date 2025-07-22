from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/posts", response_model=Dict[str, Any])
async def get_post_analytics(
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get post analytics and engagement metrics"""
    try:
        return await AnalyticsService.get_post_analytics(
            user_id=user_id,
            days=days
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_analytics(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get detailed analytics for a specific user"""
    try:
        return await AnalyticsService.get_user_analytics(
            user_id=user_id,
            days=days
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending", response_model=Dict[str, Any])
async def get_trending_content(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of trending posts to return")
):
    """Get trending content based on engagement metrics"""
    try:
        return await AnalyticsService.get_trending_content(
            days=days,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/engagement-summary", response_model=Dict[str, Any])
async def get_engagement_summary(
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get a summary of engagement metrics"""
    try:
        analytics = await AnalyticsService.get_post_analytics(
            user_id=user_id,
            days=days
        )
        
        # Extract key metrics for summary
        aggs = analytics.get("analytics", {})
        
        summary = {
            "period_days": days,
            "total_posts": analytics.get("total_posts", 0),
            "average_likes": round(aggs.get("avg_likes", {}).get("value", 0), 2),
            "average_comments": round(aggs.get("avg_comments", {}).get("value", 0), 2),
            "top_hashtags": [
                {
                    "hashtag": bucket["key"],
                    "count": bucket["doc_count"]
                }
                for bucket in aggs.get("top_hashtags", {}).get("buckets", [])[:5]
            ],
            "engagement_stats": aggs.get("engagement_stats", {}),
            "daily_activity": [
                {
                    "date": bucket["key_as_string"],
                    "posts": bucket["doc_count"]
                }
                for bucket in aggs.get("posts_over_time", {}).get("buckets", [])
            ]
        }
        
        if user_id:
            summary["user_id"] = user_id
            
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))