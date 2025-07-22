from typing import List, Dict, Any
from config.opensearch import client
from config.settings import MAX_AUTOCOMPLETE_RESULTS, AUTOCOMPLETE_MIN_CHARS
from models import AutoCompleteItem, AutoCompleteResponse, SearchSuggestion, SearchSuggestionsResponse
import re
import difflib

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
    
    @staticmethod
    async def get_typo_tolerant_suggestions(query: str, limit: int = 10) -> AutoCompleteResponse:
        """Get typo-tolerant autocomplete suggestions with related terms"""
        try:
            all_suggestions = []
            total_took = 0
            
            # 1. Fuzzy search for content terms
            content_suggestions, content_took = await AutoCompleteService._get_fuzzy_content_suggestions(query, limit//4)
            all_suggestions.extend(content_suggestions)
            total_took += content_took
            
            # 2. Fuzzy search for hashtags
            hashtag_suggestions, hashtag_took = await AutoCompleteService._get_fuzzy_hashtag_suggestions(query, limit//4)
            all_suggestions.extend(hashtag_suggestions)
            total_took += hashtag_took
            
            # 3. Fuzzy search for users
            user_suggestions, user_took = await AutoCompleteService._get_fuzzy_user_suggestions(query, limit//4)
            all_suggestions.extend(user_suggestions)
            total_took += user_took
            
            # 4. Get related terms based on semantic similarity
            related_suggestions, related_took = await AutoCompleteService._get_related_term_suggestions(query, limit//4)
            all_suggestions.extend(related_suggestions)
            total_took += related_took
            
            # Sort all suggestions by score and limit
            all_suggestions.sort(key=lambda x: x.score, reverse=True)
            all_suggestions = all_suggestions[:limit]
            
            return AutoCompleteResponse(
                suggestions=all_suggestions,
                total=len(all_suggestions),
                took=total_took
            )
        except Exception as e:
            print(f"Error getting typo-tolerant suggestions: {e}")
            return AutoCompleteResponse(suggestions=[], total=0, took=0)
    
    @staticmethod
    async def _get_fuzzy_content_suggestions(query: str, limit: int) -> tuple[List[AutoCompleteItem], int]:
        """Get fuzzy content suggestions with typo tolerance"""
        try:
            response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["content^2", "content.autocomplete"],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO",
                                        "prefix_length": 1,
                                        "max_expansions": 50
                                    }
                                },
                                {"term": {"is_public": True}}
                            ]
                        }
                    },
                    "sort": [
                        "_score",
                        {"like_count": {"order": "desc"}}
                    ],
                    "size": limit,
                    "_source": ["content", "like_count", "user.username"],
                    "highlight": {
                        "fields": {
                            "content": {
                                "fragment_size": 50,
                                "number_of_fragments": 1
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            seen_content = set()
            
            for hit in response["hits"]["hits"]:
                content = hit["_source"]["content"]
                # Extract relevant words from content
                words = re.findall(r'\b\w+\b', content.lower())
                
                for word in words:
                    if len(word) >= 3 and word not in seen_content and difflib.SequenceMatcher(None, query.lower(), word).ratio() > 0.6:
                        seen_content.add(word)
                        
                        # Use highlighted content if available
                        display_text = word
                        if "highlight" in hit and "content" in hit["highlight"]:
                            highlighted = hit["highlight"]["content"][0]
                            if word in highlighted.lower():
                                display_text = highlighted
                        
                        suggestions.append(AutoCompleteItem(
                            type="content_term",
                            value=word,
                            display_text=f"'{word}' in posts",
                            metadata={
                                "similarity": difflib.SequenceMatcher(None, query.lower(), word).ratio(),
                                "like_count": hit["_source"].get("like_count", 0)
                            },
                            score=hit["_score"]
                        ))
                        
                        if len(suggestions) >= limit:
                            break
                
                if len(suggestions) >= limit:
                    break
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting fuzzy content suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def _get_fuzzy_hashtag_suggestions(query: str, limit: int) -> tuple[List[AutoCompleteItem], int]:
        """Get fuzzy hashtag suggestions with typo tolerance"""
        try:
            response = client.search(
                index="posts",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["hashtags^2", "hashtags.autocomplete"],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO",
                                        "prefix_length": 1
                                    }
                                },
                                {"term": {"is_public": True}}
                            ]
                        }
                    },
                    "aggs": {
                        "fuzzy_hashtags": {
                            "terms": {
                                "field": "hashtags.keyword",
                                "size": limit * 2,
                                "order": {"_count": "desc"}
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            suggestions = []
            if "aggregations" in response and "fuzzy_hashtags" in response["aggregations"]:
                for bucket in response["aggregations"]["fuzzy_hashtags"]["buckets"]:
                    hashtag = bucket["key"]
                    similarity = difflib.SequenceMatcher(None, query.lower(), hashtag.lower()).ratio()
                    
                    if similarity > 0.4:  # Threshold for similarity
                        suggestions.append(AutoCompleteItem(
                            type="hashtag",
                            value=f"#{hashtag}",
                            display_text=f"#{hashtag} ({bucket['doc_count']} posts)",
                            metadata={
                                "hashtag": hashtag,
                                "post_count": bucket["doc_count"],
                                "similarity": similarity
                            },
                            score=float(bucket["doc_count"]) * similarity
                        ))
                
                # Sort by score (combination of popularity and similarity)
                suggestions.sort(key=lambda x: x.score, reverse=True)
                suggestions = suggestions[:limit]
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting fuzzy hashtag suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def _get_fuzzy_user_suggestions(query: str, limit: int) -> tuple[List[AutoCompleteItem], int]:
        """Get fuzzy user suggestions with typo tolerance"""
        try:
            response = client.search(
                index="users",
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["username^3", "username.autocomplete^2", "full_name", "full_name.autocomplete"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "prefix_length": 1
                        }
                    },
                    "sort": [
                        "_score",
                        {"follower_count": {"order": "desc"}},
                        {"is_verified": {"order": "desc"}}
                    ],
                    "size": limit,
                    "_source": ["username", "full_name", "is_verified", "follower_count"]
                }
            )
            
            suggestions = []
            for hit in response["hits"]["hits"]:
                user = hit["_source"]
                username = user["username"]
                full_name = user.get("full_name", "")
                
                # Calculate similarity
                username_similarity = difflib.SequenceMatcher(None, query.lower(), username.lower()).ratio()
                name_similarity = difflib.SequenceMatcher(None, query.lower(), full_name.lower()).ratio() if full_name else 0
                max_similarity = max(username_similarity, name_similarity)
                
                display_name = full_name if full_name else username
                verified_badge = " ✓" if user.get("is_verified") else ""
                
                suggestions.append(AutoCompleteItem(
                    type="user",
                    value=username,
                    display_text=f"@{username} - {display_name}{verified_badge}",
                    metadata={
                        "username": username,
                        "full_name": full_name,
                        "is_verified": user.get("is_verified", False),
                        "follower_count": user.get("follower_count", 0),
                        "similarity": max_similarity
                    },
                    score=hit["_score"] * max_similarity
                ))
            
            return suggestions, response["took"]
        except Exception as e:
            print(f"Error getting fuzzy user suggestions: {e}")
            return [], 0
    
    @staticmethod
    async def _get_related_term_suggestions(query: str, limit: int) -> tuple[List[AutoCompleteItem], int]:
        """Get related term suggestions based on co-occurrence and semantic similarity"""
        try:
            # Define related terms mapping for common queries
            related_terms_map = {
                "dev": ["developer", "programming", "coding", "software", "web", "tech", "javascript", "python", "react"],
                "developer": ["dev", "programming", "coding", "software", "engineer", "tech", "web"],
                "programming": ["coding", "dev", "developer", "software", "tech", "javascript", "python", "java"],
                "web": ["website", "frontend", "backend", "html", "css", "javascript", "react", "vue", "angular"],
                "tech": ["technology", "dev", "programming", "software", "startup", "innovation"],
                "food": ["cooking", "recipe", "restaurant", "chef", "cuisine", "meal", "dinner", "lunch"],
                "travel": ["vacation", "trip", "journey", "adventure", "explore", "tourism", "destination"],
                "music": ["song", "artist", "album", "concert", "band", "musician", "melody", "rhythm"],
                "fitness": ["workout", "exercise", "gym", "health", "training", "sport", "running", "yoga"],
                "business": ["startup", "entrepreneur", "marketing", "sales", "finance", "company", "corporate"]
            }
            
            suggestions = []
            query_lower = query.lower()
            
            # Find direct matches and related terms
            related_terms = set()
            
            # Check for exact matches
            if query_lower in related_terms_map:
                related_terms.update(related_terms_map[query_lower])
            
            # Check for partial matches
            for key, terms in related_terms_map.items():
                if query_lower in key or key in query_lower:
                    related_terms.update(terms)
                    related_terms.add(key)
                
                # Check if query matches any related term
                for term in terms:
                    if query_lower in term or term in query_lower:
                        related_terms.update(terms)
                        related_terms.add(key)
                        break
            
            # Remove the original query from related terms
            related_terms.discard(query_lower)
            
            # Get popularity scores for related terms from actual content
            if related_terms:
                for term in list(related_terms)[:limit]:
                    try:
                        # Search for posts containing this term
                        term_response = client.search(
                            index="posts",
                            body={
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"content": term}},
                                            {"term": {"is_public": True}}
                                        ]
                                    }
                                },
                                "size": 0
                            }
                        )
                        
                        post_count = term_response["hits"]["total"]["value"]
                        if post_count > 0:
                            similarity = difflib.SequenceMatcher(None, query_lower, term).ratio()
                            suggestions.append(AutoCompleteItem(
                                type="related_term",
                                value=term,
                                display_text=f"'{term}' (related to '{query}')",
                                metadata={
                                    "original_query": query,
                                    "post_count": post_count,
                                    "similarity": similarity,
                                    "relation_type": "semantic"
                                },
                                score=float(post_count) * (1 + similarity)
                            ))
                    except:
                        continue
            
            # Sort by score and limit results
            suggestions.sort(key=lambda x: x.score, reverse=True)
            suggestions = suggestions[:limit]
            
            return suggestions, 50  # Estimated time
        except Exception as e:
            print(f"Error getting related term suggestions: {e}")
            return [], 0