from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_verified: bool = False
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    created_at: datetime
    updated_at: datetime

class UserSuggestion(BaseModel):
    id: int
    username: str
    full_name: str
    is_verified: bool = False
    follower_count: int = 0
    profile_image_url: Optional[str] = None