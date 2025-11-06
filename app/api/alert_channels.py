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


@router.post("/")
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


@router.get("/")
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


@router.delete("/{channel_id}")
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
