"""
Alert management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel, Field

from .. import models, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.alert_service import NotificationService
from ..limiter import limiter


router = APIRouter(prefix="/alerts", tags=["alerts"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AlertChannelCreate(BaseModel):
    """Schema for creating an alert channel."""
    channel_type: str = Field(..., description="Channel type: 'slack', 'email', or 'webhook'")
    configuration: dict = Field(..., description="Channel configuration (webhook_url, email, etc.)")


class AlertChannelResponse(BaseModel):
    """Schema for alert channel response."""
    id: int
    channel_type: str
    configuration: dict
    is_active: bool
    
    class Config:
        from_attributes = True


class AlertConfigCreate(BaseModel):
    """Schema for creating an alert configuration."""
    alert_type: str = Field(..., description="Alert type: 'daily_cost', 'weekly_cost', 'monthly_cost'")
    threshold_usd: float = Field(..., description="Cost threshold in USD", gt=0)


class AlertConfigResponse(BaseModel):
    """Schema for alert config response."""
    id: int
    alert_type: str
    threshold_usd: float
    enabled: bool
    last_triggered: Optional[str]
    
    class Config:
        from_attributes = True


# ============================================================================
# Alert Channel Endpoints
# ============================================================================

@router.post(
    "/channels",
    response_model=AlertChannelResponse,
    summary="Create an alert channel",
    description="""
    Configure email, Slack, or webhook notifications for alerts.
    
    When alerts are triggered, Cognitude will automatically send notifications
    through all active channels configured for your organization.
    
    **Email Example:**
    ```bash
    curl -X POST https://api.cognitude.io/alerts/channels/ \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_type": "email",
        "configuration": {"email": "alerts@company.com"}
      }'
    ```
    
    **Slack Example:**
    ```bash
    curl -X POST https://api.cognitude.io/alerts/channels/ \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_type": "slack",
        "configuration": {
          "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        }
      }'
    ```
    
    **Webhook Example:**
    ```bash
    curl -X POST https://api.cognitude.io/alerts/channels/ \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_type": "webhook",
        "configuration": {
          "webhook_url": "https://your-server.com/webhook"
        }
      }'
    ```
    
    **How to get a Slack webhook:**
    1. Go to https://api.slack.com/apps
    2. Create a new app or select existing
    3. Enable "Incoming Webhooks"
    4. Add webhook to your workspace
    5. Copy the webhook URL
    """,
    responses={
        200: {
            "description": "Alert channel created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "channel_type": "email",
                        "is_active": True,
                        "created_at": "2025-11-06T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_type": {
                            "summary": "Invalid channel type",
                            "value": {"detail": "channel_type must be 'email', 'slack', or 'webhook'"}
                        },
                        "missing_config": {
                            "summary": "Missing configuration",
                            "value": {"detail": "configuration must contain required fields for the channel type"}
                        }
                    }
                }
            }
        }
    }
)
def create_alert_channel(
    channel: AlertChannelCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Create a new alert channel for the organization.
    
    Examples:
    - Email: {"channel_type": "email", "configuration": {"email": "alerts@company.com"}}
    - Slack: {"channel_type": "slack", "configuration": {"webhook_url": "https://hooks.slack.com/..."}}
    - Webhook: {"channel_type": "webhook", "configuration": {"webhook_url": "https://your-server.com/webhook"}}
    """
    # Validate channel type
    if channel.channel_type not in ["email", "slack", "webhook"]:
        raise HTTPException(
            status_code=400,
            detail="channel_type must be 'email', 'slack', or 'webhook'"
        )
    
    # Validate configuration based on channel type
    if channel.channel_type == "email":
        if "email" not in channel.configuration:
            raise HTTPException(
                status_code=400,
                detail="configuration must contain 'email' field for email channels"
            )
    elif channel.channel_type == "slack":
        if "webhook_url" not in channel.configuration:
            raise HTTPException(
                status_code=400,
                detail="configuration must contain 'webhook_url' field for Slack channels"
            )
    elif channel.channel_type == "webhook":
        if "webhook_url" not in channel.configuration:
            raise HTTPException(
                status_code=400,
                detail="configuration must contain 'webhook_url' field for webhook channels"
            )
    
    # Create the alert channel
    db_channel = models.AlertChannel(
        organization_id=organization.id,
        channel_type=channel.channel_type,
        configuration=channel.configuration,
        is_active=True
    )
    
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    
    return db_channel


@router.get(
    "/channels",
    response_model=List[AlertChannelResponse],
    summary="List alert channels",
    description="""
    Get all alert channels configured for your organization.
    
    Shows which notification channels are active and when they were created.
    Sensitive data (like webhook URLs) is not exposed in the list view.
    
    Supports pagination for organizations with many channels.
    """,
    responses={
        200: {
            "description": "List of alert channels",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "channel_type": "email",
                            "is_active": True,
                            "created_at": "2025-11-06T10:30:00Z",
                            "configured": True
                        },
                        {
                            "id": 2,
                            "channel_type": "slack",
                            "is_active": True,
                            "created_at": "2025-11-06T10:35:00Z",
                            "configured": True
                        }
                    ]
                }
            }
        }
    }
)
def list_alert_channels(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """List all alert channels for the organization with pagination."""
    # Use selectinload to avoid N+1 query problems
    channels = db.query(models.AlertChannel).filter(
        models.AlertChannel.organization_id == organization.id
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": c.id,
            "channel_type": c.channel_type,
            "configuration": {},  # Don't expose sensitive data in list view
            "is_active": c.is_active
        }
        for c in channels
    ]


