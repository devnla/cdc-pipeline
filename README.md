# Enhanced Social Media CDC Pipeline

A complete Change Data Capture (CDC) pipeline for a social media application that captures real-time changes from MySQL and makes them searchable through OpenSearch with a FastAPI search service. Features enhanced data generation, automated setup, and comprehensive monitoring.

## 🏗️ Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   MySQL     │───▶│   Debezium   │───▶│    Kafka    │───▶│ Kafka Consumer│───▶│ OpenSearch  │
│ (Social DB) │    │  Connector   │    │   Topics    │    │   Service     │    │   Indices   │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
                                                                   │
                                                                   ▼
                                                           ┌──────────────┐
                                                           │   FastAPI    │
                                                           │ Search API   │
                                                           └──────────────┘
```

### Components

1. **MySQL Database**: Stores social media data (users, posts, comments, likes, follows)
2. **Debezium**: Captures changes from MySQL binlog and publishes to Kafka
3. **Apache Kafka**: Message broker for streaming CDC events
4. **Kafka Consumer**: Processes CDC events and indexes data to OpenSearch
5. **OpenSearch**: Search engine for real-time search capabilities
6. **FastAPI**: REST API for searching posts, users, and hashtags

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 8GB RAM available for Docker
- Ports 3306, 8000, 8080, 8083, 9092, 9200, 5601 available
- Python 3.8+ (for monitoring and testing tools)

### 1. Automated Setup (Recommended)

```bash
# Run the automated setup script
python auto_setup.py

# Or check status only
python auto_setup.py --check-only
```

The automated setup will:
- Check and start Docker services
- Fix MySQL permissions for Debezium
- Restart Kafka Connect
- Register the Debezium MySQL connector
- Create OpenSearch indices with mappings
- Verify UI availability (Kafka UI, OpenSearch Dashboards)

### 2. Manual Setup (Alternative)

```bash
# Make scripts executable
chmod +x setup.sh monitor.py test_pipeline.py data_generator.py

# Start the entire pipeline
./setup.sh setup
```

### 3. Verify the Setup

```bash
# Check service status
./setup.sh status

# Run comprehensive health check
python monitor.py --detailed

# Run end-to-end tests
python test_pipeline.py --detailed
```

### 2. Initialize Database (Optional)

```bash
# Initialize with foundational data for better testing
python data_generator.py --mode init --users 50 --posts-per-user 3
```

### 3. Access Services

Once setup is complete, you can access:

- **Web UI**: http://localhost:3000 (Modern search interface)
- **FastAPI Search API**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:8080
- **OpenSearch Dashboards**: http://localhost:5601
- **OpenSearch API**: http://localhost:9200
- **Kafka Connect API**: http://localhost:8083

## 📊 Database Schema

The social media database includes:

### Core Tables
- `users` - User profiles and metadata
- `posts` - Social media posts with content, hashtags, mentions
- `comments` - Comments on posts (with threading support)
- `likes` - Likes on posts and comments
- `follows` - User follow relationships
- `hashtags` - Hashtag management
- `post_hashtags` - Many-to-many relationship between posts and hashtags

### Sample Data
The system comes with sample users, posts, comments, and relationships to demonstrate the CDC pipeline.

## 🔍 Search API Endpoints

### Posts Search
```bash
# Search posts by content
curl "http://localhost:8000/search/posts?q=technology&size=10"

# Search with filters
curl "http://localhost:8000/search/posts?q=AI&hashtag=technology&sort_by=like_count"
```

### Users Search
```bash
# Search users by name or username
curl "http://localhost:8000/search/users?q=john&verified_only=true"
```

### Hashtags
```bash
# Search hashtags
curl "http://localhost:8000/search/hashtags?q=tech&limit=10"

# Get trending hashtags
curl "http://localhost:8000/trending/hashtags?limit=20"
```

### Analytics
```bash
# Get post analytics
curl "http://localhost:8000/analytics/posts?days=30"

