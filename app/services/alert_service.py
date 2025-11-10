"""
Notification service for sending alerts via Slack, email, and webhooks.
"""
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models


class NotificationService:
    """
    Handles sending notifications through various channels.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_slack_notification(
        self,
        webhook_url: str,
        message: str,
        title: Optional[str] = None,
        color: str = "#36a64f",
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send notification to Slack via webhook.
        
        Args:
            webhook_url: Slack webhook URL
            message: Main message text
            title: Optional title/header
            color: Color bar (#36a64f=green, #ff0000=red, #ffaa00=orange)
            fields: Optional list of field dicts with 'title' and 'value'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            attachment = {
                "color": color,
                "text": message,
                "ts": int(datetime.utcnow().timestamp())
            }
            
            if title:
                attachment["title"] = title
            
            if fields:
                attachment["fields"] = [
                    {
                        "title": field.get("title", ""),
                        "value": field.get("value", ""),
                        "short": field.get("short", True)
                    }
                    for field in fields
                ]
            
            payload = {
                "attachments": [attachment]
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Slack notification error: {e}")
            return False
    
    def send_email_notification(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        from_email: Optional[str] = None,
        smtp_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            from_email: Sender email (defaults to env var)
            smtp_config: SMTP server config (host, port, username, password)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use environment variables or provided config
            if not smtp_config:
                smtp_config = {
                    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                    "port": int(os.getenv("SMTP_PORT", "587")),
                    "username": os.getenv("SMTP_USERNAME"),
                    "password": os.getenv("SMTP_PASSWORD")
                }
            
            if not from_email:
                from_email = os.getenv("ALERT_FROM_EMAIL", smtp_config.get("username"))
            
            if not smtp_config.get("username") or not smtp_config.get("password"):
                print("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email
            
            # Add HTML body
            html_part = MIMEText(body_html, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
                server.starttls()
                server.login(smtp_config["username"], smtp_config["password"])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email notification error: {e}")
            return False
    
    def send_webhook_notification(
        self,
        webhook_url: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Send generic webhook notification.
        
        Args:
            webhook_url: Webhook URL
            payload: JSON payload to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code in [200, 201, 202, 204]
            
        except Exception as e:
            print(f"Webhook notification error: {e}")
            return False
    
    def notify_cost_threshold(
        self,
        organization_id: int,
        alert_config: models.AlertConfig,
        current_cost: Decimal,
        period: str = "daily"
    ) -> Dict[str, int]:
        """
        Send cost threshold alert to all configured channels.
        
        Args:
            organization_id: Organization ID
            alert_config: Alert configuration that was triggered
            current_cost: Current cost that triggered the alert
            period: Time period (daily, weekly, monthly)
            
        Returns:
            Dict with counts of successful sends per channel type
        """
        results = {"slack": 0, "email": 0, "webhook": 0}
        
        # Get active alert channels
        channels = self.db.query(models.AlertChannel).filter(
            models.AlertChannel.organization_id == organization_id,
            models.AlertChannel.is_active == True
        ).all()
        
        if not channels:
            return results
        
        # Get organization name
        org = self.db.query(models.Organization).filter(
            models.Organization.id == organization_id
        ).first()
        org_name = org.name if org else f"Organization {organization_id}"
        
        # Prepare message
        threshold = float(alert_config.threshold_usd)
        cost = float(current_cost)
        overage = cost - threshold
        overage_pct = (overage / threshold * 100) if threshold > 0 else 0
        
        color = "#ff0000" if overage_pct > 50 else "#ffaa00"
        
        # Send to each channel
        for channel in channels:
            config = channel.configuration
            
            if channel.channel_type == "slack" and config.get("webhook_url"):
                title = f"🚨 Cost Alert: {period.title()} Threshold Exceeded"
                message = (
                    f"Your {period} LLM costs have exceeded the configured threshold.\n\n"
                    f"**Current Cost:** ${cost:.2f}\n"
                    f"**Threshold:** ${threshold:.2f}\n"
                    f"**Overage:** ${overage:.2f} ({overage_pct:.0f}% over)\n"
                )
                
                fields = [
                    {"title": "Organization", "value": org_name, "short": True},
                    {"title": "Period", "value": period.title(), "short": True},
                    {"title": "Current Cost", "value": f"${cost:.2f}", "short": True},
                    {"title": "Threshold", "value": f"${threshold:.2f}", "short": True}
                ]
                
                if self.send_slack_notification(
                    webhook_url=config["webhook_url"],
                    title=title,
                    message=message,
                    color=color,
                    fields=fields
                ):
                    results["slack"] += 1
            
            elif channel.channel_type == "email" and config.get("email"):
                subject = f"🚨 Cost Alert: {period.title()} Threshold Exceeded"
                
                body_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #d32f2f;">🚨 Cost Alert</h2>
                        <p>Your {period} LLM costs have exceeded the configured threshold.</p>
                        
                        <div style="background-color: #fff3cd; border-left: 4px solid #ffaa00; padding: 15px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Organization:</td>
                                    <td style="padding: 8px;">{org_name}</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="padding: 8px; font-weight: bold;">Period:</td>
                                    <td style="padding: 8px;">{period.title()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Current Cost:</td>
                                    <td style="padding: 8px; color: #d32f2f; font-size: 18px;">${cost:.2f}</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="padding: 8px; font-weight: bold;">Threshold:</td>
                                    <td style="padding: 8px;">${threshold:.2f}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Overage:</td>
                                    <td style="padding: 8px; color: #d32f2f;">${overage:.2f} ({overage_pct:.0f}% over)</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p style="margin-top: 20px;">
                            <strong>Recommendations:</strong>
                        </p>
                        <ul>
                            <li>Review your usage at <a href="http://your-server:8000/analytics/usage">Analytics Dashboard</a></li>
                            <li>Check optimization recommendations at <a href="http://your-server:8000/analytics/recommendations">Recommendations</a></li>
                            <li>Consider enabling smart routing for automatic cost optimization</li>
                        </ul>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                            This is an automated alert from Cognitude LLM Proxy. To manage alert settings, visit your dashboard.
                        </p>
                    </div>
                </body>
                </html>
                """
                
                if self.send_email_notification(
                    to_email=config["email"],
                    subject=subject,
                    body_html=body_html
                ):
                    results["email"] += 1
            
            elif channel.channel_type == "webhook" and config.get("webhook_url"):
                payload = {
                    "event": "cost_threshold_exceeded",
                    "organization_id": organization_id,
                    "organization_name": org_name,
                    "period": period,
                    "current_cost_usd": cost,
                    "threshold_usd": threshold,
                    "overage_usd": overage,
                    "overage_percentage": overage_pct,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if self.send_webhook_notification(
                    webhook_url=config["webhook_url"],
                    payload=payload
                ):
                    results["webhook"] += 1
        
        return results
    
    def send_daily_summary(
        self,
        organization_id: int,
        summary_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Send daily usage summary to all configured channels.
        
        Args:
            organization_id: Organization ID
            summary_data: Summary statistics (requests, cost, cache_hit_rate, etc.)
            
        Returns:
            Dict with counts of successful sends per channel type
        """
        results = {"slack": 0, "email": 0, "webhook": 0}
        
        # Get active alert channels
        channels = self.db.query(models.AlertChannel).filter(
            models.AlertChannel.organization_id == organization_id,
            models.AlertChannel.is_active == True
        ).all()
        
        if not channels:
            return results
        
        # Get organization name
        org = self.db.query(models.Organization).filter(
            models.Organization.id == organization_id
        ).first()
        org_name = org.name if org else f"Organization {organization_id}"
        
        # Extract summary data
        requests = summary_data.get("requests", 0)
        cost = summary_data.get("cost_usd", 0.0)
        cache_hit_rate = summary_data.get("cache_hit_rate", 0.0)
        cached_requests = summary_data.get("cached_requests", 0)
        cache_savings = summary_data.get("cache_savings_usd", 0.0)
        
        # Send to each channel
        for channel in channels:
            config = channel.configuration
            
            if channel.channel_type == "slack" and config.get("webhook_url"):
                title = f"📊 Daily Summary: {org_name}"
                message = (
                    f"Here's your LLM usage summary for {datetime.utcnow().strftime('%B %d, %Y')}:\n\n"
                    f"**Total Requests:** {requests:,}\n"
                    f"**Total Cost:** ${cost:.2f}\n"
                    f"**Cache Hit Rate:** {cache_hit_rate:.1f}%\n"
                    f"**Cache Savings:** ${cache_savings:.2f}\n"
                )
                
                fields = [
                    {"title": "Requests", "value": f"{requests:,}", "short": True},
                    {"title": "Cost", "value": f"${cost:.2f}", "short": True},
                    {"title": "Cache Hits", "value": f"{cache_hit_rate:.1f}%", "short": True},
                    {"title": "Savings", "value": f"${cache_savings:.2f}", "short": True}
                ]
                
                if self.send_slack_notification(
                    webhook_url=config["webhook_url"],
                    title=title,
                    message=message,
                    color="#36a64f",
                    fields=fields
                ):
                    results["slack"] += 1
            
            elif channel.channel_type == "email" and config.get("email"):
                subject = f"📊 Daily Summary: {datetime.utcnow().strftime('%B %d, %Y')}"
                
                body_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2e7d32;">📊 Daily Summary</h2>
                        <p>Here's your LLM usage summary for <strong>{datetime.utcnow().strftime('%B %d, %Y')}</strong>:</p>
                        
                        <div style="background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Total Requests:</td>
                                    <td style="padding: 8px;">{requests:,}</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="padding: 8px; font-weight: bold;">Total Cost:</td>
                                    <td style="padding: 8px; font-size: 18px; color: #2e7d32;">${cost:.2f}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Cache Hit Rate:</td>
                                    <td style="padding: 8px;">{cache_hit_rate:.1f}%</td>
                                </tr>
                                <tr style="background-color: #f9f9f9;">
                                    <td style="padding: 8px; font-weight: bold;">Cached Requests:</td>
                                    <td style="padding: 8px;">{cached_requests:,}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Cache Savings:</td>
                                    <td style="padding: 8px; color: #2e7d32;">${cache_savings:.2f}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p style="margin-top: 20px;">
                            <a href="http://your-server:8000/analytics/usage" style="display: inline-block; padding: 10px 20px; background-color: #2e7d32; color: white; text-decoration: none; border-radius: 4px;">
                                View Detailed Analytics
                            </a>
                        </p>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                            This is an automated daily summary from Cognitude LLM Proxy.
                        </p>
                    </div>
                </body>
                </html>
                """
                
                if self.send_email_notification(
                    to_email=config["email"],
                    subject=subject,
                    body_html=body_html
                ):
                    results["email"] += 1
        
        return results
    
    def check_and_send_cost_alerts(self, organization_id: int) -> Dict[str, Any]:
        """
        Check cost thresholds and send alerts if exceeded.
        
        Args:
            organization_id: Organization ID to check
            
        Returns:
            Dict with alert results
        """
        results = {
            "alerts_checked": 0,
            "alerts_triggered": 0,
            "notifications_sent": {"slack": 0, "email": 0, "webhook": 0}
        }
        
        # Get enabled alert configs
        alert_configs = self.db.query(models.AlertConfig).filter(
            models.AlertConfig.organization_id == organization_id,
            models.AlertConfig.enabled == True
        ).all()
        
        results["alerts_checked"] = len(alert_configs)
        
        for config in alert_configs:
            # Calculate period start date
            now = datetime.utcnow()
            if config.alert_type == "daily_cost":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period = "daily"
            elif config.alert_type == "weekly_cost":
                days_since_monday = now.weekday()
                start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                period = "weekly"
            elif config.alert_type == "monthly_cost":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                period = "monthly"
            else:
                continue
            
            # Get current cost for period
            current_cost = self.db.query(
                func.sum(models.LLMRequest.cost_usd)
            ).filter(
                models.LLMRequest.organization_id == organization_id,
                models.LLMRequest.timestamp >= start_date,
                models.LLMRequest.cached == False  # Only count non-cached costs
            ).scalar() or Decimal("0.0")
            
            # Check if threshold exceeded
            if current_cost > config.threshold_usd:
                # Check if we should send (don't spam - once per period)
                should_send = True
                if config.last_triggered:
                    if config.alert_type == "daily_cost" and config.last_triggered >= start_date:
                        should_send = False
                    elif config.alert_type == "weekly_cost" and config.last_triggered >= start_date:
                        should_send = False
                    elif config.alert_type == "monthly_cost" and config.last_triggered >= start_date:
                        should_send = False
                
                if should_send:
                    # Send notifications
                    notification_results = self.notify_cost_threshold(
                        organization_id=organization_id,
                        alert_config=config,
                        current_cost=current_cost,
                        period=period
                    )
                    
                    # Update last_triggered
                    config.last_triggered = now
                    self.db.commit()
                    
                    results["alerts_triggered"] += 1
                    for channel_type, count in notification_results.items():
                        results["notifications_sent"][channel_type] += count
        
        return results
