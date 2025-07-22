from typing import Optional, Dict, Any
from config import client

class AnalyticsService:
    @staticmethod
    async def get_post_analytics(
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get post analytics and engagement metrics"""
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"is_public": True}},
                        {
                            "range": {
                                "created_at": {
                                    "gte": f"now-{days}d"
                                }
                            }
                        }
                    ]
                }
            }
            
            if user_id:
                query["bool"]["must"].append({"term": {"user_id": user_id}})
            
            response = client.search(
                index="posts",
                body={
                    "query": query,
                    "aggs": {
                        "posts_over_time": {
                            "date_histogram": {
                                "field": "created_at",
                                "calendar_interval": "day"
                            }
                        },
                        "avg_likes": {"avg": {"field": "like_count"}},
                        "avg_comments": {"avg": {"field": "comment_count"}},
                        "total_posts": {"value_count": {"field": "id"}},
                        "top_hashtags": {
                            "terms": {
                                "field": "hashtags.keyword",
                                "size": 10
                            }
                        },
                        "engagement_stats": {
                            "stats": {"field": "like_count"}
                        },
                        "comment_stats": {
                            "stats": {"field": "comment_count"}
                        }
                    },
                    "size": 0
                }
            )
            
            return {
                "analytics": response["aggregations"],
                "total_posts": response["hits"]["total"]["value"],
                "took": response["took"]
            }
        except Exception as e:
            raise Exception(f"Analytics error: {str(e)}")
    
    @staticmethod
    async def get_user_analytics(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get detailed analytics for a specific user"""
        try:
            # Get user's posts analytics
            posts_response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"user_id": user_id}},
                                {"term": {"is_public": True}},
                                {
                                    "range": {
                                        "created_at": {
                                            "gte": f"now-{days}d"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "aggs": {
                        "daily_posts": {
                            "date_histogram": {
                                "field": "created_at",
                                "calendar_interval": "day"
                            }
                        },
                        "total_engagement": {
                            "sum": {"field": "like_count"}
                        },
                        "avg_engagement": {
                            "avg": {"field": "like_count"}
                        },
                        "popular_hashtags": {
                            "terms": {
                                "field": "hashtags.keyword",
                                "size": 10
                            }
                        },
                        "best_performing_post": {
                            "top_hits": {
                                "sort": [{"like_count": {"order": "desc"}}],
                                "size": 1,
                                "_source": ["id", "content", "like_count", "comment_count", "created_at"]
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            return {
                "user_id": user_id,
                "period_days": days,
                "analytics": posts_response["aggregations"],
                "total_posts": posts_response["hits"]["total"]["value"],
                "took": posts_response["took"]
            }
        except Exception as e:
            raise Exception(f"User analytics error: {str(e)}")
    
    @staticmethod
    async def get_trending_content(days: int = 7, limit: int = 10) -> Dict[str, Any]:
        """Get trending content based on engagement"""
        try:
            response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"is_public": True}},
                                {
                                    "range": {
                                        "created_at": {
                                            "gte": f"now-{days}d"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "sort": [
                        {"like_count": {"order": "desc"}},
                        {"comment_count": {"order": "desc"}},
                        {"created_at": {"order": "desc"}}
                    ],
                    "size": limit,
                    "_source": [
                        "id", "content", "like_count", "comment_count", 
                        "hashtags", "created_at", "user.username", "user.full_name"
                    ]
                }
            )
            
            trending_posts = [hit["_source"] for hit in response["hits"]["hits"]]
            
            return {
                "trending_posts": trending_posts,
                "period_days": days,
                "total_found": response["hits"]["total"]["value"],
                "took": response["took"]
            }
        except Exception as e:
            raise Exception(f"Trending content error: {str(e)}")