"""Notification service for sending drift alerts via email and Slack."""
from typing import Optional
import aiohttp
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings

settings = get_settings()


class NotificationService:
    """Handle sending notifications through various channels."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Email configuration
        self.fm = None
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.FROM_EMAIL and settings.SMTP_PORT and settings.SMTP_SERVER:
            self.mail_conf = ConnectionConfig(
                MAIL_USERNAME=settings.SMTP_USERNAME,
                MAIL_PASSWORD=settings.SMTP_PASSWORD,
                MAIL_FROM=settings.FROM_EMAIL,
                MAIL_PORT=settings.SMTP_PORT,
                MAIL_SERVER=settings.SMTP_SERVER,
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True
            )
            self.fm = FastMail(self.mail_conf)
    
    async def notify_drift(
        self, 
        model: models.Model, 
        drift_score: float, 
        p_value: float
    ) -> None:
        """Send drift notifications through all active channels."""
        # Get organization's alert channels
        channels = (
            self.db.query(models.AlertChannel)
            .filter(
                models.AlertChannel.organization_id == model.organization_id,
                models.AlertChannel.is_active == True  # noqa: E712
            )
            .all()
        )
        
        for channel in channels:
            try:
                if channel.channel_type == "email":
                    await self.send_email_alert(channel, model, drift_score, p_value)
                elif channel.channel_type == "slack":
                    await self.send_slack_alert(channel, model, drift_score, p_value)
            except Exception as e:
                print(f"Failed to send alert via {channel.channel_type}: {e}")
    
    async def send_email_alert(
        self,
        channel: models.AlertChannel,
        model: models.Model,
        drift_score: float,
        p_value: float
    ) -> None:
        """Send email alert about drift detection."""
        email = channel.configuration.get("email")
        if not email:
            return
        
        if not self.fm:
            print(f"[DEV MODE] Email not configured. Would send to {email}")
            return
        
        severity = "HIGH" if drift_score > 0.8 else "MEDIUM" if drift_score > 0.5 else "LOW"
        
        subject = f"🚨 Drift Alert: {model.name} - {severity} Severity"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">Drift Detected in Model: {model.name}</h2>
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px;">
                    <p><strong>Model ID:</strong> {model.id}</p>
                    <p><strong>Drift Score:</strong> {drift_score:.3f}</p>
                    <p><strong>P-Value:</strong> {p_value:.4f}</p>
                    <p><strong>Severity:</strong> <span style="color: #d32f2f;">{severity}</span></p>
                </div>
                <p>
                    This indicates that your model's predictions have statistically significantly 
                    drifted from the baseline distribution.
                </p>
                <p>
                    <strong>Recommended Actions:</strong>
                    <ul>
                        <li>Review recent input data for anomalies</li>
                        <li>Check if the underlying data distribution has changed</li>
                        <li>Consider retraining your model with recent data</li>
                    </ul>
                </p>
                <p>
                    <a href="https://app.cognitude.io/models/{model.id}" 
                       style="background-color: #1976d2; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        View Dashboard
                    </a>
                </p>
            </body>
        </html>
        """
        
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=html_body,
            subtype="html",
        )
        
        try:
            await self.fm.send_message(message)
            print(f"Email sent to {email}")
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    async def send_slack_alert(
        self,
        channel: models.AlertChannel,
        model: models.Model,
        drift_score: float,
        p_value: float
    ) -> None:
        """Send Slack alert about drift detection."""
        webhook_url = channel.configuration.get("webhook_url")
        if not webhook_url:
            return
        
        severity_color = "#d32f2f" if drift_score > 0.8 else "#ff9800" if drift_score > 0.5 else "#4caf50"
        severity = "HIGH" if drift_score > 0.8 else "MEDIUM" if drift_score > 0.5 else "LOW"
        
        payload = {
            "text": f"🚨 Drift Alert: {model.name}",
            "attachments": [
                {
                    "color": severity_color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"🚨 Drift Detected: {model.name}"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Model ID:*\n{model.id}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Severity:*\n{severity}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Drift Score:*\n{drift_score:.3f}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*P-Value:*\n{p_value:.4f}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Your model's predictions have statistically significantly drifted from the baseline distribution."
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Dashboard"
                                    },
                                    "url": f"https://app.cognitude.io/models/{model.id}",
                                    "style": "primary"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        print(f"Slack alert sent for model {model.id}")
                    else:
                        print(f"Slack webhook returned {resp.status}")
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
