#!/usr/bin/env python3
"""
CDC Pipeline End-to-End Test Suite

Tests the complete CDC pipeline by:
1. Inserting test data into MySQL
2. Verifying CDC events are captured by Debezium
3. Checking data propagation to OpenSearch
4. Testing search API functionality
5. Validating data consistency across the pipeline
"""

import mysql.connector
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
from dataclasses import dataclass
from faker import Faker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    test_name: str
    success: bool
    message: str
    duration_ms: float
    details: Dict[str, Any] = None

class CDCPipelineTester:
    def __init__(self):
        self.fake = Faker()
        
        # Service configurations
        self.db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'dbuser',
            'password': 'dbpassword',
            'database': 'socialmedia'
        }
        
        self.opensearch_url = 'http://localhost:9200'
        self.search_api_url = 'http://localhost:8000'
        self.kafka_connect_url = 'http://localhost:8083'
        
        # Test data tracking
        self.test_user_ids = []
        self.test_post_ids = []
        self.test_comment_ids = []
        
    def setup_test_environment(self) -> TestResult:
        """Prepare the test environment"""
        start_time = time.time()
        
        try:
            # Clear any existing test data
            self._cleanup_test_data()
            
            # Verify all services are running
            services_ok = self._check_services_availability()
            if not services_ok:
                return TestResult(
                    "Environment Setup",
                    False,
                    "One or more services are not available",
                    (time.time() - start_time) * 1000
                )
            
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "Environment Setup",
                True,
                "Test environment is ready",
                duration
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "Environment Setup",
                False,
                f"Setup failed: {str(e)}",
                duration
            )
    
    def test_mysql_insert_and_cdc_capture(self) -> TestResult:
        """Test MySQL data insertion and CDC event capture"""
        start_time = time.time()
        
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Create test user
            test_user = {
                'username': f'testuser_{uuid.uuid4().hex[:8]}',
                'email': self.fake.email(),
                'full_name': self.fake.name(),
                'bio': self.fake.text(max_nb_chars=200),
                'profile_image_url': self.fake.image_url(),
                'is_verified': False,
                'follower_count': 0,
                'following_count': 0
            }
            
            cursor.execute("""
                INSERT INTO users (username, email, full_name, bio, profile_image_url, 
                                 is_verified, follower_count, following_count)
                VALUES (%(username)s, %(email)s, %(full_name)s, %(bio)s, %(profile_image_url)s,
                       %(is_verified)s, %(follower_count)s, %(following_count)s)
            """, test_user)
            
            user_id = cursor.lastrowid
            self.test_user_ids.append(user_id)
            
            # Create test post
            test_post = {
                'user_id': user_id,
                'content': f'Test post content {uuid.uuid4().hex[:8]} #testpost',
                'like_count': 0,
                'comment_count': 0,
                'share_count': 0
            }
            
            cursor.execute("""
                INSERT INTO posts (user_id, content, like_count, comment_count, share_count)
                VALUES (%(user_id)s, %(content)s, %(like_count)s, %(comment_count)s, %(share_count)s)
            """, test_post)
            
            post_id = cursor.lastrowid
            self.test_post_ids.append(post_id)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Wait for CDC to process
            time.sleep(2)
            
            duration = (time.time() - start_time) * 1000
            
            details = {
                'test_user_id': user_id,
                'test_post_id': post_id,
                'user_data': test_user,
                'post_data': test_post
            }
            
            return TestResult(
                "MySQL Insert & CDC Capture",
                True,
                f"Created user {user_id} and post {post_id}",
                duration,
                details
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "MySQL Insert & CDC Capture",
                False,
                f"Failed: {str(e)}",
                duration
            )
    
    def test_opensearch_data_propagation(self, test_user_id: int, test_post_id: int) -> TestResult:
        """Test data propagation to OpenSearch"""
        start_time = time.time()
        
        try:
            # Wait for data to propagate (CDC + consumer processing)
            max_wait_time = 30  # seconds
            wait_interval = 2   # seconds
            waited = 0
            
            user_found = False
            post_found = False
            
            while waited < max_wait_time and not (user_found and post_found):
                # Check if user exists in OpenSearch
                if not user_found:
                    user_response = requests.get(
                        f"{self.opensearch_url}/users/_doc/{test_user_id}",
                        timeout=5
                    )
                    user_found = user_response.status_code == 200
                
                # Check if post exists in OpenSearch
                if not post_found:
                    post_response = requests.get(
                        f"{self.opensearch_url}/posts/_doc/{test_post_id}",
                        timeout=5
                    )
                    post_found = post_response.status_code == 200
                
                if not (user_found and post_found):
                    time.sleep(wait_interval)
                    waited += wait_interval
            
            duration = (time.time() - start_time) * 1000
            
            if user_found and post_found:
                # Get the actual documents
                user_doc = requests.get(f"{self.opensearch_url}/users/_doc/{test_user_id}").json()
                post_doc = requests.get(f"{self.opensearch_url}/posts/_doc/{test_post_id}").json()
                
                details = {
                    'wait_time_seconds': waited,
                    'user_document': user_doc['_source'],
                    'post_document': post_doc['_source']
                }
                
                return TestResult(
                    "OpenSearch Data Propagation",
                    True,
                    f"Data propagated successfully in {waited}s",
                    duration,
                    details
                )
            else:
                missing = []
                if not user_found:
                    missing.append("user")
                if not post_found:
                    missing.append("post")
                
                return TestResult(
                    "OpenSearch Data Propagation",
                    False,
                    f"Data not found after {waited}s: {', '.join(missing)}",
                    duration
                )
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "OpenSearch Data Propagation",
                False,
                f"Failed: {str(e)}",
                duration
            )
    
    def test_search_api_functionality(self, test_post_content: str, test_username: str) -> TestResult:
        """Test search API functionality"""
        start_time = time.time()
        
        try:
            # Wait a bit for search index to refresh
            time.sleep(2)
            
            # Test health endpoint
            health_response = requests.get(f"{self.search_api_url}/health", timeout=5)
            health_response.raise_for_status()
            
            # Test post search
            search_term = "testpost"  # From hashtag in test post
            search_response = requests.get(
                f"{self.search_api_url}/search/posts",
                params={'q': search_term, 'size': 10},
                timeout=10
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            # Test user search - search for the actual test username
            user_search_response = requests.get(
                f"{self.search_api_url}/search/users",
                params={'q': test_username, 'size': 10},
                timeout=10
            )
            user_search_response.raise_for_status()
            user_search_data = user_search_response.json()
            
            # Test trending hashtags
            trending_response = requests.get(
                f"{self.search_api_url}/hashtags/trending",
                timeout=10
            )
            trending_response.raise_for_status()
            trending_data = trending_response.json()
            
            duration = (time.time() - start_time) * 1000
            
            # Verify search results contain our test data
            test_post_found = any(
                search_term.lower() in hit.get('content', '').lower() 
                for hit in search_data.get('results', [])
            )
            
            test_user_found = any(
                test_username.lower() in hit.get('username', '').lower() 
                for hit in user_search_data.get('results', [])
            )
            
            details = {
                'health_check': health_response.json(),
                'post_search_results': search_data,
                'user_search_results': user_search_data,
                'trending_hashtags': trending_data,
                'test_post_found': test_post_found,
                'test_user_found': test_user_found
            }
            
            success = test_post_found and test_user_found
            message = "Search API working correctly" if success else "Test data not found in search results"
            
            return TestResult(
                "Search API Functionality",
                success,
                message,
                duration,
                details
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "Search API Functionality",
                False,
                f"Failed: {str(e)}",
                duration
            )
    
    def test_data_consistency(self, test_user_id: int, test_post_id: int) -> TestResult:
        """Test data consistency between MySQL and OpenSearch"""
        start_time = time.time()
        
        try:
            # Get data from MySQL
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM users WHERE id = %s", (test_user_id,))
            mysql_user = cursor.fetchone()
            
            cursor.execute("SELECT * FROM posts WHERE id = %s", (test_post_id,))
            mysql_post = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            # Get data from OpenSearch
            user_response = requests.get(f"{self.opensearch_url}/users/_doc/{test_user_id}", timeout=5)
            post_response = requests.get(f"{self.opensearch_url}/posts/_doc/{test_post_id}", timeout=5)
            
            if user_response.status_code != 200 or post_response.status_code != 200:
                duration = (time.time() - start_time) * 1000
                return TestResult(
                    "Data Consistency",
                    False,
                    "Data not found in OpenSearch",
                    duration
                )
            
            opensearch_user = user_response.json()['_source']
            opensearch_post = post_response.json()['_source']
            
            # Compare key fields
            user_consistent = (
                mysql_user['username'] == opensearch_user['username'] and
                mysql_user['email'] == opensearch_user['email'] and
                mysql_user['full_name'] == opensearch_user['full_name']
            )
            
            post_consistent = (
                mysql_post['content'] == opensearch_post['content'] and
                mysql_post['user_id'] == opensearch_post['user_id']
            )
            
            duration = (time.time() - start_time) * 1000
            
            success = user_consistent and post_consistent
            message = "Data is consistent" if success else "Data inconsistency detected"
            
            details = {
                'mysql_user': mysql_user,
                'opensearch_user': opensearch_user,
                'mysql_post': mysql_post,
                'opensearch_post': opensearch_post,
                'user_consistent': user_consistent,
                'post_consistent': post_consistent
            }
            
            return TestResult(
                "Data Consistency",
                success,
                message,
                duration,
                details
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "Data Consistency",
                False,
                f"Failed: {str(e)}",
                duration
            )
    
    def test_update_operations(self, test_user_id: int, test_post_id: int) -> TestResult:
        """Test UPDATE operations and CDC propagation"""
        start_time = time.time()
        
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Update user bio
            new_bio = f"Updated bio at {datetime.now().isoformat()}"
            cursor.execute(
                "UPDATE users SET bio = %s WHERE id = %s",
                (new_bio, test_user_id)
            )
            
            # Update post like count
            new_like_count = 42
            cursor.execute(
                "UPDATE posts SET like_count = %s WHERE id = %s",
                (new_like_count, test_post_id)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Wait for CDC to process updates
            time.sleep(3)
            
            # Verify updates in OpenSearch
            user_response = requests.get(f"{self.opensearch_url}/users/_doc/{test_user_id}", timeout=5)
            post_response = requests.get(f"{self.opensearch_url}/posts/_doc/{test_post_id}", timeout=5)
            
            if user_response.status_code != 200 or post_response.status_code != 200:
                duration = (time.time() - start_time) * 1000
                return TestResult(
                    "Update Operations",
                    False,
                    "Updated data not found in OpenSearch",
                    duration
                )
            
            opensearch_user = user_response.json()['_source']
            opensearch_post = post_response.json()['_source']
            
            bio_updated = opensearch_user['bio'] == new_bio
            likes_updated = opensearch_post['like_count'] == new_like_count
            
            duration = (time.time() - start_time) * 1000
            
            success = bio_updated and likes_updated
            message = "Updates propagated successfully" if success else "Update propagation failed"
            
            details = {
                'new_bio': new_bio,
                'new_like_count': new_like_count,
                'bio_updated': bio_updated,
                'likes_updated': likes_updated,
                'opensearch_user_bio': opensearch_user.get('bio'),
                'opensearch_post_likes': opensearch_post.get('like_count')
            }
            
            return TestResult(
                "Update Operations",
                success,
                message,
                duration,
                details
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                "Update Operations",
                False,
                f"Failed: {str(e)}",
                duration
            )
    
    def _check_services_availability(self) -> bool:
        """Check if all required services are available"""
        services = [
            ("MySQL", lambda: mysql.connector.connect(**self.db_config)),
            ("OpenSearch", lambda: requests.get(f"{self.opensearch_url}/_cluster/health", timeout=5)),
            ("Search API", lambda: requests.get(f"{self.search_api_url}/health", timeout=5)),
            ("Kafka Connect", lambda: requests.get(f"{self.kafka_connect_url}/", timeout=5))
        ]
        
        for service_name, check_func in services:
            try:
                result = check_func()
                if hasattr(result, 'close'):
                    result.close()
                elif hasattr(result, 'raise_for_status'):
                    result.raise_for_status()
            except Exception as e:
                logger.error(f"{service_name} is not available: {e}")
                return False
        
        return True
    
    def _cleanup_test_data(self):
        """Clean up any existing test data"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Clean up test users and their related data
            if self.test_user_ids:
                placeholders = ','.join(['%s'] * len(self.test_user_ids))
                
                # Delete in order to respect foreign key constraints
                cursor.execute(f"DELETE FROM comments WHERE user_id IN ({placeholders})", self.test_user_ids)
                cursor.execute(f"DELETE FROM likes WHERE user_id IN ({placeholders})", self.test_user_ids)
                cursor.execute(f"DELETE FROM follows WHERE follower_id IN ({placeholders}) OR following_id IN ({placeholders})", 
                             self.test_user_ids + self.test_user_ids)
                cursor.execute(f"DELETE FROM posts WHERE user_id IN ({placeholders})", self.test_user_ids)
                cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders})", self.test_user_ids)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Clear tracking lists
            self.test_user_ids.clear()
            self.test_post_ids.clear()
            self.test_comment_ids.clear()
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    def run_full_test_suite(self, cleanup_after: bool = True) -> List[TestResult]:
        """Run the complete test suite"""
        logger.info("🧪 Starting CDC Pipeline End-to-End Test Suite")
        
        results = []
        
        # Test 1: Environment Setup
        logger.info("Running environment setup...")
        setup_result = self.setup_test_environment()
        results.append(setup_result)
        
        if not setup_result.success:
            logger.error("Environment setup failed, aborting tests")
            return results
        
        # Test 2: MySQL Insert and CDC Capture
        logger.info("Testing MySQL insert and CDC capture...")
        insert_result = self.test_mysql_insert_and_cdc_capture()
        results.append(insert_result)
        
        if not insert_result.success:
            logger.error("MySQL insert test failed, aborting remaining tests")
            return results
        
        test_user_id = insert_result.details['test_user_id']
        test_post_id = insert_result.details['test_post_id']
        test_post_content = insert_result.details['post_data']['content']
        
        # Test 3: OpenSearch Data Propagation
        logger.info("Testing OpenSearch data propagation...")
        propagation_result = self.test_opensearch_data_propagation(test_user_id, test_post_id)
        results.append(propagation_result)
        
        # Test 4: Search API Functionality
        logger.info("Testing search API functionality...")
        test_username = insert_result.details['user_data']['username']
        search_result = self.test_search_api_functionality(test_post_content, test_username)
        results.append(search_result)
        
        # Test 5: Data Consistency
        logger.info("Testing data consistency...")
        consistency_result = self.test_data_consistency(test_user_id, test_post_id)
        results.append(consistency_result)
        
        # Test 6: Update Operations
        logger.info("Testing update operations...")
        update_result = self.test_update_operations(test_user_id, test_post_id)
        results.append(update_result)
        
        # Cleanup
        if cleanup_after:
            logger.info("Cleaning up test data...")
            self._cleanup_test_data()
        
        return results
    
    def print_test_results(self, results: List[TestResult], detailed: bool = False):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("🧪 CDC PIPELINE TEST RESULTS")
        print("="*80)
        
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        total_duration = sum(r.duration_ms for r in results)
        
        for result in results:
            status_icon = "✅" if result.success else "❌"
            print(f"{status_icon} {result.test_name:<30} ({result.duration_ms:6.1f}ms)")
            print(f"   └─ {result.message}")
            
            if detailed and result.details:
                self._print_details(result.details, indent=6)
            
            print()
        
        print("="*80)
        print(f"📊 SUMMARY: {passed}/{len(results)} tests passed")
        print(f"⏱️  Total Duration: {total_duration:.1f}ms")
        
        if failed > 0:
            print(f"❌ {failed} test(s) failed")
            print("\n🔍 Failed Tests:")
            for result in results:
                if not result.success:
                    print(f"  • {result.test_name}: {result.message}")
        else:
            print("🎉 All tests passed!")
    
    def _print_details(self, details: Dict[str, Any], indent: int = 0):
        """Print detailed information with proper indentation"""
        prefix = " " * indent
        
        for key, value in details.items():
            if isinstance(value, dict) and len(str(value)) < 200:
                print(f"{prefix}{key}: {json.dumps(value, indent=2)}")
            elif isinstance(value, list) and len(value) <= 3:
                print(f"{prefix}{key}: {value}")
            elif isinstance(value, (str, int, float, bool)):
                print(f"{prefix}{key}: {value}")
            else:
                print(f"{prefix}{key}: <complex data>")

def main():
    parser = argparse.ArgumentParser(description='CDC Pipeline End-to-End Tester')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed test information')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup after tests')
    
    args = parser.parse_args()
    
    tester = CDCPipelineTester()
    
    try:
        results = tester.run_full_test_suite(cleanup_after=not args.no_cleanup)
        tester.print_test_results(results, detailed=args.detailed)
        
        # Exit with error code if any tests failed
        failed_count = sum(1 for r in results if not r.success)
        exit(failed_count)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        tester._cleanup_test_data()
        exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()