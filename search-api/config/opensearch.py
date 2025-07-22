from opensearchpy import OpenSearch
from .settings import OPENSEARCH_HOST, OPENSEARCH_PORT

# OpenSearch client
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

# Enhanced index configurations with auto-complete support
INDICES_CONFIG = {
    "posts": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "autocomplete": {
                        "tokenizer": "autocomplete",
                        "filter": ["lowercase"]
                    },
                    "autocomplete_search": {
                        "tokenizer": "lowercase"
                    }
                },
                "tokenizer": {
                    "autocomplete": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 10,
                        "token_chars": ["letter", "digit"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "user_id": {"type": "long"},
                "content": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
                "hashtags": {
                    "type": "keyword",
                    "fields": {
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
                "mentions": {
                    "type": "keyword",
                    "fields": {
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
                "like_count": {"type": "integer"},
                "comment_count": {"type": "integer"},
                "share_count": {"type": "integer"},
                "is_public": {"type": "boolean"},
                "location": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "user": {
                    "properties": {
                        "id": {"type": "long"},
                        "username": {
                            "type": "keyword",
                            "fields": {
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "autocomplete_search"
                                }
                            }
                        },
                        "full_name": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"},
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "autocomplete_search"
                                }
                            }
                        },
                        "is_verified": {"type": "boolean"}
                    }
                }
            }
        }
    },
    "users": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "autocomplete": {
                        "tokenizer": "autocomplete",
                        "filter": ["lowercase"]
                    },
                    "autocomplete_search": {
                        "tokenizer": "lowercase"
                    }
                },
                "tokenizer": {
                    "autocomplete": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 10,
                        "token_chars": ["letter", "digit"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "username": {
                    "type": "keyword",
                    "fields": {
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
                "email": {"type": "keyword"},
                "full_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
                "bio": {
                    "type": "text",
                    "fields": {
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
                },
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
                    "analyzer": "standard",
                    "fields": {
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        }
                    }
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