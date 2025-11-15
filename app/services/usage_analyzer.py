"""
Usage pattern analysis and optimization recommendations engine.
Analyzes LLM usage data to generate actionable cost-saving suggestions.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .. import models
from ..services.pricing import PRICING


class UsageAnalyzer:
    """
    Analyzes usage patterns and generates optimization recommendations.
    """
    
    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id
    
    def get_recommendations(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Generate all optimization recommendations.
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            List of recommendation dicts with estimated savings
        """
        recommendations = []
        
        # 1. Cache opportunity analysis
        cache_rec = self._analyze_cache_opportunity(days)
        if cache_rec:
            recommendations.append(cache_rec)
        
        # 2. Model downgrade opportunities
        model_recs = self._analyze_model_downgrade(days)
        recommendations.extend(model_recs)
        
        # 3. Max tokens optimization
        tokens_rec = self._analyze_max_tokens(days)
        if tokens_rec:
            recommendations.append(tokens_rec)
        
        # 4. Smart routing adoption
        smart_rec = self._analyze_smart_routing_adoption(days)
        if smart_rec:
            recommendations.append(smart_rec)
        
        # 5. High-cost prompt patterns
        prompt_recs = self._analyze_prompt_patterns(days)
        recommendations.extend(prompt_recs)
        
        # Sort by estimated savings (highest first)
        recommendations.sort(key=lambda x: x.get('estimated_monthly_savings_usd', 0), reverse=True)
        
        return recommendations
    
    def _analyze_cache_opportunity(self, days: int) -> Optional[Dict[str, Any]]:
        """
        Analyze requests that could benefit from caching.
        Identifies frequently repeated prompts without cache hits.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get requests with same cache key (duplicate prompts)
        duplicate_requests = self.db.query(
            models.LLMRequest.cache_key,
            func.count(models.LLMRequest.id).label('count'),
            func.sum(models.LLMRequest.cost_usd).label('total_cost'),
            func.avg(models.LLMRequest.cost_usd).label('avg_cost')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.cache_key.isnot(None),
            models.LLMRequest.cache_hit == False
        ).group_by(
            models.LLMRequest.cache_key
        ).having(
            func.count(models.LLMRequest.id) > 1  # At least 2 requests
        ).all()
        
        if not duplicate_requests:
            return None
        
        # Calculate potential savings
        total_duplicate_cost = sum(float(req.total_cost or 0) for req in duplicate_requests)
        num_duplicates = sum(req.count - 1 for req in duplicate_requests)  # Subtract first request
        
        if total_duplicate_cost < 1.0:  # Less than $1 savings
            return None
        
        # Estimate monthly savings
        daily_savings = total_duplicate_cost / days
        monthly_savings = daily_savings * 30
        
        return {
            'type': 'cache_opportunity',
            'priority': 'high',
            'title': 'Enable Caching for Duplicate Requests',
            'description': f'Found {num_duplicates} duplicate requests that could be cached. '
                          f'Caching is already enabled but these prompts were not cached yet.',
            'action': 'Review your request patterns. Duplicate prompts will be automatically cached on subsequent requests.',
            'estimated_monthly_savings_usd': round(monthly_savings, 2),
            'impact': 'high' if monthly_savings > 50 else 'medium',
            'details': {
                'duplicate_request_groups': len(duplicate_requests),
                'total_duplicate_requests': num_duplicates,
                'analysis_period_days': days
            }
        }
    
    def _analyze_model_downgrade(self, days: int) -> List[Dict[str, Any]]:
        """
        Identify requests using expensive models for simple tasks.
        Suggests cheaper alternatives.
        """
        recommendations = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get usage by model
        model_usage = self.db.query(
            models.LLMRequest.model,
            func.count(models.LLMRequest.id).label('request_count'),
            func.sum(models.LLMRequest.cost_usd).label('total_cost'),
            func.avg(models.LLMRequest.prompt_tokens).label('avg_prompt_tokens'),
            func.avg(models.LLMRequest.completion_tokens).label('avg_completion_tokens')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.cache_hit == False
        ).group_by(
            models.LLMRequest.model
        ).all()
        
        # Expensive models that might be over-used
        expensive_models = {
            'gpt-4': ('gpt-4o-mini', 0.0005, 12),  # (cheaper_alternative, alt_cost, savings_multiplier)
            'gpt-4-0125-preview': ('gpt-4o-mini', 0.0005, 12),
            'gpt-4-turbo-preview': ('gpt-4o-mini', 0.0005, 6),
            'claude-3-opus-20240229': ('claude-3-sonnet-20240229', 0.003, 5),
        }
        
        for usage in model_usage:
            model = usage.model
            if model not in expensive_models:
                continue
            
            # Check if prompts are relatively short (potential simple tasks)
            avg_prompt_tokens = float(usage.avg_prompt_tokens or 0)
            avg_completion_tokens = float(usage.avg_completion_tokens or 0)
            
            # Simple task indicators: short prompts (<200 tokens) or short completions (<300 tokens)
            if avg_prompt_tokens < 200 or avg_completion_tokens < 300:
                cheaper_model, alt_cost, multiplier = expensive_models[model]
                
                # Calculate savings
                current_cost = float(usage.total_cost or 0)
                estimated_cheaper_cost = current_cost / multiplier
                savings = current_cost - estimated_cheaper_cost
                
                # Extrapolate to monthly
                daily_savings = savings / days
                monthly_savings = daily_savings * 30
                
                if monthly_savings > 5:  # At least $5/month savings
                    recommendations.append({
                        'type': 'model_downgrade',
                        'priority': 'high' if monthly_savings > 50 else 'medium',
                        'title': f'Consider Switching from {model} to {cheaper_model}',
                        'description': f'Your {model} requests have short prompts (avg {int(avg_prompt_tokens)} tokens) '
                                      f'and completions (avg {int(avg_completion_tokens)} tokens), suggesting simple tasks. '
                                      f'{cheaper_model} could handle these at {multiplier}x lower cost.',
                        'action': f'Test {cheaper_model} for these requests or use Smart Routing endpoint to auto-select models.',
                        'estimated_monthly_savings_usd': round(monthly_savings, 2),
                        'impact': 'high' if monthly_savings > 50 else 'medium',
                        'details': {
                            'current_model': model,
                            'suggested_model': cheaper_model,
                            'request_count': usage.request_count,
                            'avg_prompt_tokens': int(avg_prompt_tokens),
                            'avg_completion_tokens': int(avg_completion_tokens),
                            'current_monthly_cost': round(current_cost / days * 30, 2),
                            'estimated_monthly_cost': round(estimated_cheaper_cost / days * 30, 2)
                        }
                    })
        
        return recommendations
    
    def _analyze_max_tokens(self, days: int) -> Optional[Dict[str, Any]]:
        """
        Identify requests with excessive max_tokens settings.
        Many users set high max_tokens but don't use them.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get requests where completion tokens are much lower than typical max_tokens
        # We'll look at requests and see if there's a pattern
        requests = self.db.query(
            models.LLMRequest.completion_tokens,
            models.LLMRequest.cost_usd
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.cache_hit == False,
            models.LLMRequest.completion_tokens.isnot(None)
        ).all()
        
        if not requests or len(requests) < 10:
            return None
        
        # Calculate statistics
        completion_tokens = [float(req.completion_tokens or 0) for req in requests]
        avg_completion = sum(completion_tokens) / len(completion_tokens)
        max_completion = max(completion_tokens)
        
        # If average completion is much lower than max, there's optimization potential
        # Typical default max_tokens is 2048 or 4096
        if avg_completion < 500 and max_completion > 1000:
            # Estimate savings from reducing max_tokens
            # Lower max_tokens can reduce costs in some cases (model-dependent)
            # Conservative estimate: 5-10% savings
            total_cost = sum(float(req.cost_usd or 0) for req in requests)
            estimated_savings = total_cost * 0.075  # 7.5% savings
            monthly_savings = (estimated_savings / days) * 30
            
            if monthly_savings > 5:
                return {
                    'type': 'max_tokens_optimization',
                    'priority': 'low',
                    'title': 'Optimize max_tokens Parameter',
                    'description': f'Your requests average {int(avg_completion)} completion tokens but may have '
                                  f'higher max_tokens limits. Setting appropriate max_tokens can improve response time '
                                  f'and potentially reduce costs.',
                    'action': f'Consider setting max_tokens to {int(avg_completion * 1.5)} based on your usage patterns.',
                    'estimated_monthly_savings_usd': round(monthly_savings, 2),
                    'impact': 'low',
                    'details': {
                        'avg_completion_tokens': int(avg_completion),
                        'max_completion_tokens': int(max_completion),
                        'suggested_max_tokens': int(avg_completion * 1.5),
                        'request_count': len(requests)
                    }
                }
        
        return None
    
    def _analyze_smart_routing_adoption(self, days: int) -> Optional[Dict[str, Any]]:
        """
        Check if organization is using smart routing.
        If not, estimate potential savings.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Check if any requests used smart routing (we'd need to track this)
        # For now, estimate based on model usage patterns
        
        total_requests = self.db.query(func.count(models.LLMRequest.id)).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.cache_hit == False
        ).scalar()
        
        if not total_requests or total_requests < 10:
            return None
        
        # Get model distribution
        expensive_model_cost = self.db.query(
            func.sum(models.LLMRequest.cost_usd)
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.model.in_(['gpt-4', 'gpt-4-0125-preview', 'gpt-4-turbo-preview', 'claude-3-opus-20240229']),
            models.LLMRequest.cache_hit == False
        ).scalar() or 0
        
        expensive_cost = float(expensive_model_cost)
        
        if expensive_cost > 10:  # At least $10 spent on expensive models
            # Estimate 30% savings from smart routing
            estimated_savings = expensive_cost * 0.35
            monthly_savings = (estimated_savings / days) * 30
            
            return {
                'type': 'smart_routing_adoption',
                'priority': 'high',
                'title': 'Enable Smart Routing for Automatic Cost Optimization',
                'description': f'You are using expensive models (GPT-4, Claude Opus) for all requests. '
                              f'Smart routing can automatically select cheaper models for simple tasks, '
                              f'potentially saving 30-50% on costs.',
                'action': 'Use the /v1/smart/completions endpoint instead of /v1/chat/completions to enable automatic model selection.',
                'estimated_monthly_savings_usd': round(monthly_savings, 2),
                'impact': 'high',
                'details': {
                    'current_expensive_model_cost': round(expensive_cost / days * 30, 2),
                    'estimated_cost_with_smart_routing': round((expensive_cost * 0.65) / days * 30, 2),
                    'total_requests': total_requests
                }
            }
        
        return None
    
    def _analyze_prompt_patterns(self, days: int) -> List[Dict[str, Any]]:
        """
        Analyze prompt patterns for optimization opportunities.
        """
        recommendations = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get requests with very high token counts
        high_token_requests = self.db.query(
            func.count(models.LLMRequest.id).label('count'),
            func.sum(models.LLMRequest.cost_usd).label('total_cost'),
            func.avg(models.LLMRequest.prompt_tokens).label('avg_prompt_tokens')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.prompt_tokens > 2000,  # Very long prompts
            models.LLMRequest.cache_hit == False
        ).first()
        
        if high_token_requests and high_token_requests.count > 0:
            count = high_token_requests.count
            total_cost = float(high_token_requests.total_cost or 0)
            avg_tokens = float(high_token_requests.avg_prompt_tokens or 0)
            
            # Estimate 20% savings from prompt optimization
            estimated_savings = total_cost * 0.20
            monthly_savings = (estimated_savings / days) * 30
            
            if monthly_savings > 5:
                recommendations.append({
                    'type': 'prompt_optimization',
                    'priority': 'medium',
                    'title': 'Optimize Long Prompts',
                    'description': f'Found {count} requests with very long prompts (avg {int(avg_tokens)} tokens). '
                                  f'Reducing prompt length through better prompt engineering can significantly reduce costs.',
                    'action': 'Review your prompts for redundancy. Consider using prompt templates, removing unnecessary context, '
                             f'or breaking complex prompts into smaller requests.',
                    'estimated_monthly_savings_usd': round(monthly_savings, 2),
                    'impact': 'medium',
                    'details': {
                        'high_token_request_count': count,
                        'avg_prompt_tokens': int(avg_tokens),
                        'current_monthly_cost': round(total_cost / days * 30, 2)
                    }
                })
        
        return recommendations
    
    def get_usage_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed usage breakdown for analytics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with usage statistics and breakdowns
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total stats
        total_stats = self.db.query(
            func.count(models.LLMRequest.id).label('total_requests'),
            func.sum(models.LLMRequest.cost_usd).label('total_cost'),
            func.sum(models.LLMRequest.prompt_tokens).label('total_prompt_tokens'),
            func.sum(models.LLMRequest.completion_tokens).label('total_completion_tokens'),
            func.avg(models.LLMRequest.latency_ms).label('avg_latency_ms')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date
        ).first()
        
        if not total_stats:
            # No data available
            return {
                'period_days': days,
                'total': {'requests': 0, 'cost_usd': 0.0, 'prompt_tokens': 0, 'completion_tokens': 0, 'avg_latency_ms': 0.0},
                'cache': {'cached_requests': 0, 'cache_hit_rate': 0.0, 'estimated_savings_usd': 0.0},
                'by_model': [],
                'by_provider': [],
                'daily_breakdown': []
            }
        
        # Cache stats
        cache_stats = self.db.query(
            func.count(models.LLMRequest.id).label('cached_requests'),
            func.sum(models.LLMRequest.cost_usd).label('cached_cost_saved')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date,
            models.LLMRequest.cache_hit == True
        ).first()
        
        if not cache_stats:
            # Create a mock stats object with default values
            class MockCacheStats:
                cached_requests = 0
                cached_cost_saved = 0
            cache_stats = MockCacheStats()
        
        # By model
        by_model = self.db.query(
            models.LLMRequest.model,
            func.count(models.LLMRequest.id).label('requests'),
            func.sum(models.LLMRequest.cost_usd).label('cost')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date
        ).group_by(
            models.LLMRequest.model
        ).order_by(
            desc('cost')
        ).all()
        
        # By provider
        by_provider = self.db.query(
            models.LLMRequest.provider,
            func.count(models.LLMRequest.id).label('requests'),
            func.sum(models.LLMRequest.cost_usd).label('cost')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date
        ).group_by(
            models.LLMRequest.provider
        ).order_by(
            desc('cost')
        ).all()
        
        # Daily breakdown
        daily_breakdown = self.db.query(
            func.date(models.LLMRequest.timestamp).label('date'),
            func.count(models.LLMRequest.id).label('requests'),
            func.sum(models.LLMRequest.cost_usd).label('cost'),
            func.sum(func.cast(models.LLMRequest.cache_hit, func.Integer)).label('cached_requests')
        ).filter(
            models.LLMRequest.organization_id == self.organization_id,
            models.LLMRequest.timestamp >= cutoff_date
        ).group_by(
            func.date(models.LLMRequest.timestamp)
        ).order_by(
            'date'
        ).all()
        
        return {
            'period_days': days,
            'total': {
                'requests': total_stats.total_requests or 0,
                'cost_usd': round(float(total_stats.total_cost or 0), 2),
                'prompt_tokens': int(total_stats.total_prompt_tokens or 0),
                'completion_tokens': int(total_stats.total_completion_tokens or 0),
                'avg_latency_ms': round(float(total_stats.avg_latency_ms or 0), 0)
            },
            'cache': {
                'cached_requests': cache_stats.cached_requests or 0,
                'cache_hit_rate': round((cache_stats.cached_requests or 0) / (total_stats.total_requests or 1) * 100, 1),
                'estimated_savings_usd': round(float(cache_stats.cached_cost_saved or 0), 2)
            },
            'by_model': [
                {
                    'model': row.model,
                    'requests': row.requests,
                    'cost_usd': round(float(row.cost or 0), 2),
                    'percentage': round((row.requests / (total_stats.total_requests or 1)) * 100, 1)
                }
                for row in by_model
            ],
            'by_provider': [
                {
                    'provider': row.provider,
                    'requests': row.requests,
                    'cost_usd': round(float(row.cost or 0), 2),
                    'percentage': round((row.requests / (total_stats.total_requests or 1)) * 100, 1)
                }
                for row in by_provider
            ],
            'daily_breakdown': [
                {
                    'date': str(row.date),
                    'requests': row.requests,
                    'cost_usd': round(float(row.cost or 0), 2),
                    'cached_requests': row.cached_requests or 0
                }
                for row in daily_breakdown
            ]
        }
