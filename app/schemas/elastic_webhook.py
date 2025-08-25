from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ElasticService(BaseModel):
    """Elastic service information."""
    name: str = Field(..., description="Service name")
    environment: Optional[str] = Field(None, description="Service environment")
    version: Optional[str] = Field(None, description="Service version")


class ElasticAlertState(BaseModel):
    """Elastic alert state information."""
    state: str = Field(..., description="Alert state: active, resolved, recovered")
    timestamp: Optional[str] = Field(None, description="State change timestamp")


class ElasticWebhookPayload(BaseModel):
    """Schema for Elastic APM webhook payload."""
    alert_name: Optional[str] = Field(None, description="Name of the alert")
    message: Optional[str] = Field(None, description="Alert message/description")
    severity: Optional[str] = Field(None, description="Alert severity: critical, high, medium, low")
    service: Optional[ElasticService] = Field(None, description="Service information")
    alert_id: Optional[str] = Field(None, description="Unique alert identifier")
    state: Optional[ElasticAlertState] = Field(None, description="Alert state information")
    
    # Additional fields that might be present
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[Dict[str, str]] = Field(None, description="Alert tags")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_name": "High CPU Usage Alert",
                "message": "CPU usage is above 90% for the last 5 minutes",
                "severity": "high",
                "service": {
                    "name": "api-service",
                    "environment": "production",
                    "version": "1.0.0"
                },
                "alert_id": "cpu-alert-123",
                "state": {
                    "state": "active",
                    "timestamp": "2024-01-20T10:30:00Z"
                },
                "metadata": {
                    "cpu_percentage": 95.2,
                    "threshold": 90.0
                },
                "tags": {
                    "environment": "production",
                    "team": "platform"
                }
            }
        }
    )


class ElasticWebhookResponse(BaseModel):
    """Schema for Elastic webhook response."""
    status: str = Field(..., description="Response status")
    incident_id: Optional[int] = Field(None, description="Created or updated incident ID")
    message: Optional[str] = Field(None, description="Additional response message")
