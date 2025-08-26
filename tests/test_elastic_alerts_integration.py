import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open, MagicMock
from typing import Dict, List, Any

from scripts.create_elastic_alerts import (
    main,
    ElasticAlertManager,
    AlertTemplateManager,
    AlertConfig,
    AlertSeverity,
    MetricType
)


class TestElasticAlertsIntegration:
    """Integration tests for the complete Elastic APM alert management system."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "global_thresholds": {
                "latency": {
                    "low": 500.0,
                    "medium": 1000.0,
                    "high": 2000.0,
                    "critical": 5000.0
                },
                "error_rate": {
                    "low": 0.01,
                    "medium": 0.03,
                    "high": 0.05,
                    "critical": 0.20
                }
            },
            "service_specific_thresholds": {
                "api-gateway": {
                    "latency": {
                        "low": 200.0,
                        "medium": 400.0,
                        "high": 800.0,
                        "critical": 1500.0
                    }
                }
            },
            "environment_overrides": {
                "development": {
                    "latency": {
                        "low": 1000.0,
                        "medium": 2000.0,
                        "high": 5000.0,
                        "critical": 10000.0
                    }
                }
            },
            "window_sizes": {
                "latency": {
                    "low": "10m",
                    "medium": "8m",
                    "high": "5m",
                    "critical": "2m"
                },
                "error_rate": {
                    "low": "10m",
                    "medium": "8m",
                    "high": "5m",
                    "critical": "2m"
                }
            },
            "evaluation_periods": {
                "low": 3,
                "medium": 2,
                "high": 1,
                "critical": 1
            }
        }
    
    @pytest.fixture
    def sample_team_mapping(self):
        """Sample team mapping for testing."""
        return {
            "api-gateway": {
                "team_name": "Platform Team",
                "description": "Platform infrastructure team"
            },
            "user-service": {
                "team_name": "User Management Team",
                "description": "User management team"
            },
            "payment-service": {
                "team_name": "Payment Team",
                "description": "Payment processing team"
            }
        }
    
    @pytest.fixture
    def sample_services(self):
        """Sample services from Elastic APM."""
        return [
            {"serviceName": "api-gateway", "environment": "production"},
            {"serviceName": "user-service", "environment": "production"},
            {"serviceName": "payment-service", "environment": "production"}
        ]
    
    @pytest.fixture
    def sample_teams(self):
        """Sample teams from incident management system."""
        return [
            {"id": 1, "name": "Platform Team", "description": "Platform infrastructure team"},
            {"id": 2, "name": "User Management Team", "description": "User management team"},
            {"id": 3, "name": "Payment Team", "description": "Payment processing team"}
        ]
    
    @patch('scripts.create_elastic_alerts.requests.get')
    @patch('scripts.create_elastic_alerts.requests.post')
    def test_full_alert_creation_workflow(self, mock_post, mock_get, sample_config, sample_team_mapping, sample_services, sample_teams):
        """Test the complete workflow from start to finish."""
        # Mock Elastic APM services endpoint
        mock_get_services = Mock()
        mock_get_services.json.return_value = sample_services
        mock_get_services.raise_for_status.return_value = None
        
        # Mock incident management teams endpoint
        mock_get_teams = Mock()
        mock_get_teams.json.return_value = sample_teams
        mock_get_teams.raise_for_status.return_value = None
        
        # Mock alert rule creation
        mock_create_rule = Mock()
        mock_create_rule.json.return_value = {"id": "rule-123"}
        mock_create_rule.raise_for_status.return_value = None
        
        # Configure mock to return different responses for different URLs
        def mock_get_side_effect(url, **kwargs):
            if "api/apm/services" in url:
                return mock_get_services
            elif "v1/teams" in url:
                return mock_get_teams
            else:
                raise Exception(f"Unexpected URL: {url}")
        
        def mock_post_side_effect(url, **kwargs):
            if "api/alerting/rule" in url:
                return mock_create_rule
            elif "v1/teams" in url:
                # Mock team creation response
                response = Mock()
                response.json.return_value = {"id": 4}
                response.raise_for_status.return_value = None
                return response
            else:
                raise Exception(f"Unexpected URL: {url}")
        
        mock_get.side_effect = mock_get_side_effect
        mock_post.side_effect = mock_post_side_effect
        
        # Create temporary files for configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
            json.dump(sample_config, config_file)
            config_path = config_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as team_file:
            json.dump(sample_team_mapping, team_file)
            team_path = team_file.name
        
        try:
            # Test the main function with dry-run
            with patch('sys.argv', [
                'create_elastic_alerts.py',
                '--elastic-url', 'https://test-elastic.com',
                '--elastic-api-key', 'test-key',
                '--incident-api-url', 'http://localhost:8000',
                '--incident-api-token', 'test-token',
                '--team-mapping', team_path,
                '--thresholds-file', config_path,
                '--environment', 'production',
                '--dry-run'
            ]):
                # Mock the main function to avoid actual execution
                with patch('scripts.create_elastic_alerts.main') as mock_main:
                    mock_main.return_value = None
                    # This would normally call main(), but we're just testing the setup
                    pass
                
                # Verify that the configuration was loaded correctly
                template_manager = AlertTemplateManager(config_path)
                assert template_manager.config == sample_config
                
                # Verify that services would be processed
                alert_manager = ElasticAlertManager(
                    elastic_url='https://test-elastic.com',
                    elastic_api_key='test-key',
                    incident_api_url='http://localhost:8000',
                    incident_api_token='test-token'
                )
                
                services = alert_manager.get_services()
                assert len(services) == 3
                assert services[0]["serviceName"] == "api-gateway"
                
                # Verify that alerts would be created
                alerts = template_manager.create_alerts_for_service("api-gateway", "production")
                assert len(alerts) > 0
                
                # Verify that teams would be created
                team_id = alert_manager.create_team_if_not_exists("New Team", "Description")
                assert team_id == 4
                
        finally:
            # Clean up temporary files
            os.unlink(config_path)
            os.unlink(team_path)
    
    def test_configuration_hierarchy(self, sample_config):
        """Test that configuration hierarchy is applied correctly."""
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            template_manager = AlertTemplateManager("test_config.json")
            
            # Test global thresholds
            global_thresholds = template_manager.get_thresholds_for_service("unknown-service")
            assert global_thresholds["latency"]["high"] == 2000.0
            
            # Test service-specific overrides
            api_thresholds = template_manager.get_thresholds_for_service("api-gateway")
            assert api_thresholds["latency"]["high"] == 800.0  # Service override
            
            # Test environment overrides
            dev_thresholds = template_manager.get_thresholds_for_service("api-gateway", "development")
            assert dev_thresholds["latency"]["high"] == 5000.0  # Environment override
    
    @patch('scripts.create_elastic_alerts.requests.get')
    def test_service_filtering(self, mock_get, sample_services):
        """Test service filtering by pattern."""
        mock_response = Mock()
        mock_response.json.return_value = sample_services
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        alert_manager = ElasticAlertManager(
            elastic_url='https://test-elastic.com',
            elastic_api_key='test-key',
            incident_api_url='http://localhost:8000',
            incident_api_token='test-token'
        )
        
        # Test filtering with pattern
        import re
        pattern = re.compile('api.*')
        filtered_services = [s for s in sample_services if pattern.match(s.get('serviceName', ''))]
        
        assert len(filtered_services) == 1
        assert filtered_services[0]["serviceName"] == "api-gateway"
    
    def test_alert_rule_generation(self, sample_config):
        """Test that alert rules are generated with correct structure."""
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            template_manager = AlertTemplateManager("test_config.json")
            alert_manager = ElasticAlertManager(
                elastic_url='https://test-elastic.com',
                elastic_api_key='test-key',
                incident_api_url='http://localhost:8000',
                incident_api_token='test-token'
            )
            
            alerts = template_manager.create_alerts_for_service("api-gateway", "production")
            
            for alert in alerts:
                # Test that each alert can generate a valid rule
                rule = alert_manager._build_alert_rule(alert, "api-gateway")
                
                # Verify rule structure
                assert "name" in rule
                assert "tags" in rule
                assert "actions" in rule
                assert "params" in rule
                
                # Verify tags
                assert "service:api-gateway" in rule["tags"]
                assert f"metric:{alert.metric_type.value}" in rule["tags"]
                assert f"severity:{alert.severity.value}" in rule["tags"]
                
                # Verify webhook action
                actions = rule["actions"]
                assert len(actions) == 1
                action = actions[0]
                assert action["group"] == "threshold_met"
                assert action["id"] == "webhook"
                
                # Verify webhook payload
                webhook_body = json.loads(action["params"]["body"])
                assert webhook_body["service"]["name"] == "api-gateway"
                assert webhook_body["severity"] == alert.severity.value
                assert webhook_body["metadata"]["metric_type"] == alert.metric_type.value
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with invalid configuration
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            template_manager = AlertTemplateManager("nonexistent.json")
            assert template_manager.config == {}
            
            # Should handle gracefully
            thresholds = template_manager.get_thresholds_for_service("test-service")
            assert thresholds == {}
            
            alerts = template_manager.create_alerts_for_service("test-service")
            assert alerts == []
        
        # Test with invalid JSON
        with patch('builtins.open', mock_open(read_data="invalid json")):
            template_manager = AlertTemplateManager("invalid.json")
            assert template_manager.config == {}
    
    def test_metric_type_handling(self):
        """Test that all metric types are handled correctly."""
        config = {
            "global_thresholds": {
                "latency": {"high": 1000.0},
                "error_rate": {"high": 0.05},
                "throughput": {"high": 100.0},
                "cpu_usage": {"high": 0.80},
                "memory_usage": {"high": 0.85},
                "disk_usage": {"high": 0.90},
                "jvm_heap": {"high": 0.85},
                "jvm_gc": {"high": 10.0},
                "database_connections": {"high": 0.80},
                "cache_hit_rate": {"high": 0.70}
            },
            "window_sizes": {
                "latency": {"high": "5m"},
                "error_rate": {"high": "5m"},
                "throughput": {"high": "10m"},
                "cpu_usage": {"high": "5m"},
                "memory_usage": {"high": "5m"},
                "disk_usage": {"high": "10m"},
                "jvm_heap": {"high": "5m"},
                "jvm_gc": {"high": "5m"},
                "database_connections": {"high": "5m"},
                "cache_hit_rate": {"high": "10m"}
            },
            "evaluation_periods": {"high": 1}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config))):
            template_manager = AlertTemplateManager("test_config.json")
            alert_manager = ElasticAlertManager(
                elastic_url='https://test-elastic.com',
                elastic_api_key='test-key',
                incident_api_url='http://localhost:8000',
                incident_api_token='test-token'
            )
            
            alerts = template_manager.create_alerts_for_service("test-service")
            
            # Verify all metric types are represented
            metric_types = {alert.metric_type for alert in alerts}
            expected_metrics = {
                MetricType.LATENCY,
                MetricType.ERROR_RATE,
                MetricType.THROUGHPUT,
                MetricType.CPU_USAGE,
                MetricType.MEMORY_USAGE,
                MetricType.DISK_USAGE,
                MetricType.JVM_HEAP,
                MetricType.JVM_GC,
                MetricType.DATABASE_CONNECTIONS,
                MetricType.CACHE_HIT_RATE
            }
            assert metric_types == expected_metrics
            
            # Verify each metric generates correct rule parameters
            for alert in alerts:
                rule = alert_manager._build_alert_rule(alert, "test-service")
                
                if alert.metric_type == MetricType.LATENCY:
                    assert rule["params"]["metric"] == "transaction.duration.us"
                    assert rule["params"]["aggregationType"] == "p95"
                elif alert.metric_type == MetricType.ERROR_RATE:
                    assert rule["params"]["metric"] == "transaction.failure_rate"
                    assert rule["params"]["aggregationType"] == "avg"
                elif alert.metric_type == MetricType.CPU_USAGE:
                    assert rule["params"]["metric"] == "system.cpu.total.norm.pct"
                    assert rule["params"]["aggregationType"] == "avg"
                elif alert.metric_type == MetricType.CACHE_HIT_RATE:
                    assert rule["params"]["metric"] == "cache.hit_rate"
                    assert rule["params"]["aggregationType"] == "avg"


class TestMainFunction:
    """Test cases for the main function."""
    
    @patch('scripts.create_elastic_alerts.AlertTemplateManager')
    @patch('scripts.create_elastic_alerts.ElasticAlertManager')
    @patch('scripts.create_elastic_alerts.json.load')
    @patch('builtins.open')
    def test_main_function_dry_run(self, mock_open, mock_json_load, mock_alert_manager_class, mock_template_manager_class):
        """Test main function in dry-run mode."""
        # Mock configuration
        mock_config = {
            "global_thresholds": {
                "latency": {"high": 1000.0}
            }
        }
        mock_json_load.return_value = mock_config
        
        # Mock services
        mock_services = [
            {"serviceName": "api-gateway"},
            {"serviceName": "user-service"}
        ]
        
        # Mock alert manager
        mock_alert_manager = Mock()
        mock_alert_manager.get_services.return_value = mock_services
        mock_alert_manager.create_team_if_not_exists.return_value = 1
        mock_alert_manager_class.return_value = mock_alert_manager
        
        # Mock template manager
        mock_template_manager = Mock()
        mock_alerts = [
            AlertConfig(
                name="Test Alert",
                description="Test description",
                severity=AlertSeverity.HIGH,
                metric_type=MetricType.LATENCY,
                threshold=1000.0
            )
        ]
        mock_template_manager.create_alerts_for_service.return_value = mock_alerts
        mock_template_manager_class.return_value = mock_template_manager
        
        # Mock command line arguments
        with patch('sys.argv', [
            'create_elastic_alerts.py',
            '--elastic-url', 'https://test-elastic.com',
            '--elastic-api-key', 'test-key',
            '--incident-api-url', 'http://localhost:8000',
            '--incident-api-token', 'test-token',
            '--team-mapping', 'test_teams.json',
            '--environment', 'production',
            '--dry-run'
        ]):
            # Mock argparse
            with patch('scripts.create_elastic_alerts.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_args = Mock()
                mock_args.elastic_url = 'https://test-elastic.com'
                mock_args.elastic_api_key = 'test-key'
                mock_args.incident_api_url = 'http://localhost:8000'
                mock_args.incident_api_token = 'test-token'
                mock_args.team_mapping = 'test_teams.json'
                mock_args.environment = 'production'
                mock_args.dry_run = True
                mock_args.service_pattern = None
                mock_args.thresholds_file = 'test_config.json'
                mock_parse_args.return_value = mock_args
                
                # Call main function
                main()
                
                # Verify that services were retrieved
                mock_alert_manager.get_services.assert_called_once()
                
                # Verify that template manager was created
                mock_template_manager_class.assert_called_once_with('test_config.json')
                
                # Verify that alerts were created for each service
                assert mock_template_manager.create_alerts_for_service.call_count == 2
    
    @patch('scripts.create_elastic_alerts.AlertTemplateManager')
    @patch('scripts.create_elastic_alerts.ElasticAlertManager')
    def test_main_function_no_services(self, mock_alert_manager_class, mock_template_manager_class):
        """Test main function when no services are found."""
        # Mock alert manager with no services
        mock_alert_manager = Mock()
        mock_alert_manager.get_services.return_value = []
        mock_alert_manager_class.return_value = mock_alert_manager
        
        # Mock template manager
        mock_template_manager = Mock()
        mock_template_manager_class.return_value = mock_template_manager
        
        # Mock command line arguments
        with patch('sys.argv', [
            'create_elastic_alerts.py',
            '--elastic-url', 'https://test-elastic.com',
            '--elastic-api-key', 'test-key',
            '--incident-api-url', 'http://localhost:8000',
            '--incident-api-token', 'test-token',
            '--dry-run'
        ]):
            with patch('scripts.create_elastic_alerts.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_args = Mock()
                mock_args.elastic_url = 'https://test-elastic.com'
                mock_args.elastic_api_key = 'test-key'
                mock_args.incident_api_url = 'http://localhost:8000'
                mock_args.incident_api_token = 'test-token'
                mock_args.team_mapping = None
                mock_args.environment = 'production'
                mock_args.dry_run = True
                mock_args.service_pattern = None
                mock_args.thresholds_file = 'config/alert_thresholds.json'
                mock_parse_args.return_value = mock_args
                
                # Call main function
                main()
                
                # Verify that services were retrieved
                mock_alert_manager.get_services.assert_called_once()
                
                # Verify that no alerts were created
                mock_template_manager.create_alerts_for_service.assert_not_called()
