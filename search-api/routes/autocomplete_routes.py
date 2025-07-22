from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from models import AutoCompleteResponse, SearchSuggestionsResponse
from services.autocomplete_service import AutoCompleteService

router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])

@router.get("/suggestions", response_model=AutoCompleteResponse)
async def get_autocomplete_suggestions(
    q: str = Query(..., min_length=2, description="Search query for autocomplete"),
    types: Optional[List[str]] = Query(
        default=["users", "hashtags", "content"], 
        description="Types of suggestions to include: users, hashtags, content, locations"
    ),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions per type")
):
    """Get autocomplete suggestions for search input"""
    try:
        return await AutoCompleteService.get_autocomplete_suggestions(
            query=q,
            suggestion_types=types,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=List[dict])
async def get_user_suggestions(
    q: str = Query(..., min_length=2, description="Username or name query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of user suggestions")
):
    """Get user suggestions for autocomplete"""
    try:
        result = await AutoCompleteService.get_autocomplete_suggestions(
            query=q,
            suggestion_types=["users"],
            limit=limit
        )
        return result.suggestions.get("users", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hashtags", response_model=List[dict])
async def get_hashtag_suggestions(
    q: str = Query(..., min_length=1, description="Hashtag query (without #)"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of hashtag suggestions")
):
    """Get hashtag suggestions for autocomplete"""
    try:
        # Remove # if present
        query = q.lstrip('#')
        result = await AutoCompleteService.get_autocomplete_suggestions(
            query=query,
            suggestion_types=["hashtags"],
            limit=limit
        )
        return result.suggestions.get("hashtags", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content", response_model=List[dict])
async def get_content_suggestions(
    q: str = Query(..., min_length=3, description="Content search query"),
    limit: int = Query(5, ge=1, le=15, description="Maximum number of content suggestions")
):
    """Get content suggestions for autocomplete"""
    try:
        result = await AutoCompleteService.get_autocomplete_suggestions(
            query=q,
            suggestion_types=["content"],
            limit=limit
        )
        return result.suggestions.get("content", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(8, ge=1, le=15, description="Maximum number of search suggestions")
):
    """Get search query suggestions based on popular searches"""
    try:
        return await AutoCompleteService.get_search_suggestions(
            query=q,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mentions", response_model=List[dict])
async def get_mention_suggestions(
    q: str = Query(..., min_length=1, description="Username query for mentions (without @)"),
    limit: int = Query(10, ge=1, le=15, description="Maximum number of mention suggestions")
):
    """Get user suggestions for @mentions"""
    try:
        # Remove @ if present
        query = q.lstrip('@')
        result = await AutoCompleteService.get_autocomplete_suggestions(
            query=query,
            suggestion_types=["users"],
            limit=limit
        )
        # Format for mentions
        users = result.suggestions.get("users", [])
        mentions = []
        for user in users:
            mentions.append({
                "id": user.get("id"),
                "username": user.get("username"),
                "display_name": user.get("full_name") or user.get("username"),
                "avatar_url": user.get("avatar_url"),
                "verified": user.get("is_verified", False),
                "mention": f"@{user.get('username')}"
            })
        return mentions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))