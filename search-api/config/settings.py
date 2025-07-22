import os
from typing import List

# OpenSearch Configuration
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', '9200'))
OPENSEARCH_USE_SSL = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
OPENSEARCH_VERIFY_CERTS = os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
OPENSEARCH_USERNAME = os.getenv('OPENSEARCH_USERNAME', '')
OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_PASSWORD', '')

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC_POSTS = os.getenv('KAFKA_TOPIC_POSTS', 'social.posts')
KAFKA_TOPIC_USERS = os.getenv('KAFKA_TOPIC_USERS', 'social.users')
KAFKA_TOPIC_COMMENTS = os.getenv('KAFKA_TOPIC_COMMENTS', 'social.comments')
KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_CONSUMER_GROUP', 'search-api-consumer')

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_WORKERS = int(os.getenv('API_WORKERS', '4'))

# CORS Configuration
CORS_ORIGINS_STR = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000')
CORS_ORIGINS: List[str] = [origin.strip() for origin in CORS_ORIGINS_STR.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'

# Application Settings
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')

# Search Configuration
DEFAULT_PAGE_SIZE = int(os.getenv('SEARCH_DEFAULT_SIZE', '20'))
MAX_PAGE_SIZE = int(os.getenv('SEARCH_MAX_SIZE', '100'))
MAX_AUTOCOMPLETE_RESULTS = int(os.getenv('AUTOCOMPLETE_MAX_SUGGESTIONS', '10'))
AUTOCOMPLETE_MIN_CHARS = int(os.getenv('AUTOCOMPLETE_MIN_CHARS', '2'))

# Cache Configuration
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
TRENDING_CACHE_TTL = 900  # 15 minutes
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'

# Analytics Configuration
ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
TRENDING_WINDOW_HOURS = int(os.getenv('TRENDING_WINDOW_HOURS', '24'))
TRENDING_MIN_ENGAGEMENT = int(os.getenv('TRENDING_MIN_ENGAGEMENT', '10'))

# Health Check Configuration
HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', '30'))
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))