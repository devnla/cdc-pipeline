import json
import logging
from kafka import KafkaConsumer
from opensearchpy import OpenSearch
import os
from datetime import datetime
from typing import Dict, Any, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'opensearch')
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

class CDCProcessor:
    def __init__(self):
        self.consumer = None
        self.setup_consumer()
    
    def setup_consumer(self):
        """Setup Kafka consumer with retry logic"""
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.consumer = KafkaConsumer(
                    'dbserver1.socialmedia.posts',
                    'dbserver1.socialmedia.users',
                    'dbserver1.socialmedia.comments',
                    'dbserver1.socialmedia.likes',
                    'dbserver1.socialmedia.follows',
                    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    group_id='opensearch-indexer',
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                    consumer_timeout_ms=1000
                )
                logger.info("Kafka consumer setup successful")
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to setup Kafka consumer (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(5)
        
        if retry_count >= max_retries:
            raise Exception("Failed to setup Kafka consumer after maximum retries")
    
    def wait_for_opensearch(self):
        """Wait for OpenSearch to be available"""
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                client.info()
                logger.info("OpenSearch is available")
                return True
            except Exception as e:
                retry_count += 1
                logger.info(f"Waiting for OpenSearch (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(2)
        
        raise Exception("OpenSearch is not available after maximum retries")
    
    def process_cdc_event(self, topic: str, message: Dict[str, Any]):
        """Process CDC event and index to OpenSearch"""
        try:
            if not message or 'payload' not in message:
                return
            
            payload = message['payload']
            operation = payload.get('op')
            
            # Extract table name from topic
            table_name = topic.split('.')[-1]
            
            if operation in ['c', 'u']:  # Create or Update
                after_data = payload.get('after')
                if after_data:
                    self.index_document(table_name, after_data, operation)
            elif operation == 'd':  # Delete
                before_data = payload.get('before')
                if before_data and 'id' in before_data:
                    self.delete_document(table_name, before_data['id'])
            
        except Exception as e:
            logger.error(f"Error processing CDC event: {e}")
    
    def index_document(self, table_name: str, data: Dict[str, Any], operation: str):
        """Index document to OpenSearch"""
        try:
            # Transform data based on table
            if table_name == 'posts':
                doc = self.transform_post_data(data)
                index_name = 'posts'
            elif table_name == 'users':
                doc = self.transform_user_data(data)
                index_name = 'users'
            elif table_name == 'comments':
                doc = self.transform_comment_data(data)
                index_name = 'comments'
            else:
                # For likes and follows, we might want to update related documents
                self.handle_relationship_change(table_name, data, operation)
                return
            
            # Index the document
            response = client.index(
                index=index_name,
                id=data['id'],
                body=doc,
                refresh=True
            )
            
            logger.info(f"Indexed {table_name} document {data['id']}: {response['result']}")
            
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
    
    def delete_document(self, table_name: str, doc_id: int):
        """Delete document from OpenSearch"""
        try:
            index_map = {
                'posts': 'posts',
                'users': 'users',
                'comments': 'comments'
            }
            
            if table_name in index_map:
                response = client.delete(
                    index=index_map[table_name],
                    id=doc_id,
                    refresh=True
                )
                logger.info(f"Deleted {table_name} document {doc_id}: {response['result']}")
            
        except Exception as e:
            if "not_found" not in str(e).lower():
                logger.error(f"Error deleting document: {e}")
    
    def transform_post_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform post data for OpenSearch indexing"""
        # Parse JSON fields
        hashtags = []
        mentions = []
        image_urls = []
        
        if data.get('hashtags'):
            try:
                hashtags = json.loads(data['hashtags']) if isinstance(data['hashtags'], str) else data['hashtags']
            except:
                pass
        
        if data.get('mentions'):
            try:
                mentions = json.loads(data['mentions']) if isinstance(data['mentions'], str) else data['mentions']
            except:
                pass
        
        if data.get('image_urls'):
            try:
                image_urls = json.loads(data['image_urls']) if isinstance(data['image_urls'], str) else data['image_urls']
            except:
                pass
        
        # Get user data for denormalization
        user_data = self.get_user_data(data['user_id'])
        
        return {
            'id': data['id'],
            'user_id': data['user_id'],
            'content': data['content'],
            'hashtags': hashtags,
            'mentions': mentions,
            'image_urls': image_urls,
            'like_count': data.get('like_count', 0),
            'comment_count': data.get('comment_count', 0),
            'share_count': data.get('share_count', 0),
            'is_public': data.get('is_public', True),
            'location': data.get('location'),
            'created_at': self.convert_timestamp(data.get('created_at')),
            'updated_at': self.convert_timestamp(data.get('updated_at')),
            'user': user_data
        }
    
    def transform_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user data for OpenSearch indexing"""
        return {
            'id': data['id'],
            'username': data['username'],
            'email': data['email'],
            'full_name': data['full_name'],
            'bio': data.get('bio'),
            'profile_image_url': data.get('profile_image_url'),
            'is_verified': data.get('is_verified', False),
            'follower_count': data.get('follower_count', 0),
            'following_count': data.get('following_count', 0),
            'post_count': data.get('post_count', 0),
            'created_at': self.convert_timestamp(data.get('created_at')),
            'updated_at': self.convert_timestamp(data.get('updated_at'))
        }
    
    def transform_comment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform comment data for OpenSearch indexing"""
        user_data = self.get_user_data(data['user_id'])
        
        return {
            'id': data['id'],
            'post_id': data['post_id'],
            'user_id': data['user_id'],
            'parent_comment_id': data.get('parent_comment_id'),
            'content': data['content'],
            'like_count': data.get('like_count', 0),
            'reply_count': data.get('reply_count', 0),
            'created_at': self.convert_timestamp(data.get('created_at')),
            'updated_at': self.convert_timestamp(data.get('updated_at')),
            'user': user_data
        }
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data for denormalization"""
        try:
            response = client.get(index='users', id=user_id)
            user_data = response['_source']
            return {
                'id': user_data['id'],
                'username': user_data['username'],
                'full_name': user_data['full_name'],
                'is_verified': user_data.get('is_verified', False)
            }
        except:
            return None
    
    def handle_relationship_change(self, table_name: str, data: Dict[str, Any], operation: str):
        """Handle likes and follows changes by updating related documents"""
        try:
            if table_name == 'likes':
                # Update like count in posts or comments
                if data.get('post_id'):
                    self.update_like_count('posts', data['post_id'])
                elif data.get('comment_id'):
                    self.update_like_count('comments', data['comment_id'])
            
            elif table_name == 'follows':
                # Update follower/following counts
                if operation in ['c', 'u']:
                    self.update_follow_counts(data['follower_id'], data['following_id'], 1)
                elif operation == 'd':
                    self.update_follow_counts(data['follower_id'], data['following_id'], -1)
        
        except Exception as e:
            logger.error(f"Error handling relationship change: {e}")
    
    def update_like_count(self, index_name: str, doc_id: int):
        """Update like count for posts or comments"""
        try:
            # This is a simplified approach - in production, you might want to
            # query the database for accurate counts
            client.update(
                index=index_name,
                id=doc_id,
                body={
                    "script": {
                        "source": "ctx._source.like_count = params.count",
                        "params": {"count": 0}  # You'd calculate this from the database
                    }
                },
                refresh=True
            )
        except Exception as e:
            logger.error(f"Error updating like count: {e}")
    
    def update_follow_counts(self, follower_id: int, following_id: int, delta: int):
        """Update follower/following counts"""
        try:
            # Update follower count for the user being followed
            client.update(
                index='users',
                id=following_id,
                body={
                    "script": {
                        "source": "ctx._source.follower_count += params.delta",
                        "params": {"delta": delta}
                    }
                },
                refresh=True
            )
            
            # Update following count for the user doing the following
            client.update(
                index='users',
                id=follower_id,
                body={
                    "script": {
                        "source": "ctx._source.following_count += params.delta",
                        "params": {"delta": delta}
                    }
                },
                refresh=True
            )
        except Exception as e:
            logger.error(f"Error updating follow counts: {e}")
    
    def convert_timestamp(self, timestamp) -> Optional[str]:
        """Convert various timestamp formats to ISO format"""
        if not timestamp:
            return None
        
        try:
            if isinstance(timestamp, (int, float)):
                # Unix timestamp (milliseconds)
                if timestamp > 1e10:  # milliseconds
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp).isoformat()
            elif isinstance(timestamp, str):
                # ISO format or other string format
                return timestamp
            else:
                return str(timestamp)
        except:
            return None
    
    def run(self):
        """Main consumer loop"""
        logger.info("Starting CDC processor...")
        
        # Wait for OpenSearch to be available
        self.wait_for_opensearch()
        
        logger.info("Starting to consume CDC events...")
        
        try:
            for message in self.consumer:
                try:
                    topic = message.topic
                    value = message.value
                    
                    logger.debug(f"Received message from topic {topic}")
                    self.process_cdc_event(topic, value)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("Shutting down CDC processor...")
        except Exception as e:
            logger.error(f"Unexpected error in consumer loop: {e}")
        finally:
            if self.consumer:
                self.consumer.close()

if __name__ == "__main__":
    processor = CDCProcessor()
    processor.run()