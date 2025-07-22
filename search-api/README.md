# Social Media Search API

A high-performance search API with advanced autocomplete functionality for social media platforms, built with FastAPI and OpenSearch.

## Features

### 🔍 Advanced Search
- **Full-text search** for posts, users, and hashtags
- **Multi-field search** with relevance scoring
- **Advanced filtering** by hashtags, users, verification status
- **Flexible sorting** by relevance, date, engagement metrics
- **Pagination** support for large result sets
- **Search highlighting** for better user experience

### ⚡ Real-time Autocomplete
- **Multi-type suggestions**: users, hashtags, content, locations
- **Real-time suggestions** as users type
- **Intelligent scoring** based on popularity and relevance
- **Mention suggestions** for @username completion
- **Hashtag suggestions** for #hashtag completion
- **Content suggestions** for post discovery
- **Configurable suggestion limits** and minimum character requirements

### 📊 Analytics & Insights
- **Trending hashtags** with time-based analysis
- **Engagement metrics** and post analytics
- **User analytics** with detailed insights
- **Time-series data** for trend analysis
- **Popular content discovery**

### 🔄 Real-time Data Processing
- **Kafka CDC integration** for real-time data updates
- **Automatic index synchronization**
- **Event-driven architecture**
- **Scalable data processing**

## Project Structure

```
search-api/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── config/                # Configuration modules
│   ├── __init__.py       # Configuration exports
│   ├── settings.py       # Application settings
│   └── opensearch.py     # OpenSearch configuration
├── models/               # Pydantic data models
│   ├── __init__.py      # Model exports
│   ├── user.py          # User models
│   ├── post.py          # Post models
│   ├── comment.py       # Comment models
│   ├── search.py        # Search response models
│   └── hashtag.py       # Hashtag models
├── services/            # Business logic services
│   ├── __init__.py     # Service exports
│   ├── search_service.py        # Core search functionality
│   ├── autocomplete_service.py  # Autocomplete logic
│   └── analytics_service.py     # Analytics and insights
├── routes/              # API route handlers
│   ├── __init__.py     # Route exports
│   ├── search_routes.py        # Search endpoints
│   ├── autocomplete_routes.py  # Autocomplete endpoints
│   ├── analytics_routes.py     # Analytics endpoints
│   └── health_routes.py        # Health check endpoints
└── kafka_consumer.py    # CDC event processing
```

## Installation

### Prerequisites
- Python 3.8+
- OpenSearch 2.0+
- Apache Kafka 2.8+

### Setup

1. **Clone and navigate to the project**:
   ```bash
   cd /Users/devnla/dev/cdc-pipeline/search-api
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional):
   ```bash
   export OPENSEARCH_HOST=localhost
   export OPENSEARCH_PORT=9200
   export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   ```

5. **Start the application**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Health Check
- `GET /health` - Basic health check
- `GET /health/simple` - Simple status check
- `GET /health/detailed` - Comprehensive system status

### Search Endpoints
- `GET /search/posts` - Search posts with filtering and sorting
- `GET /search/users` - Search users by username, name, or bio
- `GET /search/hashtags` - Search hashtags with post counts
- `GET /trending/hashtags` - Get trending hashtags

### Autocomplete Endpoints
- `GET /autocomplete/suggestions` - Multi-type autocomplete suggestions
- `GET /autocomplete/users` - User-specific suggestions
- `GET /autocomplete/hashtags` - Hashtag suggestions
- `GET /autocomplete/content` - Content suggestions
- `GET /autocomplete/mentions` - @mention suggestions
- `GET /autocomplete/search-suggestions` - Search query suggestions

### Analytics Endpoints
- `GET /analytics/posts` - Post analytics and metrics
- `GET /analytics/users/{user_id}` - User-specific analytics
- `GET /analytics/trending` - Trending content analysis
- `GET /analytics/engagement-summary` - Engagement summary

## Usage Examples

### Basic Search
```bash
# Search posts
curl "http://localhost:8000/search/posts?q=machine%20learning&sort_by=likes&page=1&size=10"

# Search users
curl "http://localhost:8000/search/users?q=john&verified_only=true"

# Search hashtags
curl "http://localhost:8000/search/hashtags?q=tech&min_posts=5"
```

### Autocomplete
```bash
# Get autocomplete suggestions
curl "http://localhost:8000/autocomplete/suggestions?q=mach&types=users,hashtags,content&limit=5"

# Get user suggestions for mentions
curl "http://localhost:8000/autocomplete/mentions?q=john&limit=10"

# Get hashtag suggestions
curl "http://localhost:8000/autocomplete/hashtags?q=tech&limit=8"
```

### Analytics
```bash
# Get trending hashtags
curl "http://localhost:8000/trending/hashtags?days=7&limit=10"

# Get post analytics
curl "http://localhost:8000/analytics/posts?days=30"

# Get user analytics
curl "http://localhost:8000/analytics/users/123?days=30"
```

## Configuration

### OpenSearch Settings
- **Host**: `OPENSEARCH_HOST` (default: localhost)
- **Port**: `OPENSEARCH_PORT` (default: 9200)
- **Indices**: posts, users, comments with autocomplete mappings

### Autocomplete Settings
- **Max Results**: `MAX_AUTOCOMPLETE_RESULTS` (default: 10)
- **Min Characters**: `AUTOCOMPLETE_MIN_CHARS` (default: 2)
- **Cache TTL**: `AUTOCOMPLETE_CACHE_TTL` (default: 300 seconds)

### Search Settings
- **Max Page Size**: `MAX_SEARCH_SIZE` (default: 100)
- **Default Page Size**: `DEFAULT_SEARCH_SIZE` (default: 10)
- **Search Timeout**: `SEARCH_TIMEOUT_SECONDS` (default: 30)

## Development

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=.
```

### API Documentation
Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

## Architecture

### Modular Design
- **Separation of concerns** with dedicated modules for models, services, and routes
- **Service layer** for business logic abstraction
- **Configuration management** for environment-specific settings
- **Type safety** with Pydantic models and type hints

### Performance Features
- **Async/await** for non-blocking operations
- **Connection pooling** for OpenSearch
- **Efficient indexing** with optimized mappings
- **Caching strategies** for frequently accessed data

### Scalability
- **Horizontal scaling** support
- **Load balancer friendly**
- **Stateless design**
- **Event-driven architecture** with Kafka

## Contributing

1. Follow the existing code structure and patterns
2. Add type hints for all functions and methods
3. Write tests for new functionality
4. Update documentation for API changes
5. Use meaningful commit messages

## License

This project is part of the CDC Pipeline system for social media data processing.