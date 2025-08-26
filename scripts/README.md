# Elastic APM Alert Management Scripts

This directory contains scripts for automatically creating and managing Elastic APM alerts that integrate with the incident management system.

## 📁 Files

### Core Scripts

- **`create_elastic_alerts.py`** - Main script for creating Elastic APM alerts
- **`setup_elastic_alerts.sh`** - Shell script wrapper for easy setup and execution

### Configuration Files

- **`config/alert_thresholds.json`** - Two-tier alert threshold configuration
- **`config/team_mapping.json`** - Service to team mapping configuration
- **`config/example_service_config.json`** - Example configurations for new services

## 🚀 Quick Start

### 1. Setup

```bash
# Run the setup script
./scripts/setup_elastic_alerts.sh setup
```

This creates a `.elastic_alerts.env` file that you need to configure.

### 2. Configure Environment

Edit `.elastic_alerts.env`:

```bash
# Elastic APM Configuration
ELASTIC_URL="https://your-elastic-instance.com"
ELASTIC_API_KEY="your-elastic-api-key"

# Incident Management Configuration
INCIDENT_API_URL="http://localhost:8000"
INCIDENT_API_TOKEN="your-incident-api-token"

# Alert Configuration
ENVIRONMENT="production"
TEAM_MAPPING_FILE="config/team_mapping.json"
ALERT_THRESHOLDS_FILE="config/alert_thresholds.json"
```

### 3. Preview Alerts

```bash
# Run dry-run to see what alerts will be created
./scripts/setup_elastic_alerts.sh dry-run
```

### 4. Create Alerts

```bash
# Create alerts for all services
./scripts/setup_elastic_alerts.sh create
```

## 🔧 Direct Script Usage

You can also run the Python script directly:

```bash
python3 scripts/create_elastic_alerts.py \
  --elastic-url "https://your-elastic-instance.com" \
  --elastic-api-key "your-api-key" \
  --incident-api-url "http://localhost:8000" \
  --incident-api-token "your-token" \
  --team-mapping "config/team_mapping.json" \
  --environment "production" \
  --dry-run
```

## 📊 Configuration System

### Two-Tier Configuration

The system uses a hierarchical configuration approach:

1. **Global Thresholds** - Base configuration for all services
2. **Service-Specific Thresholds** - Overrides for individual services
3. **Environment Overrides** - Environment-specific adjustments

### Adding New Services

To add a new service, edit `config/alert_thresholds.json`:

```json
{
  "service_specific_thresholds": {
    "your-new-service": {
      "latency": {
        "low": 100.0,
        "medium": 200.0,
        "high": 400.0,
        "critical": 800.0
      },
      "error_rate": {
        "low": 0.001,
        "medium": 0.003,
        "high": 0.008,
        "critical": 0.015
      }
    }
  }
}
```

### Supported Metrics

- **latency** - Response time monitoring
- **error_rate** - Transaction failure rates
- **throughput** - Request volume monitoring
- **cpu_usage** - System CPU utilization
- **memory_usage** - System memory consumption
- **disk_usage** - Disk space utilization
- **jvm_heap** - JVM heap memory usage
- **jvm_gc** - JVM garbage collection rate
- **database_connections** - Database connection pool usage
- **cache_hit_rate** - Cache performance monitoring

### Severity Levels

- **low** - Early warning indicators
- **medium** - Moderate issues requiring attention
- **high** - Serious issues requiring immediate action
- **critical** - Critical issues requiring urgent response

## 🎯 Features

### Automatic Alert Creation
- Creates comprehensive monitoring alerts for all services
- Supports multiple severity levels for each metric
- Automatic team assignment based on service type

### Flexible Configuration
- Two-tier configuration system (global + service-specific)
- Environment-specific overrides
- Easy addition of new services

### Integration
- Seamless integration with incident management system
- Automatic incident creation when alerts are triggered
- Rich metadata and tagging for better incident management

### Monitoring Coverage
- Application metrics (latency, error rate, throughput)
- Infrastructure metrics (CPU, memory, disk)
- JVM metrics (heap usage, garbage collection)
- Database and cache metrics

## 🔍 Troubleshooting

### Common Issues

1. **API Connection Errors**
   ```bash
   # Check Elastic APM connectivity
   curl -H "Authorization: ApiKey your-key" "https://your-elastic-instance.com/api/apm/services"
   
   # Check incident management connectivity
   curl -H "Authorization: Bearer your-token" "http://localhost:8000/health"
   ```

2. **Permission Errors**
   - Ensure Elastic API key has alert management permissions
   - Ensure incident management token has team creation permissions

3. **Service Discovery Issues**
   - Check if services are properly instrumented in Elastic APM
   - Verify service names match team mapping configuration

### Log Analysis

```bash
# View script execution logs
tail -f elastic_alerts.log

# Filter for errors
grep ERROR elastic_alerts.log

# Filter for specific service
grep "api-gateway" elastic_alerts.log
```

## 📚 Documentation

For detailed documentation, see:
- [Elastic APM Integration Guide](../docs/ELASTIC_APM_INTEGRATION.md)
- [Configuration Examples](../config/example_service_config.json)

## 🔒 Security

- Store API keys securely (use environment variables)
- Use HTTPS for all API communications
- Rotate API keys regularly
- Use least-privilege permissions

## 🚀 Future Enhancements

- Dynamic threshold adjustment using machine learning
- Alert correlation and grouping
- Custom business metrics support
- Enhanced multi-environment support
- Integration with additional monitoring tools
