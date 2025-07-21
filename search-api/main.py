from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from opensearchpy import OpenSearch
from datetime import datetime
import json
import os
import asyncio
import threading
from contextlib import asynccontextmanager
from kafka_consumer import CDCProcessor

# Configuration
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', '9200'))

# OpenSearch client
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

# Pydantic models
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

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    results: List[Dict[str, Any]]
    took: int
    aggregations: Optional[Dict[str, Any]] = None

class HashtagStats(BaseModel):
    name: str
    post_count: int
    recent_posts: List[Post]

# Global variable to hold the consumer thread
consumer_thread = None
cdc_processor = None

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_thread, cdc_processor
    
    # Startup: Create indices if they don't exist
    await create_indices()
    
    # Start Kafka consumer in background thread
    try:
        cdc_processor = CDCProcessor()
        consumer_thread = threading.Thread(target=cdc_processor.run, daemon=True)
        consumer_thread.start()
        print("Started Kafka consumer thread")
    except Exception as e:
        print(f"Failed to start Kafka consumer: {e}")
    
    yield
    
    # Shutdown: cleanup if needed
    if cdc_processor and hasattr(cdc_processor, 'consumer') and cdc_processor.consumer:
        cdc_processor.consumer.close()
        print("Closed Kafka consumer")

# FastAPI app
app = FastAPI(
    title="Social Media Search API",
    description="Search API for social media posts, users, and hashtags using OpenSearch",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Index configurations
INDICES_CONFIG = {
    "posts": {
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "user_id": {"type": "long"},
                "content": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "hashtags": {"type": "keyword"},
                "mentions": {"type": "keyword"},
                "like_count": {"type": "integer"},
                "comment_count": {"type": "integer"},
                "share_count": {"type": "integer"},
                "is_public": {"type": "boolean"},
                "location": {"type": "text"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "user": {
                    "properties": {
                        "id": {"type": "long"},
                        "username": {"type": "keyword"},
                        "full_name": {"type": "text"},
                        "is_verified": {"type": "boolean"}
                    }
                }
            }
        }
    },
    "users": {
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "username": {"type": "keyword"},
                "email": {"type": "keyword"},
                "full_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "bio": {"type": "text"},
                "is_verified": {"type": "boolean"},
                "follower_count": {"type": "integer"},
                "following_count": {"type": "integer"},
                "post_count": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
    },
    "comments": {
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "post_id": {"type": "long"},
                "user_id": {"type": "long"},
                "parent_comment_id": {"type": "long"},
                "content": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "like_count": {"type": "integer"},
                "reply_count": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "user": {
                    "properties": {
                        "id": {"type": "long"},
                        "username": {"type": "keyword"},
                        "full_name": {"type": "text"}
                    }
                }
            }
        }
    }
}

async def create_indices():
    """Create OpenSearch indices if they don't exist"""
    for index_name, config in INDICES_CONFIG.items():
        try:
            if not client.indices.exists(index=index_name):
                client.indices.create(index=index_name, body=config)
                print(f"Created index: {index_name}")
            else:
                print(f"Index already exists: {index_name}")
        except Exception as e:
            print(f"Error creating index {index_name}: {e}")

# Health check
@app.get("/health")
async def health_check():
    try:
        info = client.info()
        return {"status": "healthy", "opensearch": info}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OpenSearch unavailable: {str(e)}")

# Search endpoints
@app.get("/search/posts", response_model=SearchResponse)
async def search_posts(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Results per page"),
    hashtag: Optional[str] = Query(None, description="Filter by hashtag"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    sort_by: str = Query("relevance", description="Sort by: relevance, created_at, like_count")
):
    """Search posts with full-text search and filters"""
    try:
        # Build query
        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": q,
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
        if hashtag:
            query["bool"]["filter"].append({"term": {"hashtags": hashtag}})
        if user_id:
            query["bool"]["filter"].append({"term": {"user_id": user_id}})
        
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
                "query": query,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/search/users", response_model=SearchResponse)
async def search_users(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Results per page"),
    verified_only: bool = Query(False, description="Show only verified users")
):
    """Search users by username, full name, or bio"""
    try:
        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": q,
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
            query["bool"]["filter"].append({"term": {"is_verified": True}})
        
        response = client.search(
            index="users",
            body={
                "query": query,
                "sort": [
                    "_score",
                    {"follower_count": {"order": "desc"}},
                    {"is_verified": {"order": "desc"}}
                ],
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/search/hashtags")
async def search_hashtags(
    q: str = Query(..., description="Hashtag search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Search and suggest hashtags"""
    try:
        # Search for hashtags in posts
        response = client.search(
            index="posts",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"wildcard": {"hashtags": f"*{q.lower()}*"}},
                            {"term": {"is_public": True}}
                        ]
                    }
                },
                "aggs": {
                    "hashtags": {
                        "terms": {
                            "field": "hashtags.keyword",
                            "size": limit,
                            "include": f".*{q.lower()}.*"
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
        
        return {"hashtags": hashtags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/trending/hashtags")
async def trending_hashtags(
    limit: int = Query(10, ge=1, le=50, description="Number of trending hashtags")
):
    """Get trending hashtags based on recent post activity"""
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
                                        "gte": "now-7d"
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
        
        return {"trending_hashtags": hashtags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/hashtags/trending")
async def hashtags_trending(
    limit: int = Query(10, ge=1, le=50, description="Number of trending hashtags")
):
    """Get trending hashtags (alternative endpoint for compatibility)"""
    return await trending_hashtags(limit)

@app.get("/analytics/posts")
async def post_analytics(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
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
                    }
                },
                "size": 0
            }
        )
        
        return {
            "analytics": response["aggregations"],
            "total_posts": response["hits"]["total"]["value"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)