from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from .user import UserSuggestion
from .post import PostSuggestion

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    results: List[Dict[str, Any]]
    took: int
    aggregations: Optional[Dict[str, Any]] = None

class AutoCompleteItem(BaseModel):
    type: str  # 'user', 'post', 'hashtag', 'mention'
    value: str
    display_text: str
    metadata: Optional[Dict[str, Any]] = None
    score: float = 0.0

class AutoCompleteResponse(BaseModel):
    suggestions: List[AutoCompleteItem]
    total: int
    took: int

class SearchSuggestion(BaseModel):
    text: str
    highlighted: str
    score: float
    type: str  # 'content', 'hashtag', 'user', 'location'

class SearchSuggestionsResponse(BaseModel):
    suggestions: List[SearchSuggestion]
    total: int
    took: int