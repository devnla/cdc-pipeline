#!/bin/bash

# Social Media CDC Setup Script
# This script sets up the complete CDC pipeline with MySQL, Debezium, Kafka, and OpenSearch

set -e

echo "🚀 Starting Social Media CDC Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local health_check=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval $health_check > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Function to start services
start_services() {
    print_status "Starting all services with docker-compose..."
    docker-compose up -d
    
    # Wait for core services
    wait_for_service "MySQL" "docker-compose exec -T mysql mysqladmin ping -h localhost -u root -prootpassword"
    wait_for_service "Kafka" "docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list"
    wait_for_service "OpenSearch" "curl -s http://localhost:9200/_cluster/health"
    wait_for_service "Kafka Connect" "curl -s http://localhost:8083/connectors"
}

# Function to register Debezium connector
register_debezium_connector() {
    print_status "Registering Debezium MySQL connector..."
    
    # Wait a bit more for Kafka Connect to be fully ready
    sleep 10
    
    # Register the connector
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d @debezium-mysql-connector.json \
        http://localhost:8083/connectors)
    
    if [ "$response" = "201" ] || [ "$response" = "409" ]; then
        print_success "Debezium connector registered successfully"
    else
        print_error "Failed to register Debezium connector (HTTP $response)"
        print_status "Checking Kafka Connect logs..."
        docker-compose logs kafka-connect | tail -20
        return 1
    fi
}

# Function to verify connector status
verify_connector() {
    print_status "Verifying connector status..."
    
    sleep 5
    
    status=$(curl -s http://localhost:8083/connectors/mysql-socialmedia-connector/status | jq -r '.connector.state' 2>/dev/null || echo "UNKNOWN")
    
    if [ "$status" = "RUNNING" ]; then
        print_success "Connector is running successfully"
    else
        print_warning "Connector status: $status"
        print_status "Connector details:"
        curl -s http://localhost:8083/connectors/mysql-socialmedia-connector/status | jq .
    fi
}

# Function to start Kafka consumer
start_kafka_consumer() {
    print_status "Starting Kafka consumer for OpenSearch indexing..."
    
    # Build and start the consumer service
    docker-compose exec -d search-api python kafka_consumer.py
    
    print_success "Kafka consumer started"
}

# Function to test the setup
test_setup() {
    print_status "Testing the CDC pipeline..."
    
    # Insert a test post
    print_status "Inserting test data..."
    docker-compose exec -T mysql mysql -u dbuser -pdbpassword socialmedia -e "
        INSERT INTO posts (user_id, content, hashtags, is_public) 
        VALUES (1, 'Testing CDC pipeline! This should appear in OpenSearch. 🔥', JSON_ARRAY('#test', '#cdc'), TRUE);
    "
    
    # Wait for CDC to process
    sleep 5
    
    # Check if data appears in OpenSearch
    print_status "Checking OpenSearch for test data..."
    response=$(curl -s "http://localhost:9200/posts/_search?q=Testing%20CDC%20pipeline" | jq -r '.hits.total.value' 2>/dev/null || echo "0")
    
    if [ "$response" -gt "0" ]; then
        print_success "CDC pipeline is working! Test data found in OpenSearch"
    else
        print_warning "Test data not found in OpenSearch yet. This might be normal if the pipeline is still processing."
    fi
}

# Function to show service URLs
show_service_urls() {
    echo ""
    print_success "🎉 Setup completed! Here are your service URLs:"
    echo ""
    echo "📊 Kafka UI:              http://localhost:8080"
    echo "🔍 OpenSearch Dashboards: http://localhost:5601"
    echo "🔌 Kafka Connect API:     http://localhost:8083"
    echo "🔍 OpenSearch API:        http://localhost:9200"
    echo "🚀 FastAPI Search API:    http://localhost:8000"
    echo "🗄️  MySQL Database:       localhost:3306 (user: dbuser, password: dbpassword)"
    echo ""
    echo "📖 API Documentation:     http://localhost:8000/docs"
    echo ""
    print_status "You can now:"
    echo "  1. View Kafka topics and messages at http://localhost:8080"
    echo "  2. Search posts, users, and hashtags via the API at http://localhost:8000/docs"
    echo "  3. Monitor OpenSearch indices at http://localhost:5601"
    echo "  4. Insert data into MySQL and see it automatically indexed in OpenSearch"
    echo ""
}

# Function to show sample API calls
show_sample_api_calls() {
    print_status "📝 Sample API calls:"
    echo ""
    echo "# Search posts:"
    echo "curl 'http://localhost:8000/search/posts?q=technology&size=5'"
    echo ""
    echo "# Search users:"
    echo "curl 'http://localhost:8000/search/users?q=john&size=5'"
    echo ""
    echo "# Get trending hashtags:"
    echo "curl 'http://localhost:8000/trending/hashtags?limit=10'"
    echo ""
    echo "# Search hashtags:"
    echo "curl 'http://localhost:8000/search/hashtags?q=tech&limit=10'"
    echo ""
    echo "# Get analytics:"
    echo "curl 'http://localhost:8000/analytics/posts?days=30'"
    echo ""
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    docker-compose down -v
    print_success "Cleanup completed"
}

# Main execution
main() {
    case "${1:-setup}" in
        "setup")
            check_docker
            check_docker_compose
            start_services
            register_debezium_connector
            verify_connector
            start_kafka_consumer
            test_setup
            show_service_urls
            show_sample_api_calls
            ;;
        "cleanup")
            cleanup
            ;;
        "restart")
            cleanup
            main setup
            ;;
        "status")
            docker-compose ps
            echo ""
            print_status "Connector status:"
            curl -s http://localhost:8083/connectors/mysql-socialmedia-connector/status 2>/dev/null | jq . || echo "Connector not available"
            ;;
        "logs")
            service=${2:-"all"}
            if [ "$service" = "all" ]; then
                docker-compose logs -f
            else
                docker-compose logs -f "$service"
            fi
            ;;
        "test")
            test_setup
            ;;
        *)
            echo "Usage: $0 {setup|cleanup|restart|status|logs [service]|test}"
            echo ""
            echo "Commands:"
            echo "  setup    - Start all services and configure CDC pipeline"
            echo "  cleanup  - Stop all services and remove volumes"
            echo "  restart  - Cleanup and setup again"
            echo "  status   - Show service status and connector status"
            echo "  logs     - Show logs (optionally for specific service)"
            echo "  test     - Test the CDC pipeline"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"