# User-specific analytics
curl "http://localhost:8000/analytics/posts?user_id=1&days=7"
```

## 🌐 Web UI

A modern, Facebook-like web interface for searching and browsing social media content.

### Features
- **Search Interface**: Real-time search with auto-suggestions
- **Navigation Tabs**: Filter by All, Users, or Posts
- **Hashtag Support**: Clickable hashtags that trigger searches
- **Post Display**: Shows reactions, comments, and engagement metrics
- **User Profiles**: Display user information and verification status
- **Responsive Design**: Mobile-friendly interface
- **Interactive Elements**: Modal views for detailed post information

### Access the Web UI

**Development Mode:**
```bash
# Start the web server (if not using Docker)
cd web-ui
python -m http.server 3000
# Access at http://localhost:3000
```

**Docker Mode:**
```bash
# Build and start with Docker Compose
docker-compose up web-ui
# Access at http://localhost:3000
```

### Web UI Architecture
- **Frontend**: Pure HTML, CSS, and JavaScript
- **Styling**: Modern CSS with animations and responsive design
- **API Integration**: Connects to FastAPI search endpoints
- **Docker**: Nginx-based container for production deployment

## 📊 Enhanced Data Generator

The data generator now includes database initialization and auto-incrementing ID support.

### New Features

**Database Initialization Mode:**
```bash
# Initialize database with foundational data
python data_generator.py --mode init --users 100 --posts-per-user 5
```

**Auto-incrementing IDs:**
- Users and posts now use proper auto-incrementing primary keys
- Ensures data consistency and proper relationships
- Supports bulk operations with correct ID management

**Enhanced User Creation:**
```bash
# Create users with realistic profiles
python data_generator.py --mode bulk --count 50 --data-type users
```

**Improved Post Generation:**
```bash
# Generate posts with proper user relationships
python data_generator.py --mode bulk --count 200 --data-type posts
```

### Data Generator Modes

1. **init**: Initialize database with foundational users and posts
2. **burst**: Generate random activities for a specified duration
3. **bulk**: Generate large amounts of specific data types
4. **trending**: Create trending content with popular hashtags
5. **viral**: Simulate viral posts with high engagement
6. **continuous**: Generate ongoing activity at regular intervals
7. **single**: Generate individual items for testing

## 🔧 Configuration

### Debezium Connector
The Debezium MySQL connector is configured in `debezium-mysql-connector.json` with:
- Captures changes from all social media tables
- Uses JSON format for Kafka messages
- Includes metadata like operation type and timestamp
- Handles schema changes gracefully

### OpenSearch Indices
Three main indices are created:
- `posts` - For searching post content, hashtags, mentions
- `users` - For searching user profiles
- `comments` - For searching comment content

### Kafka Topics
Debezium creates topics for each table:
- `dbserver1.socialmedia.users`
- `dbserver1.socialmedia.posts`
- `dbserver1.socialmedia.comments`
- `dbserver1.socialmedia.likes`
- `dbserver1.socialmedia.follows`

## 🧪 Testing the Pipeline

### 1. Insert Test Data
```bash
# Connect to MySQL and insert a new post
docker-compose exec mysql mysql -u dbuser -pdbpassword socialmedia

INSERT INTO posts (user_id, content, hashtags, is_public) 
VALUES (1, 'Real-time CDC test! 🚀', JSON_ARRAY('#realtime', '#cdc'), TRUE);
```

### 2. Verify in OpenSearch
```bash
# Search for the new post
curl "http://localhost:8000/search/posts?q=Real-time%20CDC%20test"
```

### 3. Monitor CDC Events
- View Kafka messages in Kafka UI: http://localhost:8080
- Check Debezium connector status: http://localhost:8083/connectors
- Monitor OpenSearch indices: http://localhost:5601

## 📈 Performance Considerations

### MySQL Configuration
- Binary logging enabled with row-based replication
- Optimized for CDC with minimal locking
- Proper indexing on frequently queried columns

### Kafka Configuration
- Single partition for simplicity (scale as needed)
- JSON serialization for human-readable messages
- Retention configured for development use

### OpenSearch Configuration
- Disabled security for development
- Optimized mappings for search performance
- Real-time refresh for immediate search availability

## 🔧 Management Commands

### Automated Setup Script (`auto_setup.py`)

Comprehensive automation for CDC pipeline setup:

```bash
# Full automated setup
python auto_setup.py

# Check status only (no changes)
python auto_setup.py --check-only
```

**Features:**
- Docker service health checks
- MySQL permission configuration for CDC
- Kafka Connect restart and connector registration
- OpenSearch index creation with proper mappings
- UI availability verification (Kafka UI, OpenSearch Dashboards)
- Comprehensive error handling and reporting

### Manual Setup Script (`setup.sh`)

Traditional setup script with management commands:

```bash
# Start all services
./setup.sh setup

