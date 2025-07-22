from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from models import SearchResponse, User, Post, HashtagStats
from services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/posts", response_model=SearchResponse)
async def search_posts(
    q: str = Query(..., description="Search query"),
    hashtags: Optional[List[str]] = Query(None, description="Filter by hashtags"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    sort_by: str = Query("relevance", description="Sort by: relevance, date, likes"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Results per page")
):
    """Search posts with full-text search and filtering options"""
    try:
        return await SearchService.search_posts(
            query=q,
            hashtags=hashtags,
            user_id=user_id,
            sort_by=sort_by,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=SearchResponse)
async def search_users(
    q: str = Query(..., description="Search query for username or full name"),
    verified_only: bool = Query(False, description="Show only verified users"),
    sort_by: str = Query("relevance", description="Sort by: relevance, followers, posts"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Results per page")
):
    """Search users by username, full name, or bio"""
    try:
        return await SearchService.search_users(
            query=q,
            verified_only=verified_only,
            sort_by=sort_by,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hashtags", response_model=SearchResponse)
async def search_hashtags(
    q: str = Query(..., description="Hashtag search query"),
    min_posts: int = Query(1, ge=1, description="Minimum number of posts"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Results per page")
):
    """Search hashtags with post count information"""
    try:
        return await SearchService.search_hashtags(
            query=q,
            min_posts=min_posts,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending/hashtags", response_model=List[HashtagStats])
async def get_trending_hashtags(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of hashtags to return")
):
    """Get trending hashtags from recent posts"""
    try:
        return await SearchService.get_trending_hashtags(days=days, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Alternative endpoint for trending hashtags (backward compatibility)
@router.get("/hashtags/trending", response_model=List[HashtagStats])
async def get_hashtags_trending(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of hashtags to return")
):
    """Get trending hashtags from recent posts (alternative endpoint)"""
    try:
        return await SearchService.get_trending_hashtags(days=days, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))