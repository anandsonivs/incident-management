# Elastic APM Alert Integration

This document describes the comprehensive Elastic APM alert integration system that automatically creates monitoring alerts for all services and integrates them seamlessly with the incident management platform.

## 🎯 Overview

The Elastic APM Alert Integration system provides:

- **Automatic Alert Creation**: Creates comprehensive monitoring alerts for all services in Elastic APM
- **Multi-Metric Monitoring**: Covers latency, error rate, throughput, CPU, memory, disk usage, and more
- **Severity-Based Categorization**: Alerts are categorized using the same severity levels as the incident management system
- **Team-Based Assignment**: Automatic team assignment based on service type
- **Seamless Integration**: Direct integration with the incident management system via webhooks
- **Customizable Thresholds**: Environment and service-specific alert thresholds
- **Comprehensive Tagging**: Rich metadata and tagging for better incident management

## 📊 Supported Metrics

The system monitors the following metrics across all services:

### Core Application Metrics
- **Latency**: Response time monitoring (p95, p99)
- **Error Rate**: Transaction failure rates
- **Throughput**: Request volume monitoring

### Infrastructure Metrics
- **CPU Usage**: System CPU utilization
- **Memory Usage**: System memory consumption
- **Disk Usage**: Disk space utilization

### JVM Metrics (Java Services)
- **JVM Heap Usage**: Java heap memory usage
- **JVM GC Rate**: Garbage collection frequency