# Stop and clean up
./setup.sh cleanup

# Restart services
./setup.sh restart

# Check service status
./setup.sh status

# View service logs
./setup.sh logs [service_name]

# Run basic tests
./setup.sh test
```

## Monitoring and Testing Tools

### Health Monitoring (`monitor.py`)

Comprehensive health monitoring for all pipeline components:

```bash
# Single health check with detailed output
./monitor.py --detailed

# Continuous monitoring (every 30 seconds)
./monitor.py --mode monitor

# Custom monitoring interval
./monitor.py --mode monitor --interval 60
```

**Features:**
- MySQL connectivity and CDC configuration validation
- Kafka Connect and Debezium connector status
- OpenSearch cluster health and indices verification
- Search API functionality testing
- Kafka topics monitoring
- Performance metrics and response times

### End-to-End Testing (`test_pipeline.py`)

Comprehensive test suite that validates the entire CDC pipeline:

```bash
# Run full test suite with detailed output
./test_pipeline.py --detailed

# Run tests without cleanup (for debugging)
./test_pipeline.py --no-cleanup
```

**Test Coverage:**
- Environment setup validation
- MySQL data insertion and CDC event capture
- Data propagation to OpenSearch
- Search API functionality
- Data consistency between MySQL and OpenSearch
- UPDATE operations and CDC propagation

### Enhanced Data Generation (`data_generator.py`)

Advanced data generation with multiple modes and performance tracking:

```bash
# Install dependencies
pip install -r generator-requirements.txt

# Activate virtual environment (recommended)
source venv/bin/activate
```

#### Generation Modes

**1. Burst Mode (Default)**
```bash
# Generate random activities for 60 seconds
python data_generator.py --mode burst --duration 60
```

**2. Bulk Generation**
```bash
# Generate 100 mixed items
python data_generator.py --mode bulk --count 100 --data-type mixed

# Generate 50 users
python data_generator.py --mode bulk --count 50 --data-type users

# Generate 200 posts
python data_generator.py --mode bulk --count 200 --data-type posts
```

**3. Trending Content**
```bash
# Generate trending posts with specific hashtags
python data_generator.py --mode trending --count 50 \
  --trending-hashtags '#ai' '#blockchain' '#innovation'
```

**4. Viral Post Simulation**
```bash
# Create a viral post with high engagement
python data_generator.py --mode viral
```

**5. Continuous Generation**
```bash
# Generate continuous activity every 5 seconds
python data_generator.py --mode continuous --interval 5
```

**6. Single Activity**
```bash
# Generate a single post
python data_generator.py --mode single --activity post
```

#### Performance Features
- **Performance Metrics**: Tracks operations per second, average operation time
- **Thread Safety**: Uses locks for concurrent operations
- **Bulk Operations**: Optimized for high-volume data generation
- **Realistic Data**: Uses Faker library for authentic social media content

## 🔍 Monitoring and Debugging

### Check Connector Status
```bash
curl http://localhost:8083/connectors/mysql-socialmedia-connector/status
```

### View Kafka Topics
```bash
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Monitor OpenSearch Health
```bash
curl http://localhost:9200/_cluster/health
curl http://localhost:9200/_cat/indices
```

### Check API Health
```bash
curl http://localhost:8000/health
```

## 🚨 Troubleshooting

### Common Issues

1. **Services fail to start**:
   ```bash
   # Check if ports are already in use
   lsof -i :3306 -i :9092 -i :9200 -i :8083 -i :8000
   
   # Check Docker resources
   docker system df
   docker system prune  # if needed
   
   # View service logs
   ./setup.sh logs [service_name]
   ```

2. **Connector fails to start**:
   ```bash
   # Check MySQL binlog configuration
   ./monitor.py --detailed  # Look for CDC configuration issues
   
   # Verify database permissions
   docker exec -it mysql mysql -u dbuser -p -e "SHOW GRANTS;"
   
   # Fix CDC permissions if needed (common issue)
   docker-compose exec mysql mysql -u root -prootpassword -e "GRANT RELOAD, FLUSH_TABLES ON *.* TO 'dbuser'@'%'; FLUSH PRIVILEGES;"
   
   # Check connector logs
   docker-compose logs kafka-connect
   
   # Restart connector after fixing permissions
   curl -X POST "localhost:8083/connectors/mysql-socialmedia-connector/restart"
   
   # Re-register connector if needed
   curl -X DELETE "localhost:8083/connectors/mysql-socialmedia-connector"
   ./setup.sh setup  # Will re-register
   ```

