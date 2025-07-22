from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .user import User

class Comment(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_comment_id: Optional[int] = None
    content: str
    like_count: int = 0
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime
    user: Optional[User] = None