from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user import User

class Post(BaseModel):
    id: int
    user_id: int
    content: str
    image_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    is_public: bool = True
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user: Optional[User] = None

class PostSuggestion(BaseModel):
    id: int
    content: str
    hashtags: Optional[List[str]] = None
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    user: Optional[dict] = None