"""API endpoints for managing alert channels (Email, Slack)."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import models, crud
from ..security import get_db, get_organization_from_api_key

router = APIRouter()


class AlertChannelCreate(BaseModel):
    """Schema for creating an alert channel."""
    channel_type: str  # "email" or "slack"
    configuration: Dict[str, Any]  # {"email": "..."} or {"webhook_url": "..."}


@router.post(
    "/",
    summary="Create an alert channel",
    description="""
    Configure email or Slack notifications for drift alerts.
    
    When drift is detected, DriftGuard will automatically send notifications 
    through all active channels configured for your organization.
    
    **Email Example:**
    ```bash
    curl -X POST http://localhost:8000/alert-channels/ \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_type": "email",
        "configuration": {"email": "alerts@company.com"}
      }'
    ```
    
    **Slack Example:**
    ```bash
    curl -X POST http://localhost:8000/alert-channels/ \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_type": "slack",
        "configuration": {
          "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
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
                            "value": {"detail": "channel_type must be 'email' or 'slack'"}
                        },
                        "missing_config": {
                            "summary": "Missing configuration",
                            "value": {"detail": "configuration must contain 'email' field for email channels"}
                        }
                    }
                }
            }
        }
    }
)
def create_alert_channel(
    channel_data: AlertChannelCreate,
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Create a new alert channel for the organization.
    
    Examples:
    - Email: {"channel_type": "email", "configuration": {"email": "alerts@company.com"}}
    - Slack: {"channel_type": "slack", "configuration": {"webhook_url": "https://hooks.slack.com/..."}}
    """
    # Validate channel type
    if channel_data.channel_type not in ["email", "slack"]:
        raise HTTPException(
            status_code=400,
            detail="channel_type must be 'email' or 'slack'"
        )
    
    # Validate configuration based on channel type
    if channel_data.channel_type == "email":
        if "email" not in channel_data.configuration:
            raise HTTPException(
                status_code=400,
                detail="configuration must contain 'email' field for email channels"
            )
    elif channel_data.channel_type == "slack":
        if "webhook_url" not in channel_data.configuration:
            raise HTTPException(
                status_code=400,
                detail="configuration must contain 'webhook_url' field for Slack channels"
            )
    
    # Create the alert channel
    alert_channel = models.AlertChannel(
        organization_id=organization.id,  # type: ignore
        channel_type=channel_data.channel_type,
        configuration=channel_data.configuration,
        is_active=True
    )
    
    db.add(alert_channel)
    db.commit()
    db.refresh(alert_channel)
    
    return {
        "id": alert_channel.id,
        "channel_type": alert_channel.channel_type,
        "is_active": alert_channel.is_active,
        "created_at": alert_channel.created_at
    }


@router.get(
    "/",
    summary="List alert channels",
    description="""
    Get all alert channels configured for your organization.
    
    Shows which notification channels are active and when they were created.
    Sensitive data (like webhook URLs) is not exposed in the list view.
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
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    """List all alert channels for the organization."""
    channels = (
        db.query(models.AlertChannel)
        .filter(models.AlertChannel.organization_id == organization.id)  # type: ignore
        .all()
    )
    
    return [
        {
            "id": c.id,
            "channel_type": c.channel_type,
            "is_active": c.is_active,
            "created_at": c.created_at,
            # Don't expose sensitive data like webhook URLs in list view
            "configured": True
        }
        for c in channels
    ]


@router.delete(
    "/{channel_id}",
    summary="Delete an alert channel",
    description="""
    Remove an alert channel. You will stop receiving notifications through this channel.
    
    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/alert-channels/1 \\
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
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    """Delete an alert channel."""
    channel = (
        db.query(models.AlertChannel)
        .filter(
            models.AlertChannel.id == channel_id,
            models.AlertChannel.organization_id == organization.id  # type: ignore
        )
        .first()
    )
    
    if not channel:
        raise HTTPException(status_code=404, detail="Alert channel not found")
    
    db.delete(channel)
    db.commit()
    
    return {"success": True, "message": "Alert channel deleted"}
