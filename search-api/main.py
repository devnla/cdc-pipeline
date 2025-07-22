from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
import logging

# Import configuration and services
from config import client, create_indices
from config.settings import CORS_ORIGINS
from kafka_consumer import CDCProcessor

# Import route modules
from routes import search_router, analytics_router, health_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to hold the consumer thread
consumer_thread = None
cdc_processor = None

def start_kafka_consumer():
    """Start Kafka consumer in a separate thread"""
    try:
        processor = CDCProcessor()
        processor.run()
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Search API...")
    
    # Create indices
    await create_indices()
    
    # Start Kafka consumer
    global consumer_thread
    consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Kafka consumer started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Search API...")
    # Consumer thread will stop when main thread exits due to daemon=True

# FastAPI app
app = FastAPI(
    title="Social Media Search API",
    description="Advanced search API with autocomplete functionality for social media platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(search_router)
app.include_router(analytics_router)

# Add autocomplete router if it exists
try:
    from routes import autocomplete_router
    app.include_router(autocomplete_router)
except ImportError:
    logger.warning("Autocomplete router not found, skipping...")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Social Media Search API",
        "version": "2.0.0",
        "description": "Advanced search API with autocomplete functionality",
        "features": [
            "Full-text search for posts, users, and hashtags",
            "Real-time autocomplete suggestions",
            "Analytics and trending content",
            "Advanced filtering and sorting",
            "Real-time CDC data processing"
        ],
        "endpoints": {
            "health": "/health",
            "search": {
                "posts": "/search/posts",
                "users": "/search/users",
                "hashtags": "/search/hashtags"
            },
            "autocomplete": {
                "suggestions": "/autocomplete/suggestions",
                "users": "/autocomplete/users",
                "hashtags": "/autocomplete/hashtags",
                "mentions": "/autocomplete/mentions"
            },
            "analytics": {
                "posts": "/analytics/posts",
                "trending": "/analytics/trending"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)