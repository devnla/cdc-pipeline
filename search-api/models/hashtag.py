from pydantic import BaseModel
from typing import List
from .post import Post

class HashtagStats(BaseModel):
    name: str
    post_count: int
    recent_posts: List[Post]

class HashtagSuggestion(BaseModel):
    name: str
    post_count: int
    trending_score: float = 0.0