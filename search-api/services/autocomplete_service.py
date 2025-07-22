from typing import List, Dict, Any
from config import client
from config.settings import MAX_AUTOCOMPLETE_RESULTS, AUTOCOMPLETE_MIN_CHARS
from models.search import AutoCompleteResponse, AutoCompleteItem, SearchSuggestionsResponse, SearchSuggestion

class AutoCompleteService:
    @staticmethod
    async def get_autocomplete_suggestions(query: str, types: List[str] = None) -> AutoCompleteResponse:
        """Get comprehensive auto-complete suggestions"""
        if len(query) < AUTOCOMPLETE_MIN_CHARS:
            return AutoCompleteResponse(suggestions=[], total=0, took=0)
        
        if types is None:
            types = ["users", "hashtags", "content", "locations"]
        
        suggestions = []
        total_took = 0
        
        # Get user suggestions
        if "users" in types:
            user_suggestions, took = await AutoCompleteService._get_user_suggestions(query)
            suggestions.extend(user_suggestions)
            total_took += took
        
        # Get hashtag suggestions
        if "hashtags" in types:
            hashtag_suggestions, took = await AutoCompleteService._get_hashtag_suggestions(query)
            suggestions.extend(hashtag_suggestions)
            total_took += took
        
        # Get content suggestions
        if "content" in types:
            content_suggestions, took = await AutoCompleteService._get_content_suggestions(query)
            suggestions.extend(content_suggestions)
            total_took += took
        
        # Get location suggestions
        if "locations" in types:
            location_suggestions, took = await AutoCompleteService._get_location_suggestions(query)
            suggestions.extend(location_suggestions)
            total_took += took
        
        # Sort by score and limit results
        suggestions.sort(key=lambda x: x.score, reverse=True)
        suggestions = suggestions[:MAX_AUTOCOMPLETE_RESULTS]
        
        return AutoCompleteResponse(
            suggestions=suggestions,
            total=len(suggestions),
            took=total_took
        )
    
    @staticmethod
    async def _get_user_suggestions(query: str) -> tuple[List[AutoCompleteItem], int]:
        """Get user auto-complete suggestions"""
        try:
            response = client.search(
                index="users",
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "username.autocomplete": {
                                            "query": query,
                                            "boost": 3.0
                                        }
                                    }
                                },
                                {
                                    "match": {
                                        "full_name.autocomplete": {
                                            "query": query,
                                            "boost": 2.0
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    "sort": [
                        "_score",
                        {"follower_count": {"order": "desc"}},
                        {"is_verified": {"order": "desc"}}
                    ],
                    "size": 10,
                    "_source": ["id", "username", "full_name", "is_verified", "follower_count", "profile_image_url"]
                }
            )
            
            suggestions = []
            for hit in response["hits"]["hits"]:
                user = hit["_source"]
                suggestions.append(AutoCompleteItem(
                    type="user",
                    value=f"@{user['username']}",
                    display_text=f"@{user['username']} ({user['full_name']})",
                    metadata={
                        "id": user["id"],
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "is_verified": user.get("is_verified", False),
                        "follower_count": user.get("follower_count", 0),
                        "profile_image_url": user.get("profile_image_url")
                    },
                    score=hit["_score"]
                ))
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting user suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def _get_hashtag_suggestions(query: str) -> tuple[List[AutoCompleteItem], int]:
        """Get hashtag auto-complete suggestions"""
        try:
            # Remove # if present
            clean_query = query.lstrip('#')
            
            response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"hashtags.autocomplete": clean_query}},
                                {"term": {"is_public": True}}
                            ]
                        }
                    },
                    "aggs": {
                        "hashtags": {
                            "terms": {
                                "field": "hashtags.keyword",
                                "size": 10,
                                "include": f".*{clean_query.lower()}.*",
                                "order": {"_count": "desc"}
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            suggestions = []
            if "aggregations" in response and "hashtags" in response["aggregations"]:
                for bucket in response["aggregations"]["hashtags"]["buckets"]:
                    hashtag = bucket["key"]
                    count = bucket["doc_count"]
                    suggestions.append(AutoCompleteItem(
                        type="hashtag",
                        value=f"#{hashtag}",
                        display_text=f"#{hashtag} ({count} posts)",
                        metadata={
                            "hashtag": hashtag,
                            "post_count": count
                        },
                        score=float(count)  # Use post count as score
                    ))
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting hashtag suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def _get_content_suggestions(query: str) -> tuple[List[AutoCompleteItem], int]:
        """Get content auto-complete suggestions"""
        try:
            response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"content.autocomplete": query}},
                                {"term": {"is_public": True}}
                            ]
                        }
                    },
                    "sort": [
                        "_score",
                        {"like_count": {"order": "desc"}},
                        {"created_at": {"order": "desc"}}
                    ],
                    "size": 5,
                    "_source": ["id", "content", "like_count", "comment_count", "user.username"],
                    "highlight": {
                        "fields": {
                            "content": {
                                "fragment_size": 100,
                                "number_of_fragments": 1
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            for hit in response["hits"]["hits"]:
                post = hit["_source"]
                content = post["content"]
                
                # Use highlighted content if available
                if "highlight" in hit and "content" in hit["highlight"]:
                    highlighted_content = hit["highlight"]["content"][0]
                    # Remove HTML tags for display
                    import re
                    display_content = re.sub(r'<[^>]+>', '', highlighted_content)
                else:
                    display_content = content[:100] + "..." if len(content) > 100 else content
                
                suggestions.append(AutoCompleteItem(
                    type="content",
                    value=content,
                    display_text=f"{display_content} - @{post.get('user', {}).get('username', 'unknown')}",
                    metadata={
                        "post_id": post["id"],
                        "like_count": post.get("like_count", 0),
                        "comment_count": post.get("comment_count", 0),
                        "username": post.get("user", {}).get("username")
                    },
                    score=hit["_score"]
                ))
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting content suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def _get_location_suggestions(query: str) -> tuple[List[AutoCompleteItem], int]:
        """Get location auto-complete suggestions"""
        try:
            response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"location.autocomplete": query}},
                                {"term": {"is_public": True}},
                                {"exists": {"field": "location"}}
                            ]
                        }
                    },
                    "aggs": {
                        "locations": {
                            "terms": {
                                "field": "location.keyword",
                                "size": 10,
                                "include": f".*{query.lower()}.*",
                                "order": {"_count": "desc"}
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            suggestions = []
            if "aggregations" in response and "locations" in response["aggregations"]:
                for bucket in response["aggregations"]["locations"]["buckets"]:
                    location = bucket["key"]
                    count = bucket["doc_count"]
                    suggestions.append(AutoCompleteItem(
                        type="location",
                        value=location,
                        display_text=f"📍 {location} ({count} posts)",
                        metadata={
                            "location": location,
                            "post_count": count
                        },
                        score=float(count)
                    ))
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting location suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def get_search_suggestions(query: str) -> SearchSuggestionsResponse:
        """Get search query suggestions based on popular searches"""
        try:
            # This could be enhanced with a dedicated suggestions index
            # For now, we'll use content and hashtag data
            suggestions = []
            
            # Get popular hashtags that match
            hashtag_response = client.search(
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
                        "popular_hashtags": {
                            "terms": {
                                "field": "hashtags.keyword",
                                "size": 5,
                                "include": f".*{query.lower()}.*"
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            if "aggregations" in hashtag_response:
                for bucket in hashtag_response["aggregations"]["popular_hashtags"]["buckets"]:
                    suggestions.append(SearchSuggestion(
                        text=bucket["key"],
                        highlighted=bucket["key"],
                        score=float(bucket["doc_count"]),
                        type="hashtag"
                    ))
            
            return SearchSuggestionsResponse(
                suggestions=suggestions,
                total=len(suggestions),
                took=hashtag_response["took"]
            )
        except Exception as e:
            print(f"Error getting search suggestions: {e}")
            return SearchSuggestionsResponse(suggestions=[], total=0, took=0)