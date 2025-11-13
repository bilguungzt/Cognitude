"""
Alert management API endpoints.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
import re

from .. import models, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.alert_service import NotificationService


router = APIRouter(prefix="/alerts", tags=["alerts"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AlertChannelCreate(BaseModel):
    """Schema for creating an alert channel."""
    channel_type: str = Field(..., description="Channel type: 'slack', 'email', or 'webhook'")
    configuration: dict = Field(..., description="Channel configuration (webhook_url, email, etc.)")
    
    @field_validator('channel_type')
    @classmethod
    def validate_channel_type(cls, v):
        if v not in ["slack", "email", "webhook"]:
            raise ValueError("Must be 'slack', 'email', or 'webhook'")
        return v
    
    @field_validator('configuration')
    @classmethod
    def validate_configuration(cls, v, info):
        channel_type = info.data.get('channel_type')
        
        if channel_type == "slack":
            if "webhook_url" not in v:
                raise ValueError("Slack channel requires 'webhook_url'")
            if not v["webhook_url"].startswith("https://hooks.slack.com"):
                raise ValueError("Invalid Slack webhook URL")
        
        elif channel_type == "email":
            if "email" not in v:
                raise ValueError("Email channel requires 'email'")
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v["email"]):
                raise ValueError("Invalid email address")
        
        elif channel_type == "webhook":
            if "webhook_url" not in v:
                raise ValueError("Webhook channel requires 'webhook_url'")
            if not v["webhook_url"].startswith(("http://", "https://")):
                raise ValueError("Invalid webhook URL")
        
        return v


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
    
    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        if v not in ["daily_cost", "weekly_cost", "monthly_cost"]:
            raise ValueError("Must be 'daily_cost', 'weekly_cost', or 'monthly_cost'")
        return v


class AlertConfigResponse(BaseModel):
    """Schema for alert config response."""
    id: int
    alert_type: str
    threshold_usd: float
    enabled: bool
    last_triggered: Optional[str] = None
    
    @field_validator('last_triggered', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)
    
    class Config:
        from_attributes = True


# ============================================================================
# Alert Channel Endpoints
# ============================================================================

@router.post("/channels", response_model=AlertChannelResponse)
def create_alert_channel(
    channel: AlertChannelCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Create a new alert channel for notifications.
    
    **Supported Channels**:
    
    1. **Slack** (channel_type: "slack")
       ```json
       {
         "channel_type": "slack",
         "configuration": {
           "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
         }
       }
       ```
       Get webhook URL from: Slack Settings → Incoming Webhooks
    
    2. **Email** (channel_type: "email")
       ```json
       {
         "channel_type": "email",
         "configuration": {
           "email": "alerts@your-company.com"
         }
       }
       ```
       Requires SMTP configuration in environment variables
    
    3. **Webhook** (channel_type: "webhook")
       ```json
       {
         "channel_type": "webhook",
         "configuration": {
           "webhook_url": "https://your-server.com/webhook"
         }
       }
       ```
       Will receive JSON POST requests with alert data
    """
    try:
        # Create channel
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
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert channel: {str(e)}"
        )


@router.get("/channels", response_model=List[AlertChannelResponse])
def list_alert_channels(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    List all alert channels for the organization.
    """
    channels = db.query(models.AlertChannel).filter(
        models.AlertChannel.organization_id == organization.id
    ).all()
    
    return channels


@router.delete("/channels/{channel_id}")
def delete_alert_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Delete an alert channel.
    """
    channel = db.query(models.AlertChannel).filter(
        models.AlertChannel.id == channel_id,
        models.AlertChannel.organization_id == organization.id
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Alert channel not found")
    
    try:
        db.delete(channel)
        db.commit()
        return {"message": "Alert channel deleted"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete alert channel: {str(e)}"
        )


# ============================================================================
# Alert Configuration Endpoints
# ============================================================================

@router.post("/config", response_model=AlertConfigResponse)
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
    
    try:
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
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert config: {str(e)}"
        )


@router.get("/config", response_model=List[AlertConfigResponse])
def list_alert_configs(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    List all alert configurations for the organization.
    """
    configs = db.query(models.AlertConfig).filter(
        models.AlertConfig.organization_id == organization.id
    ).all()
    
    return configs




# ============================================================================
# Testing & Manual Triggering
# ============================================================================


@router.put("/config/{config_id}", response_model=AlertConfigResponse)
def update_alert_config(
    config_id: int,
    config: AlertConfigCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Update an existing alert configuration.
    """
    db_config = db.query(models.AlertConfig).filter(
        models.AlertConfig.id == config_id,
        models.AlertConfig.organization_id == organization.id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    update_data = config.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    db.commit()
    db.refresh(db_config)
    return db_config

