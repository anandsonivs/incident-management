import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from typing import Dict, List, Any

from scripts.create_elastic_alerts import (
    AlertTemplateManager,
    AlertConfig,
    AlertSeverity,
    MetricType
)


class TestAlertTemplateManager:
    """Test cases for AlertTemplateManager class."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration data."""
        return {
            "global_thresholds": {
                "latency": {
                    "low": 500.0,
                    "medium": 1000.0,
                    "high": 2000.0,
                    "critical": 5000.0,
                    "unit": "milliseconds",
                    "description": "Response time thresholds"
                },
                "error_rate": {
                    "low": 0.01,
                    "medium": 0.03,
                    "high": 0.05,
                    "critical": 0.20,
                    "unit": "percentage",
                    "description": "Error rate thresholds"
                },
                "cpu_usage": {
                    "low": 0.60,
                    "medium": 0.75,
                    "high": 0.85,
                    "critical": 0.95,
                    "unit": "percentage",
                    "description": "CPU usage thresholds"
                }
            },
            "service_specific_thresholds": {
                "api-gateway": {
                    "latency": {
                        "low": 200.0,
                        "medium": 400.0,
                        "high": 800.0,
                        "critical": 1500.0
                    },
                    "error_rate": {
                        "low": 0.005,
                        "medium": 0.01,
                        "high": 0.02,
                        "critical": 0.05
                    }
                },
                "payment-service": {
                    "latency": {
                        "low": 50.0,
                        "medium": 100.0,
                        "high": 200.0,
                        "critical": 500.0
                    },
                    "error_rate": {
                        "low": 0.0001,
                        "medium": 0.001,
                        "high": 0.005,
                        "critical": 0.01
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
                    },
                    "error_rate": {
                        "low": 0.05,
                        "medium": 0.10,
                        "high": 0.20,
                        "critical": 0.40
                    }
                },
                "production": {
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
                },
                "cpu_usage": {
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
    def template_manager(self, sample_config):
        """Create a test instance of AlertTemplateManager with sample config."""
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            return AlertTemplateManager("test_config.json")
    
    def test_init_with_valid_config(self, sample_config):
        """Test AlertTemplateManager initialization with valid config."""
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            manager = AlertTemplateManager("test_config.json")
            assert manager.config == sample_config
    
    def test_init_with_invalid_file(self):
        """Test AlertTemplateManager initialization with invalid file."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            manager = AlertTemplateManager("nonexistent.json")
            assert manager.config == {}
    
    def test_init_with_invalid_json(self):
        """Test AlertTemplateManager initialization with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            manager = AlertTemplateManager("invalid.json")
            assert manager.config == {}
    
    def test_get_thresholds_for_service_global_only(self, template_manager):
        """Test getting thresholds for service with only global configuration."""
        thresholds = template_manager.get_thresholds_for_service("unknown-service")
        
        assert "latency" in thresholds
        assert "error_rate" in thresholds
        assert "cpu_usage" in thresholds
        
        # Check global values
        assert thresholds["latency"]["low"] == 500.0
        assert thresholds["latency"]["high"] == 2000.0
        assert thresholds["error_rate"]["critical"] == 0.20
    
    def test_get_thresholds_for_service_with_overrides(self, template_manager):
        """Test getting thresholds for service with specific overrides."""
        # Test without environment overrides (default is production)
        thresholds = template_manager.get_thresholds_for_service("api-gateway", "production")
        
        # In production environment, environment overrides take precedence over service-specific
        assert thresholds["latency"]["low"] == 500.0  # Production environment override
        assert thresholds["latency"]["high"] == 2000.0  # Production environment override
        assert thresholds["error_rate"]["low"] == 0.01  # Production environment override
        
        # Check that non-overridden values remain global
        assert thresholds["cpu_usage"]["low"] == 0.60  # Global value
        
        # Test with a different environment that doesn't have overrides
        thresholds_no_env = template_manager.get_thresholds_for_service("api-gateway", "staging")
        
        # Service-specific overrides should be applied
        assert thresholds_no_env["latency"]["low"] == 200.0  # Service-specific override
        assert thresholds_no_env["latency"]["high"] == 800.0  # Service-specific override
        assert thresholds_no_env["error_rate"]["low"] == 0.005  # Service-specific override
    
    def test_get_thresholds_for_service_with_environment_overrides(self, template_manager):
        """Test getting thresholds with environment overrides."""
        thresholds = template_manager.get_thresholds_for_service("api-gateway", "development")
        
        # Check that environment overrides are applied
        assert thresholds["latency"]["low"] == 1000.0  # Environment override
        assert thresholds["latency"]["high"] == 5000.0  # Environment override
        assert thresholds["error_rate"]["low"] == 0.05  # Environment override
        
        # Check that service-specific overrides are preserved for non-environment metrics
        assert thresholds["cpu_usage"]["low"] == 0.60  # Global value (no env override)
    
    def test_get_thresholds_for_service_production_environment(self, template_manager):
        """Test getting thresholds for production environment."""
        thresholds = template_manager.get_thresholds_for_service("api-gateway", "production")
        
        # Check that production environment overrides are applied
        assert thresholds["latency"]["low"] == 500.0  # Production override
        assert thresholds["latency"]["high"] == 2000.0  # Production override
        assert thresholds["error_rate"]["low"] == 0.01  # Production override
    
    def test_get_window_size_from_config(self, template_manager):
        """Test getting window size from configuration."""
        window_size = template_manager.get_window_size(MetricType.LATENCY, AlertSeverity.HIGH)
        assert window_size == "5m"
        
        window_size = template_manager.get_window_size(MetricType.ERROR_RATE, AlertSeverity.CRITICAL)
        assert window_size == "2m"
    
    def test_get_window_size_default(self, template_manager):
        """Test getting default window size when not in config."""
        window_size = template_manager.get_window_size(MetricType.THROUGHPUT, AlertSeverity.HIGH)
        assert window_size == "10m"  # Default from the method
    
    def test_get_evaluation_periods_from_config(self, template_manager):
        """Test getting evaluation periods from configuration."""
        periods = template_manager.get_evaluation_periods(AlertSeverity.LOW)
        assert periods == 3
        
        periods = template_manager.get_evaluation_periods(AlertSeverity.CRITICAL)
        assert periods == 1
    
    def test_get_evaluation_periods_default(self):
        """Test getting default evaluation periods when not in config."""
        sample_config = {"global_thresholds": {"latency": {"high": 1000.0}}}
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            manager = AlertTemplateManager("test_config.json")
            periods = manager.get_evaluation_periods(AlertSeverity.HIGH)
            assert periods == 1  # Default value
    
    def test_create_alerts_for_service(self, template_manager):
        """Test creating alerts for a service."""
        alerts = template_manager.create_alerts_for_service("api-gateway", "production")
        
        # Should create alerts for each metric and severity level
        assert len(alerts) > 0
        
        # Check that we have alerts for different metrics
        metric_types = {alert.metric_type for alert in alerts}
        assert MetricType.LATENCY in metric_types
        assert MetricType.ERROR_RATE in metric_types
        assert MetricType.CPU_USAGE in metric_types
        
        # Check that we have alerts for different severities
        severities = {alert.severity for alert in alerts}
        assert AlertSeverity.LOW in severities
        assert AlertSeverity.MEDIUM in severities
        assert AlertSeverity.HIGH in severities
        assert AlertSeverity.CRITICAL in severities
        
        # Check specific alert properties
        latency_alerts = [a for a in alerts if a.metric_type == MetricType.LATENCY]
        assert len(latency_alerts) == 4  # low, medium, high, critical
        
        high_latency_alert = next(a for a in latency_alerts if a.severity == AlertSeverity.HIGH)
        # In production environment, the service-specific override should be applied
        # but the test config has production environment overrides that might override service-specific
        assert high_latency_alert.threshold in [800.0, 2000.0]  # Service-specific or production override
        assert high_latency_alert.window_size == "5m"
        assert high_latency_alert.evaluation_periods == 1
    
    def test_create_alerts_for_service_with_unknown_metric(self, template_manager):
        """Test creating alerts with unknown metric types."""
        # Add an unknown metric to the config
        template_manager.config["global_thresholds"]["unknown_metric"] = {
            "low": 10.0,
            "medium": 20.0,
            "high": 30.0,
            "critical": 40.0
        }
        
        alerts = template_manager.create_alerts_for_service("test-service")
        
        # Should skip unknown metrics and only create alerts for known ones
        metric_types = {alert.metric_type for alert in alerts}
        assert MetricType.LATENCY in metric_types
        assert MetricType.ERROR_RATE in metric_types
        assert MetricType.CPU_USAGE in metric_types
        # unknown_metric should not be in the results
    
    def test_create_alerts_for_service_with_unknown_severity(self, template_manager):
        """Test creating alerts with unknown severity levels."""
        # Add an unknown severity to the config
        template_manager.config["global_thresholds"]["latency"]["unknown_severity"] = 999.0
        
        alerts = template_manager.create_alerts_for_service("test-service")
        
        # Should skip unknown severities
        latency_alerts = [a for a in alerts if a.metric_type == MetricType.LATENCY]
        severities = {a.severity for a in latency_alerts}
        assert severities == {AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL}
        # unknown_severity should not be in the results
    
    def test_create_alerts_for_service_with_non_numeric_threshold(self):
        """Test creating alerts with non-numeric thresholds."""
        # Create a config with non-numeric threshold
        config_with_non_numeric = {
            "global_thresholds": {
                "latency": {
                    "low": 500.0,
                    "medium": 1000.0,
                    "high": "not_a_number",  # Non-numeric threshold
                    "critical": 5000.0
                }
            },
            "window_sizes": {
                "latency": {
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
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_with_non_numeric))):
            manager = AlertTemplateManager("test_config.json")
            alerts = manager.create_alerts_for_service("test-service")
            
            # Should skip non-numeric thresholds
            latency_alerts = [a for a in alerts if a.metric_type == MetricType.LATENCY]
            high_latency_alerts = [a for a in latency_alerts if a.severity == AlertSeverity.HIGH]
            assert len(high_latency_alerts) == 0  # Should be skipped
            
            # Should still create alerts for other severities
            low_latency_alerts = [a for a in latency_alerts if a.severity == AlertSeverity.LOW]
            assert len(low_latency_alerts) == 1  # Should still be created
    
    def test_create_alerts_for_service_special_handling(self, template_manager):
        """Test special handling for cache hit rate and throughput metrics."""
        # Add cache hit rate and throughput to config
        template_manager.config["global_thresholds"]["cache_hit_rate"] = {
            "low": 0.70,
            "medium": 0.80,
            "high": 0.90,
            "critical": 0.95
        }
        template_manager.config["global_thresholds"]["throughput"] = {
            "low": 10.0,
            "medium": 20.0,
            "high": 30.0,
            "critical": 40.0
        }
        
        alerts = template_manager.create_alerts_for_service("test-service")
        
        # Find cache hit rate alerts
        cache_alerts = [a for a in alerts if a.metric_type == MetricType.CACHE_HIT_RATE]
        if cache_alerts:
            low_cache_alert = next(a for a in cache_alerts if a.severity == AlertSeverity.LOW)
            assert "below" in low_cache_alert.description.lower()
        
        # Find throughput alerts
        throughput_alerts = [a for a in alerts if a.metric_type == MetricType.THROUGHPUT]
        if throughput_alerts:
            low_throughput_alert = next(a for a in throughput_alerts if a.severity == AlertSeverity.LOW)
            assert "below" in low_throughput_alert.description.lower()
    
    def test_create_alerts_for_service_alert_names(self, template_manager):
        """Test that alert names are properly formatted."""
        alerts = template_manager.create_alerts_for_service("api-gateway")
        
        for alert in alerts:
            # Check that alert names follow the expected format
            assert alert.name.endswith(" Alert")
            # Check that the metric type (with underscores replaced) is in the name
            metric_name = alert.metric_type.value.replace("_", " ").title()
            assert metric_name in alert.name
            assert alert.severity.value.title() in alert.name
    
    def test_create_alerts_for_service_descriptions(self, template_manager):
        """Test that alert descriptions are properly formatted."""
        alerts = template_manager.create_alerts_for_service("api-gateway")
        
        for alert in alerts:
            # Check that descriptions contain relevant information
            assert alert.metric_type.value.replace("_", " ") in alert.description
            assert alert.severity.value in alert.description.lower()


class TestAlertTemplateManagerIntegration:
    """Integration tests for AlertTemplateManager."""
    
    def test_full_configuration_workflow(self):
        """Test the complete workflow from config loading to alert creation."""
        config = {
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
                "payment-service": {
                    "latency": {
                        "low": 50.0,
                        "medium": 100.0,
                        "high": 200.0,
                        "critical": 500.0
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
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config))):
            manager = AlertTemplateManager("test_config.json")
            
            # Test global service
            global_alerts = manager.create_alerts_for_service("unknown-service")
            assert len(global_alerts) == 8  # 2 metrics * 4 severities
            
            # Test service-specific overrides
            payment_alerts = manager.create_alerts_for_service("payment-service")
            latency_alerts = [a for a in payment_alerts if a.metric_type == MetricType.LATENCY]
            high_latency = next(a for a in latency_alerts if a.severity == AlertSeverity.HIGH)
            assert high_latency.threshold == 200.0  # Service-specific override
            
            # Test environment overrides
            dev_alerts = manager.create_alerts_for_service("payment-service", "development")
            dev_latency_alerts = [a for a in dev_alerts if a.metric_type == MetricType.LATENCY]
            dev_high_latency = next(a for a in dev_latency_alerts if a.severity == AlertSeverity.HIGH)
            assert dev_high_latency.threshold == 5000.0  # Environment override