### Database & Cache Metrics
- **Database Connections**: Connection pool usage
- **Cache Hit Rate**: Cache performance monitoring

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Run the setup script
./scripts/setup_elastic_alerts.sh setup
```

This will create a `.elastic_alerts.env` file that you need to configure.

### 2. Configure Environment

Edit `.elastic_alerts.env` with your configuration:

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

### 3. Preview Alert Creation

```bash
# Run dry-run to see what alerts will be created
./scripts/setup_elastic_alerts.sh dry-run
```

### 4. Create Alerts

```bash
# Create alerts for all services
./scripts/setup_elastic_alerts.sh create
```

## 📋 Alert Configuration

The system uses a **two-tier configuration approach** for maximum flexibility:

1. **Global Configuration**: Default thresholds for all services
2. **Service-Specific Configuration**: Overrides for individual services
3. **Environment Overrides**: Environment-specific adjustments

### Configuration Hierarchy

The system applies thresholds in this order (later overrides earlier):
1. **Global Thresholds** (base configuration)
2. **Service-Specific Thresholds** (service overrides)
3. **Environment Overrides** (environment-specific adjustments)

### Global Alert Thresholds

The system includes comprehensive default thresholds for all severity levels:

| Metric | Low | Medium | High | Critical | Unit |
|--------|-----|--------|------|----------|------|
| Latency | 500ms | 1000ms | 2000ms | 5000ms | milliseconds |
| Error Rate | 1% | 3% | 5% | 20% | percentage |
| Throughput | 5/min | 10/min | 20/min | 50/min | requests/minute |
| CPU Usage | 60% | 75% | 85% | 95% | percentage |
| Memory Usage | 70% | 80% | 90% | 95% | percentage |
| Disk Usage | 75% | 85% | 90% | 95% | percentage |

### Service-Specific Thresholds

Different services have customized thresholds based on their characteristics:

#### API Gateway
- **Latency**: 200ms (Low) → 1500ms (Critical)
- **Error Rate**: 0.5% (Low) → 5% (Critical)
- **Throughput**: 100/min (Low) → 2000/min (Critical)

#### Payment Service
- **Latency**: 50ms (Low) → 500ms (Critical)
- **Error Rate**: 0.01% (Low) → 1% (Critical)
- **Throughput**: 10/min (Low) → 200/min (Critical)

#### Database Service
- **Latency**: 10ms (Low) → 100ms (Critical)
- **Error Rate**: 0.01% (Low) → 1% (Critical)
- **Connections**: 50% (Low) → 90% (Critical)

#### Cache Service
- **Latency**: 5ms (Low) → 50ms (Critical)
- **Error Rate**: 0.01% (Low) → 1% (Critical)
- **Hit Rate**: 85% (Low) → 98% (Critical)

### Environment-Specific Thresholds

Thresholds are automatically adjusted based on environment:

#### Development
- **Latency**: 1000ms (Low) → 10000ms (Critical)
- **Error Rate**: 5% (Low) → 40% (Critical)
- **CPU/Memory**: 80% (Low) → 98% (Critical)

#### Staging
- **Latency**: 750ms (Low) → 7500ms (Critical)
- **Error Rate**: 3% (Low) → 30% (Critical)
- **CPU/Memory**: 75% (Low) → 95% (Critical)

#### Production
- **Latency**: 500ms (Low) → 5000ms (Critical)
- **Error Rate**: 1% (Low) → 20% (Critical)
- **CPU/Memory**: 60% (Low) → 95% (Critical)

## 👥 Team Assignment

The system automatically assigns alerts to appropriate teams based on service type:

### Team Categories

- **Platform Team**: Infrastructure and platform services
- **User Management Team**: Authentication and user services
- **Payment Team**: Financial and payment processing
- **Order Management Team**: Order processing and fulfillment
- **Inventory Team**: Stock and inventory management
- **Data Team**: Analytics and reporting
- **Search Team**: Search and recommendation services
- **Catalog Team**: Product catalog and content
- **Media Team**: Media processing and storage
- **Security Team**: Security and compliance services
- **Billing Team**: Billing and subscription management
- **Logistics Team**: Shipping and logistics
- **Customer Support Team**: Support and helpdesk services
- **Marketing Team**: Marketing and campaign services
- **Database Team**: Database administration
- **Cache Team**: Cache and session management
- **Message Queue Team**: Event processing and queues
- **DevOps Team**: Monitoring and infrastructure
- **Network Team**: Network infrastructure
- **Integration Team**: Third-party integrations
- **Mobile Team**: Mobile application services
- **Web Team**: Web application services
- **Admin Team**: Administrative services

### Customizing Team Mapping

Edit `config/team_mapping.json` to customize team assignments:

```json
{
  "your-service-name": {
    "team_name": "Your Team Name",
    "description": "Team description"
  }
}
```

## 🔧 Alert Types and Configurations

### 1. Latency Alerts

**High Latency Alert**
- Threshold: 1000ms (configurable per service)
- Window: 5 minutes
- Severity: High

**Critical Latency Alert**
- Threshold: 5000ms (configurable per service)
- Window: 2 minutes
- Severity: Critical

### 2. Error Rate Alerts

**High Error Rate Alert**
- Threshold: 5% (configurable per service)
- Window: 5 minutes
- Severity: High

**Critical Error Rate Alert**
- Threshold: 20% (configurable per service)
- Window: 2 minutes
- Severity: Critical

### 3. Throughput Alerts

**Low Throughput Alert**
- Threshold: 10 requests/minute
- Window: 10 minutes
- Severity: Medium

### 4. Infrastructure Alerts

**CPU Usage Alerts**
- High: 80% (5-minute window)
- Critical: 95% (2-minute window)

**Memory Usage Alerts**
- High: 85% (5-minute window)
- Critical: 95% (2-minute window)

**Disk Usage Alerts**
- High: 85% (10-minute window)
- Critical: 95% (5-minute window)

### 5. JVM Alerts (Java Services)

**JVM Heap Usage Alert**
- Threshold: 85%
- Window: 5 minutes
- Severity: High

**JVM GC Rate Alert**
- Threshold: 10 events/minute
- Window: 5 minutes
- Severity: Medium

### 6. Database & Cache Alerts

**Database Connections Alert**
- Threshold: 80% of max connections
- Window: 5 minutes
- Severity: Medium

**Cache Hit Rate Alert**
- Threshold: 70% minimum
- Window: 10 minutes
- Severity: Medium

## 🔗 Integration with Incident Management

### Webhook Integration

When an alert is triggered, Elastic APM sends a webhook to the incident management system:

```json
{
  "alert_name": "High Latency Alert - api-gateway",
  "message": "Service response time is above acceptable threshold for service api-gateway",
  "severity": "high",
  "service": {
    "name": "api-gateway",
    "environment": "production"
  },
  "alert_id": "alert-123",
  "state": {
    "state": "active",
    "timestamp": "2024-01-20T10:30:00Z"
  },
  "metadata": {
    "metric_type": "latency",
    "threshold": 1000.0,
    "window_size": "5m",
    "team_id": 1,
    "rule_id": "rule-456"
  },
  "tags": {
    "service": "api-gateway",
    "environment": "production",
    "team_id": "1",
    "metric_type": "latency",
    "severity": "high"
  }
}
```

### Automatic Incident Creation

The webhook automatically creates incidents with:

- **Proper Severity**: Matches alert severity
- **Team Assignment**: Based on service type
- **Rich Metadata**: Includes all alert details
- **Service Context**: Service name and environment
- **Alert Correlation**: Links to original Elastic alert

### Incident Lifecycle

1. **Alert Triggered**: Elastic APM detects threshold breach
2. **Webhook Sent**: Alert data sent to incident management
3. **Incident Created**: Automatic incident creation with full context
4. **Team Notification**: Appropriate team notified based on assignment
5. **Escalation**: Follows escalation policies if incident not acknowledged
6. **Resolution**: Incident resolved when alert recovers

## 🛠️ Advanced Configuration

### Adding New Services

To add a new service with custom thresholds, edit `config/alert_thresholds.json`:

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
      },
      "throughput": {
        "low": 10.0,
        "medium": 25.0,
        "high": 50.0,
        "critical": 100.0
      },
      "cpu_usage": {
        "low": 0.65,
        "medium": 0.80,
        "high": 0.90,
        "critical": 0.95
      },
      "memory_usage": {
        "low": 0.75,
        "medium": 0.85,
        "high": 0.92,
        "critical": 0.97
      }
    }
  }
}
```

