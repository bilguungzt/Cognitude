"""
Analytics API endpoints for LLM usage metrics.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.usage_analyzer import UsageAnalyzer


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/usage", response_model=schemas.AnalyticsResponse)
def get_usage_analytics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get comprehensive usage analytics and cost metrics.
    
    Returns aggregated metrics including:
    - Total requests made through the LLM proxy
    - Total cost in USD (based on token usage)
    - Average latency in milliseconds
    - Daily breakdown of usage and costs
    - Provider breakdown showing usage per LLM provider
    - Model breakdown showing usage per model
    - Cache statistics (hit rate, savings)
    
    Optional filters:
    - start_date: Filter from this date (inclusive)
    - end_date: Filter until this date (inclusive)
    """
    analytics = crud.get_analytics(
        db,
        organization.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return analytics


@router.get("/recommendations")
def get_optimization_recommendations(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=90),
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get AI-powered optimization recommendations based on usage patterns.
    
    Analyzes your LLM usage over the specified period and generates actionable
    recommendations to reduce costs and improve efficiency.
    
    **Recommendation Types**:
    1. **Cache Opportunities**: Identify duplicate requests that could be cached
    2. **Model Downgrades**: Suggest cheaper models for simple tasks
    3. **Max Tokens Optimization**: Optimize token limits based on actual usage
    4. **Smart Routing**: Enable automatic model selection for cost savings
    5. **Prompt Optimization**: Identify long prompts that could be shortened
    
    **Each recommendation includes**:
    - Clear title and description
    - Actionable steps to implement
    - Estimated monthly savings in USD
    - Priority level (high/medium/low)
    - Impact assessment
    - Detailed metrics and analysis
    
    **Example Use Cases**:
    - "Where can I save the most money?"
    - "Are my prompts too long?"
    - "Should I switch to cheaper models?"
    - "Is caching working effectively?"
    
    **Parameters**:
    - days: Analysis period (default 30, max 90)
    
    **Returns**:
    List of recommendations sorted by estimated savings (highest first)
    """
    analyzer = UsageAnalyzer(db, organization.id)
    recommendations = analyzer.get_recommendations(days)
    
    # Calculate total potential savings
    total_savings = sum(r.get('estimated_monthly_savings_usd', 0) for r in recommendations)
    
    return {
        'analysis_period_days': days,
        'total_recommendations': len(recommendations),
        'total_potential_monthly_savings_usd': round(total_savings, 2),
        'recommendations': recommendations
    }


@router.get("/breakdown")
def get_usage_breakdown(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=90),
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get detailed usage breakdown and statistics.
    
    Provides comprehensive analysis of your LLM usage including:
    - Total requests, costs, and tokens
    - Cache performance metrics
    - Cost breakdown by model
    - Cost breakdown by provider
    - Daily usage trends
    - Average latency
    
    **Perfect for**:
    - Building custom dashboards
    - Tracking usage trends
    - Understanding cost distribution
    - Monitoring cache effectiveness
    - Analyzing latency patterns
    
    **Parameters**:
    - days: Analysis period (default 30, max 90)
    
    **Returns**:
    Comprehensive usage statistics with multiple breakdowns
    """
    analyzer = UsageAnalyzer(db, organization.id)
    breakdown = analyzer.get_usage_breakdown(days)
    
    return breakdown
