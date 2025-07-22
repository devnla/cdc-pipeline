from typing import List, Optional, Dict, Any
from config import client
from models.search import SearchResponse

class SearchService:
    @staticmethod
    async def search_posts(
        query: str,
        page: int = 1,
        size: int = 10,
        hashtags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        sort_by: str = "relevance"
    ) -> SearchResponse:
        """Search posts with full-text search and filters"""
        # Build query
        search_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["content^2", "user.full_name", "user.username"],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    {"term": {"is_public": True}}
                ],
                "filter": []
            }
        }
        
        # Add filters
        if hashtags:
            if len(hashtags) == 1:
                search_query["bool"]["filter"].append({"term": {"hashtags": hashtags[0]}})
            else:
                search_query["bool"]["filter"].append({"terms": {"hashtags": hashtags}})
        if user_id:
            search_query["bool"]["filter"].append({"term": {"user_id": user_id}})
        
        # Sort configuration
        sort_config = []
        if sort_by == "created_at":
            sort_config = [{"created_at": {"order": "desc"}}]
        elif sort_by == "like_count":
            sort_config = [{"like_count": {"order": "desc"}}, {"created_at": {"order": "desc"}}]
        else:  # relevance
            sort_config = ["_score", {"created_at": {"order": "desc"}}]
        
        # Execute search
        response = client.search(
            index="posts",
            body={
                "query": search_query,
                "sort": sort_config,
                "from": (page - 1) * size,
                "size": size,
                "highlight": {
                    "fields": {
                        "content": {}
                    }
                }
            }
        )
        
        return SearchResponse(
            total=response["hits"]["total"]["value"],
            page=page,
            size=size,
            results=[hit["_source"] for hit in response["hits"]["hits"]],
            took=response["took"]
        )
    
    @staticmethod
    async def search_users(
        query: str,
        page: int = 1,
        size: int = 10,
        verified_only: bool = False,
        sort_by: str = "relevance"
    ) -> SearchResponse:
        """Search users by username, full name, or bio"""
        search_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["username^3", "full_name^2", "bio"],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    }
                ],
                "filter": []
            }
        }
        
        if verified_only:
            search_query["bool"]["filter"].append({"term": {"is_verified": True}})
        
        # Sort configuration
        sort_config = []
        if sort_by == "followers":
            sort_config = [{"follower_count": {"order": "desc"}}, {"is_verified": {"order": "desc"}}]
        elif sort_by == "posts":
            sort_config = [{"post_count": {"order": "desc"}}, {"follower_count": {"order": "desc"}}]
        else:  # relevance
            sort_config = ["_score", {"follower_count": {"order": "desc"}}, {"is_verified": {"order": "desc"}}]
        
        response = client.search(
            index="users",
            body={
                "query": search_query,
                "sort": sort_config,
                "from": (page - 1) * size,
                "size": size
            }
        )
        
        return SearchResponse(
            total=response["hits"]["total"]["value"],
            page=page,
            size=size,
            results=[hit["_source"] for hit in response["hits"]["hits"]],
            took=response["took"]
        )
    
    @staticmethod
    async def search_hashtags(query: str, page: int = 1, size: int = 10, min_posts: int = 1) -> SearchResponse:
        """Search and suggest hashtags"""
        response = client.search(
            index="posts",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"wildcard": {"hashtags": f"*{query.lower()}*"}},
                            {"term": {"is_public": True}}
                        ]
                    }
                },
                "aggs": {
                    "hashtags": {
                        "terms": {
                            "field": "hashtags.keyword",
                            "size": size * 10,  # Get more for filtering
                            "include": f".*{query.lower()}.*",
                            "min_doc_count": min_posts
                        }
                    }
                },
                "size": 0
            }
        )
        
        hashtags = []
        if "aggregations" in response and "hashtags" in response["aggregations"]:
            for bucket in response["aggregations"]["hashtags"]["buckets"]:
                hashtags.append({
                    "name": bucket["key"],
                    "post_count": bucket["doc_count"]
                })
        
        # Apply pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_hashtags = hashtags[start_idx:end_idx]
        
        return SearchResponse(
            total=len(hashtags),
            page=page,
            size=size,
            results=paginated_hashtags,
            took=response["took"]
        )
    
    @staticmethod
    async def get_trending_hashtags(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending hashtags based on recent post activity"""
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
                "aggs": {
                    "trending_hashtags": {
                        "terms": {
                            "field": "hashtags.keyword",
                            "size": limit,
                            "order": {"_count": "desc"}
                        }
                    }
                },
                "size": 0
            }
        )
        
        hashtags = []
        if "aggregations" in response and "trending_hashtags" in response["aggregations"]:
            for bucket in response["aggregations"]["trending_hashtags"]["buckets"]:
                hashtags.append({
                    "name": bucket["key"],
                    "post_count": bucket["doc_count"]
                })
        
        return hashtags