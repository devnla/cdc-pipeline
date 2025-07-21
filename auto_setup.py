#!/usr/bin/env python3
"""
Automated CDC Pipeline Setup Script
Handles database permissions, service startup, and UI configuration
"""

import subprocess
import time
import json
import requests
import sys
import os
from typing import Dict, List, Tuple

class CDCPipelineSetup:
    def __init__(self):
        self.services_status = {}
        self.required_services = [
            'mysql', 'zookeeper', 'kafka', 'opensearch', 
            'opensearch-dashboards', 'kafka-connect', 'kafka-ui', 'search-api'
        ]
        
    def run_command(self, command: str, capture_output: bool = True) -> Tuple[int, str]:
        """Run shell command and return exit code and output"""
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.returncode, result.stdout + result.stderr
            else:
                result = subprocess.run(command, shell=True)
                return result.returncode, ""
        except Exception as e:
            return 1, str(e)
    
    def check_docker_services(self) -> bool:
        """Check if all required Docker services are running"""
        print("🔍 Checking Docker services status...")
        
        exit_code, output = self.run_command("docker-compose ps --format json")
        if exit_code != 0:
            print("❌ Failed to check Docker services")
            return False
        
        try:
            services = [json.loads(line) for line in output.strip().split('\n') if line]
            running_services = [s['Service'] for s in services if s['State'] == 'running']
            
            for service in self.required_services:
                if service in running_services:
                    self.services_status[service] = 'running'
                    print(f"✅ {service}: running")
                else:
                    self.services_status[service] = 'stopped'
                    print(f"❌ {service}: stopped")
            
            return all(status == 'running' for status in self.services_status.values())
            
        except Exception as e:
            print(f"❌ Error parsing service status: {e}")
            return False
    
    def start_services(self) -> bool:
        """Start all Docker services"""
        print("🚀 Starting Docker services...")
        
        exit_code, output = self.run_command("docker-compose up -d", capture_output=False)
        if exit_code != 0:
            print("❌ Failed to start Docker services")
            return False
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(30)
        
        return self.check_docker_services()
    
    def fix_mysql_permissions(self) -> bool:
        """Fix MySQL permissions for Debezium"""
        print("🔧 Fixing MySQL permissions for CDC...")
        
        mysql_commands = [
            "GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'dbuser'@'%';",
            "GRANT SELECT ON socialmedia.* TO 'dbuser'@'%';",
            "FLUSH PRIVILEGES;"
        ]
        
        for cmd in mysql_commands:
            mysql_exec = f"docker-compose exec -T mysql mysql -u root -prootpassword -e \"{cmd}\""
            exit_code, output = self.run_command(mysql_exec)
            
            if exit_code != 0:
                print(f"❌ Failed to execute: {cmd}")
                print(f"Error: {output}")
                return False
            else:
                print(f"✅ Executed: {cmd}")
        
        return True
    
    def restart_kafka_connect(self) -> bool:
        """Restart Kafka Connect to apply new permissions"""
        print("🔄 Restarting Kafka Connect...")
        
        exit_code, _ = self.run_command("docker-compose restart kafka-connect")
        if exit_code != 0:
            print("❌ Failed to restart Kafka Connect")
            return False
        
        # Wait for Kafka Connect to be ready
        print("⏳ Waiting for Kafka Connect to be ready...")
        time.sleep(20)
        
        return self.check_kafka_connect_health()
    
    def check_kafka_connect_health(self) -> bool:
        """Check if Kafka Connect is healthy"""
        try:
            response = requests.get("http://localhost:8083/connectors", timeout=10)
            if response.status_code == 200:
                print("✅ Kafka Connect is healthy")
                return True
            else:
                print(f"❌ Kafka Connect health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Kafka Connect health check failed: {e}")
            return False
    
    def register_debezium_connector(self) -> bool:
        """Register Debezium MySQL connector"""
        print("📡 Registering Debezium MySQL connector...")
        
        # Check if connector already exists
        try:
            response = requests.get("http://localhost:8083/connectors/debezium-mysql-connector")
            if response.status_code == 200:
                print("✅ Debezium connector already exists")
                return True
        except:
            pass
        
        # Register new connector
        exit_code, output = self.run_command(
            "curl -X POST -H 'Content-Type: application/json' "
            "-d @debezium-mysql-connector.json "
            "http://localhost:8083/connectors"
        )
        
        if exit_code == 0:
            print("✅ Debezium connector registered successfully")
            return True
        else:
            print(f"❌ Failed to register Debezium connector: {output}")
            return False
    
    def check_connector_status(self) -> bool:
        """Check Debezium connector status"""
        try:
            response = requests.get("http://localhost:8083/connectors/debezium-mysql-connector/status")
            if response.status_code == 200:
                status = response.json()
                connector_state = status.get('connector', {}).get('state')
                task_state = status.get('tasks', [{}])[0].get('state') if status.get('tasks') else None
                
                print(f"📊 Connector state: {connector_state}")
                print(f"📊 Task state: {task_state}")
                
                return connector_state == 'RUNNING' and task_state == 'RUNNING'
            else:
                print(f"❌ Failed to check connector status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking connector status: {e}")
            return False
    
    def create_opensearch_indices(self) -> bool:
        """Create required OpenSearch indices"""
        print("🔍 Creating OpenSearch indices...")
        
        indices = {
            'posts': {
                'mappings': {
                    'properties': {
                        'id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'content': {'type': 'text'},
                        'hashtags': {'type': 'keyword'},
                        'like_count': {'type': 'integer'},
                        'created_at': {'type': 'date'}
                    }
                }
            },
            'users': {
                'mappings': {
                    'properties': {
                        'id': {'type': 'integer'},
                        'username': {'type': 'keyword'},
                        'email': {'type': 'keyword'},
                        'full_name': {'type': 'text'},
                        'bio': {'type': 'text'},
                        'is_verified': {'type': 'boolean'},
                        'created_at': {'type': 'date'}
                    }
                }
            },
            'comments': {
                'mappings': {
                    'properties': {
                        'id': {'type': 'integer'},
                        'post_id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'content': {'type': 'text'},
                        'created_at': {'type': 'date'}
                    }
                }
            }
        }
        
        for index_name, mapping in indices.items():
            try:
                response = requests.put(
                    f"http://localhost:9200/{index_name}",
                    json=mapping,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ Created index: {index_name}")
                elif response.status_code == 400 and 'already exists' in response.text:
                    print(f"✅ Index already exists: {index_name}")
                else:
                    print(f"❌ Failed to create index {index_name}: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creating index {index_name}: {e}")
                return False
        
        return True
    
    def check_ui_requirements(self) -> Dict[str, str]:
        """Check which UIs are needed and their status"""
        print("🖥️  Checking UI requirements...")
        
        ui_status = {}
        
        # Check Kafka UI
        try:
            response = requests.get("http://localhost:8080", timeout=5)
            if response.status_code == 200:
                ui_status['kafka_ui'] = 'available'
                print("✅ Kafka UI: Available at http://localhost:8080")
            else:
                ui_status['kafka_ui'] = 'error'
        except:
            ui_status['kafka_ui'] = 'unavailable'
            print("❌ Kafka UI: Unavailable")
        
        # Check OpenSearch Dashboards
        try:
            response = requests.get("http://localhost:5601", timeout=5)
            if response.status_code == 200:
                ui_status['opensearch_dashboards'] = 'available'
                print("✅ OpenSearch Dashboards: Available at http://localhost:5601")
            else:
                ui_status['opensearch_dashboards'] = 'error'
        except:
            ui_status['opensearch_dashboards'] = 'unavailable'
            print("❌ OpenSearch Dashboards: Unavailable")
        
        # Check if Debezium UI is needed
        print("\n🤔 Do you need Debezium UI?")
        print("   Kafka UI provides:")
        print("   - Kafka topics monitoring")
        print("   - Message browsing")
        print("   - Consumer group monitoring")
        print("   \n   Debezium UI provides:")
        print("   - Connector-specific monitoring")
        print("   - Detailed CDC metrics")
        print("   - Connector configuration management")
        
        if ui_status['kafka_ui'] == 'available':
            print("\n✅ Recommendation: Kafka UI is sufficient for most CDC monitoring needs")
            ui_status['recommendation'] = 'kafka_ui_sufficient'
        else:
            print("\n⚠️  Recommendation: Consider adding Debezium UI since Kafka UI is unavailable")
            ui_status['recommendation'] = 'debezium_ui_needed'
        
        return ui_status
    
    def run_full_setup(self) -> bool:
        """Run complete automated setup"""
        print("🚀 Starting automated CDC pipeline setup...\n")
        
        # Step 1: Check and start services
        if not self.check_docker_services():
            if not self.start_services():
                print("❌ Failed to start services")
                return False
        
        # Step 2: Fix MySQL permissions
        if not self.fix_mysql_permissions():
            print("❌ Failed to fix MySQL permissions")
            return False
        
        # Step 3: Restart Kafka Connect
        if not self.restart_kafka_connect():
            print("❌ Failed to restart Kafka Connect")
            return False
        
        # Step 4: Register Debezium connector
        if not self.register_debezium_connector():
            print("❌ Failed to register Debezium connector")
            return False
        
        # Step 5: Check connector status
        time.sleep(10)  # Wait for connector to initialize
        if not self.check_connector_status():
            print("⚠️  Connector may not be running properly")
        
        # Step 6: Create OpenSearch indices
        if not self.create_opensearch_indices():
            print("❌ Failed to create OpenSearch indices")
            return False
        
        # Step 7: Check UI requirements
        ui_status = self.check_ui_requirements()
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Service URLs:")
        print("   - Kafka UI: http://localhost:8080")
        print("   - OpenSearch Dashboards: http://localhost:5601")
        print("   - Kafka Connect API: http://localhost:8083")
        print("   - OpenSearch API: http://localhost:9200")
        print("   - Search API: http://localhost:8000")
        print("   - MySQL: localhost:3306")
        
        return True

def main():
    setup = CDCPipelineSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        # Only check status, don't fix anything
        setup.check_docker_services()
        setup.check_ui_requirements()
    else:
        # Run full automated setup
        success = setup.run_full_setup()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()