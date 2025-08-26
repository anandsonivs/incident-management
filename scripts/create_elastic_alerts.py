#!/usr/bin/env python3
"""
Elastic APM Alert Management Script

This script automatically creates comprehensive monitoring alerts for all services
in Elastic APM and integrates them with the incident management system.

Features:
- Automatic alert creation for latency, error rate, throughput, CPU, memory, disk
- Alert categorization based on incident severities
- Team-based alert assignment
- Automatic integration with incident management system
- Comprehensive tagging and metadata
"""

import json
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import argparse
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('elastic_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels matching incident management system."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class MetricType(Enum):
    """Types of metrics to monitor."""
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    JVM_HEAP = "jvm_heap"
    JVM_GC = "jvm_gc"
    DATABASE_CONNECTIONS = "database_connections"
    CACHE_HIT_RATE = "cache_hit_rate"

@dataclass
class AlertConfig:
    """Configuration for creating alerts."""
    name: str
    description: str
    severity: AlertSeverity
    metric_type: MetricType
    threshold: float
    window_size: str = "5m"
    evaluation_periods: int = 1
    team_id: Optional[int] = None
    service_pattern: Optional[str] = None
    environment: Optional[str] = None

class ElasticAlertManager:
    """Manages Elastic APM alerts and integrates with incident management."""
    
    def __init__(self, elastic_url: str, elastic_api_key: str, incident_api_url: str, incident_api_token: str):
        self.elastic_url = elastic_url.rstrip('/')
        self.elastic_api_key = elastic_api_key
        self.incident_api_url = incident_api_url.rstrip('/')
        self.incident_api_token = incident_api_token
        
        self.headers = {
            'Authorization': f'ApiKey {elastic_api_key}',
            'Content-Type': 'application/json',
            'kbn-xsrf': 'true'
        }
        
        self.incident_headers = {
            'Authorization': f'Bearer {incident_api_token}',
            'Content-Type': 'application/json'
        }
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get all services from Elastic APM."""
        try:
            url = f"{self.elastic_url}/api/apm/services"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            services = response.json()
            logger.info(f"Found {len(services)} services in Elastic APM")
            return services
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return []
    
    def create_alert_rule(self, alert_config: AlertConfig, service_name: str) -> Optional[str]:
        """Create an alert rule in Elastic."""
        try:
            # Build the alert rule based on metric type
            rule = self._build_alert_rule(alert_config, service_name)
            
            url = f"{self.elastic_url}/api/alerting/rule"
            response = requests.post(url, headers=self.headers, json=rule)
            response.raise_for_status()
            
            rule_id = response.json().get('id')
            logger.info(f"Created alert rule '{alert_config.name}' for service '{service_name}' with ID: {rule_id}")
            return rule_id
            
        except Exception as e:
            logger.error(f"Failed to create alert rule for {service_name}: {e}")
            return None
    
    def _build_alert_rule(self, alert_config: AlertConfig, service_name: str) -> Dict[str, Any]:
        """Build the alert rule configuration based on metric type."""
        
        # Base rule structure
        rule = {
            "name": f"{alert_config.name} - {service_name}",
            "tags": [
                f"service:{service_name}",
                f"metric:{alert_config.metric_type.value}",
                f"severity:{alert_config.severity.value}",
                "auto-generated",
                "incident-management"
            ],
            "consumer": "alerts",
            "rule_type_id": "apm.anomaly",
            "schedule": {
                "interval": "1m"
            },
            "actions": [
                {
                    "group": "threshold_met",
                    "id": "webhook",
                    "params": {
                        "body": json.dumps({
                            "alert_name": f"{alert_config.name} - {service_name}",
                            "message": f"{alert_config.description} for service {service_name}",
                            "severity": alert_config.severity.value,
                            "service": {
                                "name": service_name,
                                "environment": alert_config.environment or "production"
                            },
                            "alert_id": "{{alert.id}}",
                            "state": {
                                "state": "active",
                                "timestamp": "{{alert.start}}"
                            },
                            "metadata": {
                                "metric_type": alert_config.metric_type.value,
                                "threshold": alert_config.threshold,
                                "window_size": alert_config.window_size,
                                "team_id": alert_config.team_id,
                                "rule_id": "{{alert.id}}"
                            },
                            "tags": {
                                "service": service_name,
                                "environment": alert_config.environment or "production",
                                "team_id": str(alert_config.team_id) if alert_config.team_id else "unassigned",
                                "metric_type": alert_config.metric_type.value,
                                "severity": alert_config.severity.value
                            }
                        }),
                        "method": "POST",
                        "url": f"{self.incident_api_url}/v1/alerts/elastic"
                    }
                }
            ],
            "notify_when": "onActionGroupChange",
            "params": {
                "serviceName": service_name,
                "environment": alert_config.environment or "production",
                "threshold": alert_config.threshold,
                "windowSize": alert_config.window_size,
                "aggregationType": "avg"
            }
        }
        
        # Add metric-specific configuration
        if alert_config.metric_type == MetricType.LATENCY:
            rule["params"]["metric"] = "transaction.duration.us"
            rule["params"]["aggregationType"] = "p95"
        elif alert_config.metric_type == MetricType.ERROR_RATE:
            rule["params"]["metric"] = "transaction.failure_rate"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.THROUGHPUT:
            rule["params"]["metric"] = "transaction.throughput"
            rule["params"]["aggregationType"] = "sum"
        elif alert_config.metric_type == MetricType.CPU_USAGE:
            rule["params"]["metric"] = "system.cpu.total.norm.pct"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.MEMORY_USAGE:
            rule["params"]["metric"] = "system.memory.actual.used.pct"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.DISK_USAGE:
            rule["params"]["metric"] = "system.diskio.used.pct"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.JVM_HEAP:
            rule["params"]["metric"] = "jvm.memory.heap.used.pct"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.JVM_GC:
            rule["params"]["metric"] = "jvm.gc.old.rate"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.DATABASE_CONNECTIONS:
            rule["params"]["metric"] = "db.connections.active"
            rule["params"]["aggregationType"] = "avg"
        elif alert_config.metric_type == MetricType.CACHE_HIT_RATE:
            rule["params"]["metric"] = "cache.hit_rate"
            rule["params"]["aggregationType"] = "avg"
        
        return rule
    
    def create_team_if_not_exists(self, team_name: str, team_description: str) -> Optional[int]:
        """Create a team in the incident management system if it doesn't exist."""
        try:
            # First, try to get existing teams
            response = requests.get(f"{self.incident_api_url}/v1/teams/", headers=self.incident_headers)
            response.raise_for_status()
            
            teams = response.json()
            for team in teams:
                if team.get('name') == team_name:
                    logger.info(f"Team '{team_name}' already exists with ID: {team['id']}")
                    return team['id']
            
            # Create new team
            team_data = {
                "name": team_name,
                "description": team_description,
                "is_active": True
            }
            
            response = requests.post(f"{self.incident_api_url}/v1/teams/", 
                                   headers=self.incident_headers, json=team_data)
            response.raise_for_status()
            
            team_id = response.json().get('id')
            logger.info(f"Created team '{team_name}' with ID: {team_id}")
            return team_id
            
        except Exception as e:
            logger.error(f"Failed to create team '{team_name}': {e}")
            return None

class AlertTemplateManager:
    """Manages alert templates for different service types and environments."""
    
    def __init__(self, thresholds_file: str = "config/alert_thresholds.json"):
        """Initialize with thresholds configuration file."""
        self.thresholds_file = thresholds_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the thresholds configuration file."""
        try:
            with open(self.thresholds_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded alert thresholds configuration from {self.thresholds_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load thresholds configuration: {e}")
            return {}
    
    def get_thresholds_for_service(self, service_name: str, environment: str = "production") -> Dict[str, Any]:
        """Get thresholds for a specific service, applying overrides in order: global -> service-specific -> environment."""
        thresholds = {}
        
        # Start with global thresholds
        if "global_thresholds" in self.config:
            thresholds.update(self.config["global_thresholds"])
        
        # Apply service-specific overrides
        if "service_specific_thresholds" in self.config and service_name in self.config["service_specific_thresholds"]:
            service_thresholds = self.config["service_specific_thresholds"][service_name]
            for metric, values in service_thresholds.items():
                if metric in thresholds:
                    thresholds[metric].update(values)
                else:
                    thresholds[metric] = values
        
        # Apply environment overrides
        if "environment_overrides" in self.config and environment in self.config["environment_overrides"]:
            env_thresholds = self.config["environment_overrides"][environment]
            for metric, values in env_thresholds.items():
                if metric in thresholds:
                    thresholds[metric].update(values)
                else:
                    thresholds[metric] = values
        
        return thresholds
    
    def get_window_size(self, metric_type: MetricType, severity: AlertSeverity) -> str:
        """Get window size for a metric type and severity."""
        if "window_sizes" in self.config:
            metric_name = metric_type.value
            severity_name = severity.value
            if metric_name in self.config["window_sizes"]:
                if severity_name in self.config["window_sizes"][metric_name]:
                    return self.config["window_sizes"][metric_name][severity_name]
        
        # Default window sizes
        default_windows = {
            MetricType.LATENCY: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.ERROR_RATE: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.THROUGHPUT: {"low": "15m", "medium": "12m", "high": "10m", "critical": "5m"},
            MetricType.CPU_USAGE: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.MEMORY_USAGE: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.DISK_USAGE: {"low": "15m", "medium": "12m", "high": "10m", "critical": "5m"},
            MetricType.JVM_HEAP: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.JVM_GC: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.DATABASE_CONNECTIONS: {"low": "10m", "medium": "8m", "high": "5m", "critical": "2m"},
            MetricType.CACHE_HIT_RATE: {"low": "15m", "medium": "12m", "high": "10m", "critical": "5m"}
        }
        
        return default_windows.get(metric_type, {}).get(severity.value, "5m")
    
    def get_evaluation_periods(self, severity: AlertSeverity) -> int:
        """Get evaluation periods for a severity level."""
        if "evaluation_periods" in self.config:
            return self.config["evaluation_periods"].get(severity.value, 1)
        return 1
    
    def create_alerts_for_service(self, service_name: str, environment: str = "production") -> List[AlertConfig]:
        """Create alert configurations for a specific service."""
        thresholds = self.get_thresholds_for_service(service_name, environment)
        alerts = []
        
        # Create alerts for each metric type and severity level
        for metric_name, metric_thresholds in thresholds.items():
            try:
                metric_type = MetricType(metric_name)
            except ValueError:
                logger.warning(f"Unknown metric type: {metric_name}")
                continue
            
            # Create alerts for each severity level
            for severity_name, threshold_value in metric_thresholds.items():
                if severity_name in ["unit", "description"]:
                    continue
                
                try:
                    severity = AlertSeverity(severity_name)
                except ValueError:
                    logger.warning(f"Unknown severity level: {severity_name}")
                    continue
                
                # Skip if threshold is not a number
                if not isinstance(threshold_value, (int, float)):
                    continue
                
                # Create alert configuration
                alert_name = f"{severity_name.title()} {metric_name.replace('_', ' ').title()} Alert"
                description = f"Service {metric_name.replace('_', ' ')} is at {severity_name} level"
                
                # Special handling for cache hit rate (higher is better)
                if metric_type == MetricType.CACHE_HIT_RATE:
                    if severity in [AlertSeverity.LOW, AlertSeverity.MEDIUM]:
                        description = f"Cache hit rate is below {severity_name} threshold"
                    else:
                        description = f"Cache hit rate is critically low"
                
                # Special handling for throughput (lower is worse)
                elif metric_type == MetricType.THROUGHPUT:
                    if severity in [AlertSeverity.LOW, AlertSeverity.MEDIUM]:
                        description = f"Service throughput is below {severity_name} threshold"
                    else:
                        description = f"Service throughput is critically low"
                
                alert_config = AlertConfig(
                    name=alert_name,
                    description=description,
                    severity=severity,
                    metric_type=metric_type,
                    threshold=threshold_value,
                    window_size=self.get_window_size(metric_type, severity),
                    evaluation_periods=self.get_evaluation_periods(severity)
                )
                
                alerts.append(alert_config)
        
        return alerts

def main():
    """Main function to create alerts for all services."""
    parser = argparse.ArgumentParser(description='Create Elastic APM alerts for all services')
    parser.add_argument('--elastic-url', required=True, help='Elastic APM URL')
    parser.add_argument('--elastic-api-key', required=True, help='Elastic API key')
    parser.add_argument('--incident-api-url', required=True, help='Incident management API URL')
    parser.add_argument('--incident-api-token', required=True, help='Incident management API token')
    parser.add_argument('--team-mapping', help='JSON file with service to team mapping')
    parser.add_argument('--environment', default='production', help='Environment name')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual creation)')
    parser.add_argument('--service-pattern', help='Regex pattern to filter services')
    parser.add_argument('--thresholds-file', default='config/alert_thresholds.json', help='Alert thresholds configuration file')
    
    args = parser.parse_args()
    
    # Initialize alert manager and template manager
    alert_manager = ElasticAlertManager(
        elastic_url=args.elastic_url,
        elastic_api_key=args.elastic_api_key,
        incident_api_url=args.incident_api_url,
        incident_api_token=args.incident_api_token
    )
    
    template_manager = AlertTemplateManager(args.thresholds_file)
    
    # Load team mapping if provided
    team_mapping = {}
    if args.team_mapping:
        try:
            with open(args.team_mapping, 'r') as f:
                team_mapping = json.load(f)
            logger.info(f"Loaded team mapping for {len(team_mapping)} services")
        except Exception as e:
            logger.error(f"Failed to load team mapping: {e}")
    
    # Get all services
    services = alert_manager.get_services()
    if not services:
        logger.error("No services found. Exiting.")
        return
    
    # Filter services by pattern if provided
    if args.service_pattern:
        import re
        pattern = re.compile(args.service_pattern)
        services = [s for s in services if pattern.match(s.get('serviceName', ''))]
        logger.info(f"Filtered to {len(services)} services matching pattern: {args.service_pattern}")
    
    # Create alerts for each service
    created_alerts = 0
    failed_alerts = 0
    
    for service in services:
        service_name = service.get('serviceName', 'unknown')
        logger.info(f"Processing service: {service_name}")
        
        # Get team ID for this service
        team_id = None
        if service_name in team_mapping:
            team_name = team_mapping[service_name]['team_name']
            team_description = team_mapping[service_name].get('description', f'Team for {service_name}')
            
            if not args.dry_run:
                team_id = alert_manager.create_team_if_not_exists(team_name, team_description)
            else:
                logger.info(f"[DRY RUN] Would create team: {team_name}")
        
        # Get service-specific alerts using the new template manager
        alerts = template_manager.create_alerts_for_service(service_name, args.environment)
        
        # Create alerts for this service
        for alert_config in alerts:
            alert_config.team_id = team_id
            alert_config.environment = args.environment
            
            if args.dry_run:
                logger.info(f"[DRY RUN] Would create alert: {alert_config.name} for {service_name} (threshold: {alert_config.threshold}, window: {alert_config.window_size})")
                created_alerts += 1
            else:
                rule_id = alert_manager.create_alert_rule(alert_config, service_name)
                if rule_id:
                    created_alerts += 1
                else:
                    failed_alerts += 1
        
        # Add delay to avoid overwhelming the API
        time.sleep(1)
    
    # Summary
    logger.info(f"Alert creation completed!")
    logger.info(f"Services processed: {len(services)}")
    logger.info(f"Alerts created: {created_alerts}")
    logger.info(f"Alerts failed: {failed_alerts}")
    
    if args.dry_run:
        logger.info("This was a dry run. No actual alerts were created.")

if __name__ == "__main__":
    main()