### Custom Alert Thresholds

You can override any metric for any service. The system supports all severity levels:

- **Low**: Early warning indicators
- **Medium**: Moderate issues requiring attention
- **High**: Serious issues requiring immediate action
- **Critical**: Critical issues requiring urgent response

Example for a high-performance service:

```json
{
  "service_specific_thresholds": {
    "high-performance-api": {
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
  }
}
```

### Service Pattern Filtering

Filter services using regex patterns:

```bash
# Create alerts only for API services
./scripts/setup_elastic_alerts.sh create --service-pattern 'api.*'

# Create alerts only for database services
./scripts/setup_elastic_alerts.sh create --service-pattern '.*database.*'
```

### Environment-Specific Configuration

Different environments can have different configurations:

```bash
# Development environment
ENVIRONMENT="development" ./scripts/setup_elastic_alerts.sh create

# Staging environment
ENVIRONMENT="staging" ./scripts/setup_elastic_alerts.sh create

# Production environment
ENVIRONMENT="production" ./scripts/setup_elastic_alerts.sh create
```

## 📈 Monitoring and Maintenance

### Alert Management

#### Viewing Alerts
- **Elastic APM**: View all created alerts in Elastic APM UI
- **Incident Management**: View incidents created from alerts
- **Logs**: Check `elastic_alerts.log` for script execution logs

#### Updating Alerts
```bash
# Update team mapping
vim config/team_mapping.json

# Update thresholds
vim config/alert_thresholds.json

# Recreate alerts
./scripts/setup_elastic_alerts.sh create
```

#### Removing Alerts
```bash
# Use Elastic APM API to remove specific alerts
curl -X DELETE "https://your-elastic-instance.com/api/alerting/rule/alert-id" \
  -H "Authorization: ApiKey your-api-key"
```

### Performance Considerations

- **Rate Limiting**: Script includes 1-second delays between API calls
- **Batch Processing**: Alerts are created sequentially to avoid overwhelming APIs
- **Error Handling**: Failed alert creation is logged and doesn't stop the process
- **Dry Run Mode**: Always test with dry-run before creating alerts

### Troubleshooting

#### Common Issues

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

#### Log Analysis

```bash
# View script execution logs
tail -f elastic_alerts.log

# Filter for errors
grep ERROR elastic_alerts.log

# Filter for specific service
grep "api-gateway" elastic_alerts.log
```

## 🔒 Security Considerations

### API Key Management
- Store API keys securely (use environment variables)
- Rotate API keys regularly
- Use least-privilege permissions

### Network Security
- Use HTTPS for all API communications
- Restrict network access to Elastic APM and incident management APIs
- Use VPN if required for secure access

### Data Privacy
- Alert data may contain sensitive service information
- Ensure compliance with data protection regulations
- Log and audit alert creation activities

## 📚 Best Practices

### Alert Design
1. **Start Conservative**: Begin with higher thresholds and adjust down
2. **Test Thoroughly**: Use dry-run mode before production deployment
3. **Monitor Alert Volume**: Too many alerts can lead to alert fatigue
4. **Regular Review**: Periodically review and adjust thresholds

### Team Organization
1. **Clear Ownership**: Ensure each service has a clear team owner
2. **Escalation Paths**: Define clear escalation procedures
3. **Documentation**: Document team responsibilities and contact information
4. **Training**: Train teams on incident response procedures

### Maintenance
1. **Regular Updates**: Keep alert configurations up to date
2. **Performance Monitoring**: Monitor the impact of alerts on system performance
3. **Feedback Loop**: Collect feedback from teams on alert effectiveness
4. **Continuous Improvement**: Regularly improve alert configurations based on learnings

## 🚀 Future Enhancements

### Planned Features
- **Dynamic Thresholds**: Machine learning-based threshold adjustment
- **Alert Correlation**: Group related alerts into single incidents
- **Custom Metrics**: Support for custom business metrics
- **Multi-Environment**: Enhanced multi-environment support
- **Alert Templates**: Reusable alert configuration templates
- **Dashboard Integration**: Integration with monitoring dashboards

### Integration Possibilities
- **Slack Integration**: Direct Slack notifications
- **PagerDuty Integration**: PagerDuty incident creation
- **Jira Integration**: Automatic Jira ticket creation
- **Email Integration**: Email notifications for critical alerts
- **SMS Integration**: SMS notifications for urgent alerts

---

**Last Updated**: January 20, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
