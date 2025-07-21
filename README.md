# Social Media CDC Pipeline with MySQL, Debezium, Kafka, and OpenSearch

A complete Change Data Capture (CDC) pipeline for a social media application that captures real-time changes from MySQL and makes them searchable through OpenSearch with a FastAPI search service.

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

### 1. Clone and Setup

```bash
# Make scripts executable
chmod +x setup.sh monitor.py test_pipeline.py data_generator.py

# Start the entire pipeline
./setup.sh setup
```

The setup script will:
- Start all services (MySQL, Kafka, Debezium, OpenSearch, FastAPI)
- Configure the Debezium MySQL connector
- Start the Kafka consumer for OpenSearch indexing
- Insert sample data and verify the pipeline

### 2. Verify the Setup

```bash
# Check service status
./setup.sh status

# Run comprehensive health check
./monitor.py --detailed

# Run end-to-end tests
./test_pipeline.py --detailed
```

### 2. Access Services

Once setup is complete, you can access:

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

## 🛠️ Management Commands

The `setup.sh` script provides several management commands:

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

### Data Generation (`data_generator.py`)

Simulate real-time social media activity for testing:

```bash
# Install dependencies
pip install -r generator-requirements.txt

# Generate burst of activity
./data_generator.py --mode burst --count 50

# Continuous data generation
./data_generator.py --mode continuous --interval 5

# Single activity
./data_generator.py --mode single
```

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
   
   # Check connector logs
   docker-compose logs kafka-connect
   
   # Re-register connector
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
./monitor.py --detailed

# Run end-to-end tests
./test_pipeline.py --detailed

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

# Generate test data
./data_generator.py --mode single
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