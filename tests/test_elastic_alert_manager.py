import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from scripts.create_elastic_alerts import (
    ElasticAlertManager,
    AlertConfig,
    AlertSeverity,
    MetricType
)


class TestElasticAlertManager:
    """Test cases for ElasticAlertManager class."""
    
    @pytest.fixture
    def alert_manager(self):
        """Create a test instance of ElasticAlertManager."""
        return ElasticAlertManager(
            elastic_url="https://test-elastic.com",
            elastic_api_key="test-api-key",
            incident_api_url="http://localhost:8000",
            incident_api_token="test-token"
        )
    
    @pytest.fixture
    def sample_services(self):
        """Sample services data from Elastic APM."""
        return [
            {"serviceName": "api-gateway", "environment": "production"},
            {"serviceName": "user-service", "environment": "production"},
            {"serviceName": "payment-service", "environment": "production"},
            {"serviceName": "database-service", "environment": "production"}
        ]
    
    @pytest.fixture
    def sample_teams(self):
        """Sample teams data from incident management system."""
        return [
            {"id": 1, "name": "Platform Team", "description": "Platform infrastructure team"},
            {"id": 2, "name": "User Management Team", "description": "User management team"},
            {"id": 3, "name": "Payment Team", "description": "Payment processing team"}
        ]
    
    def test_init(self, alert_manager):
        """Test ElasticAlertManager initialization."""
        assert alert_manager.elastic_url == "https://test-elastic.com"
        assert alert_manager.elastic_api_key == "test-api-key"
        assert alert_manager.incident_api_url == "http://localhost:8000"
        assert alert_manager.incident_api_token == "test-token"
        
        # Check headers
        assert alert_manager.headers["Authorization"] == "ApiKey test-api-key"
        assert alert_manager.headers["Content-Type"] == "application/json"
        assert alert_manager.headers["kbn-xsrf"] == "true"
        
        assert alert_manager.incident_headers["Authorization"] == "Bearer test-token"
        assert alert_manager.incident_headers["Content-Type"] == "application/json"
    
    @patch('scripts.create_elastic_alerts.requests.get')
    def test_get_services_success(self, mock_get, alert_manager, sample_services):
        """Test successful retrieval of services from Elastic APM."""
        mock_response = Mock()
        mock_response.json.return_value = sample_services
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        services = alert_manager.get_services()
        
        assert services == sample_services
        mock_get.assert_called_once_with(
            "https://test-elastic.com/api/apm/services",
            headers=alert_manager.headers
        )
    
    @patch('scripts.create_elastic_alerts.requests.get')
    def test_get_services_failure(self, mock_get, alert_manager):
        """Test handling of service retrieval failure."""
        mock_get.side_effect = Exception("Connection failed")
        
        services = alert_manager.get_services()
        
        assert services == []
    
    @patch('scripts.create_elastic_alerts.requests.post')
    def test_create_alert_rule_success(self, mock_post, alert_manager):
        """Test successful alert rule creation."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "rule-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        alert_config = AlertConfig(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.HIGH,
            metric_type=MetricType.LATENCY,
            threshold=1000.0
        )
        
        rule_id = alert_manager.create_alert_rule(alert_config, "test-service")
        
        assert rule_id == "rule-123"
        mock_post.assert_called_once()
        
        # Verify the request payload
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://test-elastic.com/api/alerting/rule"
        assert call_args[1]["headers"] == alert_manager.headers
        
        payload = call_args[1]["json"]
        assert payload["name"] == "Test Alert - test-service"
        assert "service:test-service" in payload["tags"]
        assert "metric:latency" in payload["tags"]
        assert "severity:high" in payload["tags"]
    
    @patch('scripts.create_elastic_alerts.requests.post')
    def test_create_alert_rule_failure(self, mock_post, alert_manager):
        """Test handling of alert rule creation failure."""
        mock_post.side_effect = Exception("Creation failed")
        
        alert_config = AlertConfig(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.HIGH,
            metric_type=MetricType.LATENCY,
            threshold=1000.0
        )
        
        rule_id = alert_manager.create_alert_rule(alert_config, "test-service")
        
        assert rule_id is None
    
    def test_build_alert_rule_latency(self, alert_manager):
        """Test building alert rule for latency metric."""
        alert_config = AlertConfig(
            name="High Latency Alert",
            description="Service response time is high",
            severity=AlertSeverity.HIGH,
            metric_type=MetricType.LATENCY,
            threshold=1000.0,
            window_size="5m",
            team_id=1,
            environment="production"
        )
        
        rule = alert_manager._build_alert_rule(alert_config, "api-gateway")
        
        assert rule["name"] == "High Latency Alert - api-gateway"
        assert rule["params"]["metric"] == "transaction.duration.us"
        assert rule["params"]["aggregationType"] == "p95"
        assert rule["params"]["threshold"] == 1000.0
        assert rule["params"]["windowSize"] == "5m"
        assert rule["params"]["serviceName"] == "api-gateway"
        assert rule["params"]["environment"] == "production"
        
        # Check webhook action
        actions = rule["actions"]
        assert len(actions) == 1
        action = actions[0]
        assert action["group"] == "threshold_met"
        assert action["id"] == "webhook"
        
        webhook_body = json.loads(action["params"]["body"])
        assert webhook_body["alert_name"] == "High Latency Alert - api-gateway"
        assert webhook_body["severity"] == "high"
        assert webhook_body["service"]["name"] == "api-gateway"
        assert webhook_body["metadata"]["team_id"] == 1
        assert webhook_body["tags"]["team_id"] == "1"
    
    def test_build_alert_rule_error_rate(self, alert_manager):
        """Test building alert rule for error rate metric."""
        alert_config = AlertConfig(
            name="High Error Rate Alert",
            description="Service error rate is high",
            severity=AlertSeverity.CRITICAL,
            metric_type=MetricType.ERROR_RATE,
            threshold=0.05,
            window_size="2m"
        )
        
        rule = alert_manager._build_alert_rule(alert_config, "user-service")
        
        assert rule["params"]["metric"] == "transaction.failure_rate"
        assert rule["params"]["aggregationType"] == "avg"
        assert rule["params"]["threshold"] == 0.05
        assert rule["params"]["windowSize"] == "2m"
    
    def test_build_alert_rule_cpu_usage(self, alert_manager):
        """Test building alert rule for CPU usage metric."""
        alert_config = AlertConfig(
            name="High CPU Usage Alert",
            description="Service CPU usage is high",
            severity=AlertSeverity.HIGH,
            metric_type=MetricType.CPU_USAGE,
            threshold=0.80
        )
        
        rule = alert_manager._build_alert_rule(alert_config, "monitoring-service")
        
        assert rule["params"]["metric"] == "system.cpu.total.norm.pct"
        assert rule["params"]["aggregationType"] == "avg"
        assert rule["params"]["threshold"] == 0.80
    
    def test_build_alert_rule_cache_hit_rate(self, alert_manager):
        """Test building alert rule for cache hit rate metric."""
        alert_config = AlertConfig(
            name="Low Cache Hit Rate Alert",
            description="Cache hit rate is low",
            severity=AlertSeverity.MEDIUM,
            metric_type=MetricType.CACHE_HIT_RATE,
            threshold=0.70
        )
        
        rule = alert_manager._build_alert_rule(alert_config, "redis-service")
        
        assert rule["params"]["metric"] == "cache.hit_rate"
        assert rule["params"]["aggregationType"] == "avg"
        assert rule["params"]["threshold"] == 0.70
    
    @patch('scripts.create_elastic_alerts.requests.get')
    @patch('scripts.create_elastic_alerts.requests.post')
    def test_create_team_if_not_exists_new_team(self, mock_post, mock_get, alert_manager, sample_teams):
        """Test creating a new team when it doesn't exist."""
        # Mock getting existing teams
        mock_get_response = Mock()
        mock_get_response.json.return_value = sample_teams
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Mock creating new team
        mock_post_response = Mock()
        mock_post_response.json.return_value = {"id": 4}
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response
        
        team_id = alert_manager.create_team_if_not_exists("New Team", "New team description")
        
        assert team_id == 4
        
        # Verify team creation call
        mock_post.assert_called_once_with(
            "http://localhost:8000/v1/teams/",
            headers=alert_manager.incident_headers,
            json={
                "name": "New Team",
                "description": "New team description",
                "is_active": True
            }
        )
    
    @patch('scripts.create_elastic_alerts.requests.get')
    def test_create_team_if_not_exists_existing_team(self, mock_get, alert_manager, sample_teams):
        """Test handling when team already exists."""
        mock_response = Mock()
        mock_response.json.return_value = sample_teams
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        team_id = alert_manager.create_team_if_not_exists("Platform Team", "Platform infrastructure team")
        
        assert team_id == 1  # Should return existing team ID
    
    @patch('scripts.create_elastic_alerts.requests.get')
    def test_create_team_if_not_exists_failure(self, mock_get, alert_manager):
        """Test handling of team creation failure."""
        mock_get.side_effect = Exception("API failed")
        
        team_id = alert_manager.create_team_if_not_exists("New Team", "Description")
        
        assert team_id is None