3. **Data not appearing in OpenSearch**:
   ```bash
   # Check if Kafka consumer is running
   docker-compose ps kafka-consumer
   
   # View consumer logs
   docker-compose logs kafka-consumer
   
   # Check Kafka topics and messages
   docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
   docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic dbserver1.socialmedia.posts --from-beginning --max-messages 5
   
   # Verify OpenSearch indices
   curl -X GET "localhost:9200/_cat/indices?v"
   curl -X GET "localhost:9200/posts/_search?size=1"
   ```

4. **Search API issues**:
   ```bash
   # Test API health
   curl -X GET "localhost:8000/health"
   
   # Check API logs
   docker-compose logs search-api
   
   # Test search functionality
   curl -X GET "localhost:8000/search/posts?q=test&size=5"
   
   # Verify OpenSearch connectivity from API
   docker exec -it search-api curl -X GET "opensearch:9200/_cluster/health"
   ```

5. **Performance issues**:
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check OpenSearch cluster health
   curl -X GET "localhost:9200/_cluster/health?pretty"
   
   # Monitor Kafka consumer lag
   docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group mysql-cdc-consumer
   
   # Adjust configurations if needed
   # Edit docker-compose.yml for memory limits
   # Edit debezium-mysql-connector.json for batch sizes
   ```

### Debug Commands

```bash
# Comprehensive health check
python monitor.py --detailed

# Run end-to-end tests
python test_pipeline.py --detailed

# Automated setup and health check
python auto_setup.py --check-only

# Check all Kafka topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# View recent Kafka messages
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic dbserver1.socialmedia.posts --from-beginning --max-messages 10

# Check OpenSearch indices and data
curl -X GET "localhost:9200/_cat/indices?v"
curl -X GET "localhost:9200/posts/_search?size=5&pretty"

# View connector status and configuration
curl -X GET "localhost:8083/connectors/mysql-socialmedia-connector/status" | jq
curl -X GET "localhost:8083/connectors/mysql-socialmedia-connector/config" | jq

# Test search API endpoints
curl -X GET "localhost:8000/health" | jq
curl -X GET "localhost:8000/search/posts?q=social&size=3" | jq
curl -X GET "localhost:8000/hashtags/trending" | jq

# Generate test data (various modes)
python data_generator.py --mode single
python data_generator.py --mode burst --duration 30
python data_generator.py --mode viral
```

### Recovery Procedures

1. **Complete reset**:
   ```bash
   ./setup.sh cleanup
   docker system prune -f
   ./setup.sh setup
   ```

2. **Reset only data**:
   ```bash
   # Stop services
   docker-compose down
   
   # Remove data volumes
   docker volume rm $(docker volume ls -q | grep test)
   
   # Restart
   ./setup.sh setup
   ```

3. **Restart specific service**:
   ```bash
   docker-compose restart [service_name]
   # e.g., docker-compose restart kafka-connect
   ```

### Log Locations
```bash
# Debezium/Kafka Connect logs
docker-compose logs kafka-connect

# Kafka consumer logs
docker-compose logs search-api

# MySQL logs
docker-compose logs mysql

# OpenSearch logs
docker-compose logs opensearch
```

## 🔧 Customization

### Adding New Tables
1. Update `table.include.list` in `debezium-mysql-connector.json`
2. Add corresponding index mapping in `search-api/main.py`
3. Update the Kafka consumer to handle new table events
4. Restart the connector

### Modifying Search Logic
- Edit search queries in `search-api/main.py`
- Adjust OpenSearch mappings for better search performance
- Add new search endpoints as needed

### Scaling Considerations
- Increase Kafka partitions for higher throughput
- Add more Kafka Connect workers
- Scale OpenSearch cluster
- Implement proper security and authentication

## 📚 References

- [Debezium MySQL Connector Documentation](https://debezium.io/documentation/reference/connectors/mysql.html)
- [OpenSearch Documentation](https://opensearch.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this CDC pipeline implementation.

## 📄 License

This project is open source and available under the MIT License.