@router.delete(
    "/channels/{channel_id}",
    summary="Delete an alert channel",
    description="""
    Remove an alert channel. You will stop receiving notifications through this channel.
    
    **Example:**
    ```bash
    curl -X DELETE https://api.cognitude.io/alerts/channels/1 \\
      -H "X-API-Key: your-api-key"
    ```
    """,
    responses={
        200: {
            "description": "Channel deleted successfully",
            "content": {
                "application/json": {
                    "example": {"success": True, "message": "Alert channel deleted"}
                }
            }
        },
        404: {
            "description": "Alert channel not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Alert channel not found"}
                }
            }
        }
    }
)
def delete_alert_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """Delete an alert channel."""
    # Verify ownership first to prevent IDOR
    channel = db.query(models.AlertChannel).filter(
        models.AlertChannel.id == channel_id,
        models.AlertChannel.organization_id == organization.id
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Alert channel not found")
    
    db.delete(channel)
    db.commit()
    
    return {"success": True, "message": "Alert channel deleted"}


# ============================================================================
# Alert Configuration Endpoints
# ============================================================================

@router.post("/configs", response_model=AlertConfigResponse)
def create_alert_config(
    config: AlertConfigCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Create a cost threshold alert configuration.
    
    **Alert Types**:
    - `daily_cost`: Alert when daily costs exceed threshold
    - `weekly_cost`: Alert when weekly costs exceed threshold  
    - `monthly_cost`: Alert when monthly costs exceed threshold
    
    **Example**:
    ```json
    {
      "alert_type": "daily_cost",
      "threshold_usd": 50.00
    }
    ```
    
    This will send an alert when daily costs exceed $50.
    
    **Note**: You must have at least one alert channel configured to receive notifications.
    """
    # Validate alert type
    if config.alert_type not in ["daily_cost", "weekly_cost", "monthly_cost"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid alert_type. Must be 'daily_cost', 'weekly_cost', or 'monthly_cost'"
        )
    
    # Check if alert config already exists for this type
    existing = db.query(models.AlertConfig).filter(
        models.AlertConfig.organization_id == organization.id,
        models.AlertConfig.alert_type == config.alert_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Alert config for '{config.alert_type}' already exists. Delete it first or update the threshold."
        )
    
    # Create config
    db_config = models.AlertConfig(
        organization_id=organization.id,
        alert_type=config.alert_type,
        threshold_usd=config.threshold_usd,
        enabled=True
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.get("/configs", response_model=List[AlertConfigResponse])
def list_alert_configs(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """
    List all alert configurations for the organization with pagination.
    """
    configs = db.query(models.AlertConfig).filter(
        models.AlertConfig.organization_id == organization.id
    ).offset(skip).limit(limit).all()
    
    return configs


@router.delete("/configs/{config_id}")
def delete_alert_config(
    config_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Delete an alert configuration.
    """
    # Verify ownership first to prevent IDOR
    config = db.query(models.AlertConfig).filter(
        models.AlertConfig.id == config_id,
        models.AlertConfig.organization_id == organization.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    
    db.delete(config)
    db.commit()
    
    return {"message": "Alert config deleted"}


# ============================================================================
# Testing & Manual Triggering
# ============================================================================

@router.post("/test/{channel_id}")
def test_alert_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Send a test notification to an alert channel.
    
    Useful for verifying that your channel configuration is working correctly.
    """
    channel = db.query(models.AlertChannel).filter(
        models.AlertChannel.id == channel_id,
        models.AlertChannel.organization_id == organization.id
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Alert channel not found")
    
    notification_service = NotificationService(db)
    # Get the configuration as a Python dict from the JSONB column
    config = channel.configuration
    
    success = False
    
    if channel.channel_type == "slack" and config and config.get("webhook_url"):
        webhook_url = str(config["webhook_url"])
        success = notification_service.send_slack_notification(
            webhook_url=webhook_url,
            title="🧪 Test Notification",
            message="This is a test notification from Cognitude. Your Slack integration is working correctly!",
            color="#36a64f",
            fields=[
                {"title": "Organization", "value": organization.name, "short": True},
                {"title": "Channel Type", "value": "Slack", "short": True}
            ]
        )
    
    elif channel.channel_type == "email" and config and config.get("email"):
        email = str(config["email"])
        success = notification_service.send_email_notification(
            to_email=email,
            subject="🧪 Test Notification from Cognitude",
            body_html="""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2e7d32;">🧪 Test Notification</h2>
                <p>This is a test notification from Cognitude.</p>
                <p>Your email integration is working correctly!</p>
            </body>
            </html>
            """
        )
    
    elif channel.channel_type == "webhook" and config and config.get("webhook_url"):
        webhook_url = str(config["webhook_url"])
        success = notification_service.send_webhook_notification(
            webhook_url=webhook_url,
            payload={
                "event": "test_notification",
                "organization_name": organization.name,
                "message": "This is a test notification from Cognitude"
            }
        )
    
    if success:
        return {"message": "Test notification sent successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send test notification. Check your configuration."
        )


@router.post("/check")
@limiter.limit("10/minute")  # Rate limit this expensive operation
def check_cost_alerts(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Manually check and trigger cost alerts if thresholds are exceeded.
    
    This is useful for testing your alert configurations. In production,
    this is automatically called by a background scheduler.
    
    Rate limited to 10 requests per minute to prevent abuse.
    """
    notification_service = NotificationService(db)
    results = notification_service.check_and_send_cost_alerts(organization.id)
    
    return {
        "message": "Cost alerts checked",
        "alerts_checked": results["alerts_checked"],
        "alerts_triggered": results["alerts_triggered"],
        "notifications_sent": results["notifications_sent"]
    }