class TestAlertConfig:
    """Test cases for AlertConfig dataclass."""
    
    def test_alert_config_creation(self):
        """Test AlertConfig creation with all parameters."""
        alert_config = AlertConfig(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.HIGH,
            metric_type=MetricType.LATENCY,
            threshold=1000.0,
            window_size="5m",
            evaluation_periods=2,
            team_id=1,
            service_pattern="api.*",
            environment="production"
        )
        
        assert alert_config.name == "Test Alert"
        assert alert_config.description == "Test description"
        assert alert_config.severity == AlertSeverity.HIGH
        assert alert_config.metric_type == MetricType.LATENCY
        assert alert_config.threshold == 1000.0
        assert alert_config.window_size == "5m"
        assert alert_config.evaluation_periods == 2
        assert alert_config.team_id == 1
        assert alert_config.service_pattern == "api.*"
        assert alert_config.environment == "production"
    
    def test_alert_config_defaults(self):
        """Test AlertConfig creation with default values."""
        alert_config = AlertConfig(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.MEDIUM,
            metric_type=MetricType.ERROR_RATE,
            threshold=0.05
        )
        
        assert alert_config.window_size == "5m"
        assert alert_config.evaluation_periods == 1
        assert alert_config.team_id is None
        assert alert_config.service_pattern is None
        assert alert_config.environment is None


class TestEnums:
    """Test cases for enum classes."""
    
    def test_alert_severity_enum(self):
        """Test AlertSeverity enum values."""
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.LOW.value == "low"
    
    def test_metric_type_enum(self):
        """Test MetricType enum values."""
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.ERROR_RATE.value == "error_rate"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.CPU_USAGE.value == "cpu_usage"
        assert MetricType.MEMORY_USAGE.value == "memory_usage"
        assert MetricType.DISK_USAGE.value == "disk_usage"
        assert MetricType.JVM_HEAP.value == "jvm_heap"
        assert MetricType.JVM_GC.value == "jvm_gc"
        assert MetricType.DATABASE_CONNECTIONS.value == "database_connections"
        assert MetricType.CACHE_HIT_RATE.value == "cache_hit_rate"
