from datetime import datetime, date
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from .. import models
from ..database import SessionLocal
from ..security import verify_api_key
from ..schemas import AnalyticsResponse

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.get(
    "/analytics/usage",
    summary="Get Usage Analytics",
    description="""
## Retrieve aggregated usage metrics and cost analytics

This endpoint provides comprehensive analytics about your API usage, costs, and performance metrics.

### 📊 What You Get:

- **Total requests**: Count of all API calls made through the proxy
- **Total cost**: Sum of all costs in USD (calculated from token usage)
- **Average latency**: Mean response time in milliseconds
- **Daily breakdown**: Usage and costs aggregated per day

### 💡 Use Cases:

- **📈 Dashboard Integration**: Power your analytics dashboard with real-time metrics
- **💰 Cost Tracking**: Monitor spending and track cost savings vs direct OpenAI usage
- **⚡ Performance Monitoring**: Analyze API response times and latency trends
- **📊 Trend Analysis**: Visualize usage patterns over time to optimize consumption

### 🔍 Optional Filters:

You can filter the analytics by date range using query parameters:

- `start_date`: Filter from this date (YYYY-MM-DD format, e.g., 2025-11-01)
- `end_date`: Filter until this date (YYYY-MM-DD format, e.g., 2025-11-09)

If no dates are provided, all historical data is returned.

### 📝 Example Usage:

**Get all-time analytics:**
```bash
curl -X GET "https://api.driftassure.com/analytics/usage" \\
  -H "X-API-Key: your-driftassure-key"
```

**Get analytics for specific date range:**
```bash
curl -X GET "https://api.driftassure.com/analytics/usage?start_date=2025-11-01&end_date=2025-11-09" \\
  -H "X-API-Key: your-driftassure-key"
```

### 📊 Dashboard Integration Tips:

With this data, you can:
- Show "Total Saved" by comparing to direct OpenAI pricing
- Display cache hit rate (if caching enabled)
- Calculate and show cost reduction percentage
- Visualize daily cost trends with charts
- Set up cost alerts when spending exceeds thresholds
- Track API performance and identify slow requests

### 🔗 Data Source:

All metrics come from the usage logs created by the `/v1/chat/completions` proxy endpoint. Every request made through the proxy is automatically logged with:
- Timestamp
- Model used
- Token counts (prompt + completion)
- Calculated cost
- Response latency

This ensures accurate, real-time analytics for your entire organization.
    """,
    tags=["analytics"],
    response_model=AnalyticsResponse,
    responses={
        200: {
            "description": "Successful analytics response",
            "content": {
                "application/json": {
                    "example": {
                        "total_requests": 15420,
                        "total_cost": 127.45,
                        "average_latency": 342.5,
                        "usage_by_day": [
                            {
                                "date": "2025-11-08",
                                "requests": 1180,
                                "cost": 11.20
                            },
                            {
                                "date": "2025-11-09",
                                "requests": 1250,
                                "cost": 12.30
                            }
                        ]
                    }
                }
            }
        },
        401: {
            "description": "Invalid or missing X-API-Key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            }
        }
    }
)
async def get_usage_analytics(
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    organization = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get usage analytics for the authenticated organization.
    Returns total requests, total cost, average latency, and daily usage breakdown.
    """
    # Build query filters
    query = db.query(models.APILog).filter(models.APILog.organization_id == organization.id)
    
    # Apply date filters if provided
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        query = query.filter(func.date(models.APILog.timestamp) >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(func.date(models.APILog.timestamp) <= end_dt)
    
    # Get summary statistics
    summary_result = query.with_entities(
        func.count(models.APILog.id).label('total_requests'),
        func.sum(models.APILog.total_cost).label('total_cost'),
        func.avg(models.APILog.latency_ms).label('average_latency')
    ).first()
    
    if summary_result:
        total_requests = summary_result[0] or 0
        total_cost = float(summary_result[1] or 0.0) if summary_result[1] is not None else 0.0
        average_latency = float(summary_result[2] or 0.0) if summary_result[2] is not None else 0.0
    else:
        total_requests = 0
        total_cost = 0.0
        average_latency = 0.0
    
    # Get daily usage breakdown
    daily_query = db.query(
        func.date(models.APILog.timestamp).label('date'),
        func.count(models.APILog.id).label('requests'),
        func.sum(models.APILog.total_cost).label('cost')
    ).filter(
        models.APILog.organization_id == organization.id
    ).group_by(func.date(models.APILog.timestamp))
    
    # Apply date filters to daily query as well
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        daily_query = daily_query.filter(func.date(models.APILog.timestamp) >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        daily_query = daily_query.filter(func.date(models.APILog.timestamp) <= end_dt)
    
    daily_query = daily_query.order_by(func.date(models.APILog.timestamp))
    daily_results = daily_query.all()
    
    usage_by_day = [
        {
            "date": str(row.date),
            "requests": row.requests,
            "cost": float(row.cost or 0.0)
        }
        for row in daily_results
    ]
    
    return {
        "total_requests": total_requests,
        "total_cost": total_cost,
        "average_latency": average_latency,
        "usage_by_day": usage_by_day
    }
