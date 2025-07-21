#!/usr/bin/env python3
"""
CDC Pipeline Monitor

Monitors the health and performance of the entire CDC pipeline including:
- MySQL database connectivity and binlog status
- Kafka cluster health and topic information
- Debezium connector status
- OpenSearch cluster health and indices
- FastAPI search service health
"""

import requests
import mysql.connector
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import argparse
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "🟢 HEALTHY"
    WARNING = "🟡 WARNING"
    CRITICAL = "🔴 CRITICAL"
    UNKNOWN = "⚪ UNKNOWN"

@dataclass
class ServiceHealth:
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    response_time_ms: float = 0

class CDCPipelineMonitor:
    def __init__(self):
        self.services = {
            'mysql': {'host': 'localhost', 'port': 3306},
            'kafka': {'host': 'localhost', 'port': 9092},
            'kafka_connect': {'host': 'localhost', 'port': 8083},
            'opensearch': {'host': 'localhost', 'port': 9200},
            'search_api': {'host': 'localhost', 'port': 8000}
        }
        
        self.db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'dbuser',
            'password': 'dbpassword',
            'database': 'socialmedia'
        }
    
    def check_mysql_health(self) -> ServiceHealth:
        """Check MySQL database health and CDC configuration"""
        start_time = time.time()
        
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Check basic connectivity
            cursor.execute("SELECT 1 as test")
            cursor.fetchone()
            
            # Check binlog configuration
            cursor.execute("SHOW VARIABLES WHERE Variable_name IN ('log_bin', 'binlog_format', 'server_id')")
            binlog_vars = {row['Variable_name']: row['Value'] for row in cursor.fetchall()}
            
            # Check database and tables
            cursor.execute("SHOW TABLES")
            tables = [row[f'Tables_in_{self.db_config["database"]}'] for row in cursor.fetchall()]
            
            # Check recent activity
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users) as user_count,
                    (SELECT COUNT(*) FROM posts) as post_count,
                    (SELECT COUNT(*) FROM comments) as comment_count,
                    (SELECT COUNT(*) FROM likes) as like_count,
                    (SELECT COUNT(*) FROM follows) as follow_count
            """)
            counts = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            response_time = (time.time() - start_time) * 1000
            
            # Validate CDC requirements
            issues = []
            if binlog_vars.get('log_bin') != 'ON':
                issues.append("Binary logging is disabled")
            if binlog_vars.get('binlog_format') != 'ROW':
                issues.append(f"Binlog format is {binlog_vars.get('binlog_format')}, should be ROW")
            
            status = HealthStatus.CRITICAL if issues else HealthStatus.HEALTHY
            message = "; ".join(issues) if issues else "MySQL is healthy and CDC-ready"
            
            details = {
                'binlog_config': binlog_vars,
                'tables': tables,
                'record_counts': counts,
                'cdc_ready': len(issues) == 0
            }
            
            return ServiceHealth("MySQL", status, message, details, response_time)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth("MySQL", HealthStatus.CRITICAL, f"Connection failed: {str(e)}", {}, response_time)
    
    def check_kafka_connect_health(self) -> ServiceHealth:
        """Check Kafka Connect and Debezium connector health"""
        start_time = time.time()
        
        try:
            # Check Kafka Connect health
            response = requests.get(f"http://{self.services['kafka_connect']['host']}:{self.services['kafka_connect']['port']}/", timeout=5)
            response.raise_for_status()
            
            # Check connectors
            connectors_response = requests.get(
                f"http://{self.services['kafka_connect']['host']}:{self.services['kafka_connect']['port']}/connectors",
                timeout=5
            )
            connectors = connectors_response.json()
            
            # Check specific connector status
            connector_status = None
            if 'mysql-socialmedia-connector' in connectors:
                status_response = requests.get(
                    f"http://{self.services['kafka_connect']['host']}:{self.services['kafka_connect']['port']}/connectors/mysql-socialmedia-connector/status",
                    timeout=5
                )
                connector_status = status_response.json()
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine health status
            if not connectors:
                status = HealthStatus.WARNING
                message = "No connectors registered"
            elif 'mysql-socialmedia-connector' not in connectors:
                status = HealthStatus.WARNING
                message = "MySQL connector not found"
            elif connector_status and connector_status['connector']['state'] == 'RUNNING':
                status = HealthStatus.HEALTHY
                message = "Debezium connector is running"
            else:
                status = HealthStatus.CRITICAL
                message = f"Connector state: {connector_status['connector']['state'] if connector_status else 'UNKNOWN'}"
            
            details = {
                'connectors': connectors,
                'mysql_connector_status': connector_status
            }
            
            return ServiceHealth("Kafka Connect", status, message, details, response_time)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth("Kafka Connect", HealthStatus.CRITICAL, f"Connection failed: {str(e)}", {}, response_time)
    
    def check_opensearch_health(self) -> ServiceHealth:
        """Check OpenSearch cluster and indices health"""
        start_time = time.time()
        
        try:
            # Check cluster health
            health_response = requests.get(
                f"http://{self.services['opensearch']['host']}:{self.services['opensearch']['port']}/_cluster/health",
                timeout=5
            )
            health_response.raise_for_status()
            cluster_health = health_response.json()
            
            # Check indices
            indices_response = requests.get(
                f"http://{self.services['opensearch']['host']}:{self.services['opensearch']['port']}/_cat/indices?format=json",
                timeout=5
            )
            indices = indices_response.json()
            
            # Check specific indices
            expected_indices = ['posts', 'users', 'comments']
            existing_indices = [idx['index'] for idx in indices if idx['index'] in expected_indices]
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine health status
            cluster_status = cluster_health.get('status', 'unknown')
            if cluster_status == 'red':
                status = HealthStatus.CRITICAL
                message = "Cluster status is RED"
            elif cluster_status == 'yellow':
                status = HealthStatus.WARNING
                message = "Cluster status is YELLOW"
            elif len(existing_indices) < len(expected_indices):
                status = HealthStatus.WARNING
                missing = set(expected_indices) - set(existing_indices)
                message = f"Missing indices: {', '.join(missing)}"
            else:
                status = HealthStatus.HEALTHY
                message = "OpenSearch cluster is healthy"
            
            details = {
                'cluster_health': cluster_health,
                'indices': indices,
                'expected_indices': expected_indices,
                'existing_indices': existing_indices
            }
            
            return ServiceHealth("OpenSearch", status, message, details, response_time)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth("OpenSearch", HealthStatus.CRITICAL, f"Connection failed: {str(e)}", {}, response_time)
    
    def check_search_api_health(self) -> ServiceHealth:
        """Check FastAPI search service health"""
        start_time = time.time()
        
        try:
            # Check health endpoint
            health_response = requests.get(
                f"http://{self.services['search_api']['host']}:{self.services['search_api']['port']}/health",
                timeout=5
            )
            health_response.raise_for_status()
            health_data = health_response.json()
            
            # Test search functionality
            search_response = requests.get(
                f"http://{self.services['search_api']['host']}:{self.services['search_api']['port']}/search/posts",
                params={'q': 'test', 'size': 1},
                timeout=5
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            message = "Search API is healthy and functional"
            
            details = {
                'health_check': health_data,
                'search_test': {
                    'total_posts': search_data.get('total', 0),
                    'response_time_ms': search_data.get('took', 0)
                }
            }
            
            return ServiceHealth("Search API", status, message, details, response_time)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth("Search API", HealthStatus.CRITICAL, f"Connection failed: {str(e)}", {}, response_time)
    
    def check_kafka_topics(self) -> ServiceHealth:
        """Check Kafka topics for CDC data"""
        start_time = time.time()
        
        try:
            # Use Kafka Connect API to check topics (simpler than direct Kafka API)
            response = requests.get(
                f"http://{self.services['kafka_connect']['host']}:{self.services['kafka_connect']['port']}/connectors/mysql-socialmedia-connector/topics",
                timeout=5
            )
            
            if response.status_code == 200:
                topics = response.json()
                expected_topics = [
                    'dbserver1.socialmedia.users',
                    'dbserver1.socialmedia.posts',
                    'dbserver1.socialmedia.comments'
                ]
                
                existing_topics = [topic for topic in topics if topic in expected_topics]
                
                response_time = (time.time() - start_time) * 1000
                
                if len(existing_topics) == len(expected_topics):
                    status = HealthStatus.HEALTHY
                    message = "All CDC topics are available"
                else:
                    status = HealthStatus.WARNING
                    missing = set(expected_topics) - set(existing_topics)
                    message = f"Missing topics: {', '.join(missing)}"
                
                details = {
                    'all_topics': topics,
                    'expected_topics': expected_topics,
                    'existing_topics': existing_topics
                }
                
                return ServiceHealth("Kafka Topics", status, message, details, response_time)
            else:
                response_time = (time.time() - start_time) * 1000
                return ServiceHealth("Kafka Topics", HealthStatus.WARNING, "Connector not found or not running", {}, response_time)
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth("Kafka Topics", HealthStatus.CRITICAL, f"Check failed: {str(e)}", {}, response_time)
    
    def run_health_check(self, detailed: bool = False) -> List[ServiceHealth]:
        """Run complete health check on all services"""
        print("🔍 Running CDC Pipeline Health Check...\n")
        
        checks = [
            ("MySQL Database", self.check_mysql_health),
            ("Kafka Connect", self.check_kafka_connect_health),
            ("Kafka Topics", self.check_kafka_topics),
            ("OpenSearch", self.check_opensearch_health),
            ("Search API", self.check_search_api_health)
        ]
        
        results = []
        
        for check_name, check_func in checks:
            print(f"Checking {check_name}...", end=" ")
            result = check_func()
            results.append(result)
            print(f"{result.status.value} ({result.response_time_ms:.1f}ms)")
            print(f"  └─ {result.message}")
            
            if detailed and result.details:
                self._print_details(result.details, indent=4)
            
            print()
        
        return results
    
    def _print_details(self, details: Dict[str, Any], indent: int = 0):
        """Print detailed information with proper indentation"""
        prefix = " " * indent
        
        for key, value in details.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self._print_details(value, indent + 2)
            elif isinstance(value, list):
                print(f"{prefix}{key}: {len(value)} items")
                if len(value) <= 5:  # Show small lists
                    for item in value:
                        print(f"{prefix}  - {item}")
            else:
                print(f"{prefix}{key}: {value}")
    
    def print_summary(self, results: List[ServiceHealth]):
        """Print overall health summary"""
        print("\n" + "="*60)
        print("📊 HEALTH SUMMARY")
        print("="*60)
        
        healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        warning_count = sum(1 for r in results if r.status == HealthStatus.WARNING)
        critical_count = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
        
        total_services = len(results)
        avg_response_time = sum(r.response_time_ms for r in results) / total_services
        
        print(f"Services Checked: {total_services}")
        print(f"🟢 Healthy: {healthy_count}")
        print(f"🟡 Warning: {warning_count}")
        print(f"🔴 Critical: {critical_count}")
        print(f"⚡ Avg Response Time: {avg_response_time:.1f}ms")
        
        if critical_count > 0:
            overall_status = "🔴 CRITICAL"
        elif warning_count > 0:
            overall_status = "🟡 WARNING"
        else:
            overall_status = "🟢 HEALTHY"
        
        print(f"\nOverall Status: {overall_status}")
        
        if critical_count > 0 or warning_count > 0:
            print("\n⚠️  Issues Found:")
            for result in results:
                if result.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                    print(f"  • {result.name}: {result.message}")
    
    def monitor_continuous(self, interval: int = 30):
        """Run continuous monitoring"""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] Running health check...")
                
                results = self.run_health_check(detailed=False)
                self.print_summary(results)
                
                print(f"\nNext check in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='CDC Pipeline Monitor')
    parser.add_argument('--mode', choices=['check', 'monitor'], default='check',
                       help='Run single check or continuous monitoring')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed information')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = CDCPipelineMonitor()
    
    if args.mode == 'check':
        results = monitor.run_health_check(detailed=args.detailed)
        monitor.print_summary(results)
    elif args.mode == 'monitor':
        monitor.monitor_continuous(args.interval)

if __name__ == "__main__":
    main()