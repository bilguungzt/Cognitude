"""
Smart routing service for automatic model selection.
Analyzes prompt complexity and selects optimal model based on cost/latency/quality.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal

from ..services.tokens import count_tokens
from ..services.pricing import PRICING


@dataclass
class ModelOption:
    """Represents a model option with its characteristics."""
    name: str
    provider: str
    estimated_cost: Decimal
    estimated_latency_ms: int
    quality_score: float  # 0-1, higher is better
    suitable_for_complexity: List[str]  # ['simple', 'medium', 'complex']


# Model characteristics database
MODEL_CHARACTERISTICS = {
    # OpenAI Models
    "gpt-4": ModelOption(
        name="gpt-4",
        provider="openai",
        estimated_cost=Decimal("0.03"),  # per 1K tokens (averaged)
        estimated_latency_ms=1200,
        quality_score=1.0,
        suitable_for_complexity=["medium", "complex"]
    ),
    "gpt-4-turbo": ModelOption(
        name="gpt-4-turbo",
        provider="openai",
        estimated_cost=Decimal("0.01"),
        estimated_latency_ms=900,
        quality_score=0.98,
        suitable_for_complexity=["medium", "complex"]
    ),
    "gpt-3.5-turbo": ModelOption(
        name="gpt-3.5-turbo",
        provider="openai",
        estimated_cost=Decimal("0.0005"),
        estimated_latency_ms=600,
        quality_score=0.80,
        suitable_for_complexity=["simple", "medium"]
    ),
    
    # Anthropic Models
    "claude-3-opus": ModelOption(
        name="claude-3-opus",
        provider="anthropic",
        estimated_cost=Decimal("0.015"),
        estimated_latency_ms=1400,
        quality_score=0.99,
        suitable_for_complexity=["medium", "complex"]
    ),
    "claude-3-sonnet": ModelOption(
        name="claude-3-sonnet",
        provider="anthropic",
        estimated_cost=Decimal("0.003"),
        estimated_latency_ms=1000,
        quality_score=0.92,
        suitable_for_complexity=["simple", "medium", "complex"]
    ),
    "claude-3-haiku": ModelOption(
        name="claude-3-haiku",
        provider="anthropic",
        estimated_cost=Decimal("0.00025"),
        estimated_latency_ms=400,
        quality_score=0.75,
        suitable_for_complexity=["simple", "medium"]
    ),
    
    # Groq Models (ultra-fast)
    "llama3-70b": ModelOption(
        name="llama3-70b",
        provider="groq",
        estimated_cost=Decimal("0.00059"),
        estimated_latency_ms=250,
        quality_score=0.85,
        suitable_for_complexity=["simple", "medium"]
    ),
    "mixtral-8x7b": ModelOption(
        name="mixtral-8x7b",
        provider="groq",
        estimated_cost=Decimal("0.00027"),
        estimated_latency_ms=200,
        quality_score=0.78,
        suitable_for_complexity=["simple", "medium"]
    ),
    # Google Gemini 2.5 Models
    "gemini-2.5-pro": ModelOption(
        name="gemini-2.5-pro",
        provider="google",
        estimated_cost=Decimal("0.0020"),  # per 1K tokens (input)
        estimated_latency_ms=700,
        quality_score=0.97,
        suitable_for_complexity=["medium", "complex"]
    ),
    "gemini-2.5-flash-lite": ModelOption(
        name="gemini-2.5-flash-lite",
        provider="google",
        estimated_cost=Decimal("0.00025"),  # per 1K tokens (input) - highly cost-effective
        estimated_latency_ms=250,
        quality_score=0.88,
        suitable_for_complexity=["simple", "medium"]
    ),
}


class SmartRouter:
    """
    Intelligent model selection based on task complexity and optimization goals.
    """
    
    # Keywords indicating simple tasks
    SIMPLE_TASK_KEYWORDS = [
        'classify', 'classification', 'yes or no', 'true or false',
        'extract', 'extraction', 'parse', 'format', 'convert',
        'summarize in one word', 'label', 'tag', 'category'
    ]
    
    # Keywords indicating complex tasks
    COMPLEX_TASK_KEYWORDS = [
        'analyze', 'explain', 'reasoning', 'argue', 'debate',
        'creative', 'story', 'essay', 'detailed', 'comprehensive',
        'research', 'compare', 'evaluate', 'critique'
    ]
    
    @staticmethod
    def classify_complexity(messages: List[Dict[str, str]]) -> str:
        """
        Classify prompt complexity as 'simple', 'medium', or 'complex'.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            'simple', 'medium', or 'complex'
        """
        # Combine all message content
        full_prompt = " ".join([msg.get("content", "") for msg in messages])
        prompt_lower = full_prompt.lower()
        
        # Count tokens
        try:
            token_count = count_tokens(full_prompt)
        except:
            token_count = len(full_prompt.split())
        
        # Check for simple task keywords
        simple_matches = sum(1 for kw in SmartRouter.SIMPLE_TASK_KEYWORDS if kw in prompt_lower)
        complex_matches = sum(1 for kw in SmartRouter.COMPLEX_TASK_KEYWORDS if kw in prompt_lower)
        
        # Classification logic
        if token_count < 100 and simple_matches > 0:
            return 'simple'
        
        if token_count < 50 and complex_matches == 0:
            return 'simple'
        
        if token_count > 500 or complex_matches >= 2:
            return 'complex'
        
        if simple_matches > complex_matches:
            return 'simple'
        
        if complex_matches > simple_matches:
            return 'complex'
        
        # Default to medium
        return 'medium'
    
    @staticmethod
    def select_model(
        complexity: str,
        optimize_for: str = 'cost',
        max_latency_ms: Optional[int] = None,
        available_models: Optional[List[str]] = None,
        available_providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Select optimal model based on complexity and constraints.
        
        Args:
            complexity: 'simple', 'medium', or 'complex'
            optimize_for: 'cost', 'latency', or 'quality'
            max_latency_ms: Maximum acceptable latency (optional constraint)
            available_models: List of available model names (optional filter)
            available_providers: List of available providers (optional filter)
            
        Returns:
            Dict with selected model details and alternatives
        """
        # Filter models by suitability
        suitable_models = {
            name: model for name, model in MODEL_CHARACTERISTICS.items()
            if complexity in model.suitable_for_complexity
        }
        
        # Apply provider filter
        if available_providers:
            suitable_models = {
                name: model for name, model in suitable_models.items()
                if model.provider in available_providers
            }
        
        # Apply model name filter
        if available_models:
            suitable_models = {
                name: model for name, model in suitable_models.items()
                if name in available_models
            }
        
        # Apply latency constraint
        if max_latency_ms:
            suitable_models = {
                name: model for name, model in suitable_models.items()
                if model.estimated_latency_ms <= max_latency_ms
            }
        
        if not suitable_models:
            # No suitable models found, return default
            return {
                "selected_model": "gpt-3.5-turbo",
                "selected_provider": "openai",
                "reason": "default_fallback",
                "estimated_cost": 0.0005,
                "estimated_latency_ms": 600,
                "alternatives": []
            }
        
        # Score models based on optimization goal
        scored_models = []
        for name, model in suitable_models.items():
            if optimize_for == 'cost':
                # Lower cost = higher score
                score = 1 / float(model.estimated_cost) if model.estimated_cost > 0 else 1000
            elif optimize_for == 'latency':
                # Lower latency = higher score
                score = 1 / model.estimated_latency_ms if model.estimated_latency_ms > 0 else 1000
            elif optimize_for == 'quality':
                # Higher quality = higher score
                score = model.quality_score
            else:
                # Balanced score (cost + latency + quality)
                score = (
                    (1 / float(model.estimated_cost) * 0.4) +
                    (1 / model.estimated_latency_ms * 0.3) +
                    (model.quality_score * 0.3)
                )
            
            scored_models.append((name, model, score))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[2], reverse=True)
        
        # Select best model
        selected_name, selected_model, _ = scored_models[0]
        
        # Build alternatives list
        alternatives = []
        for name, model, score in scored_models[1:4]:  # Top 3 alternatives
            reason = []
            if model.estimated_cost > selected_model.estimated_cost:
                cost_diff = float(model.estimated_cost - selected_model.estimated_cost)
                reason.append(f"{cost_diff / float(selected_model.estimated_cost) * 100:.0f}% more expensive")
            if model.estimated_latency_ms > selected_model.estimated_latency_ms:
                latency_diff = model.estimated_latency_ms - selected_model.estimated_latency_ms
                reason.append(f"{latency_diff}ms slower")
            if model.quality_score < selected_model.quality_score:
                quality_diff = (selected_model.quality_score - model.quality_score) * 100
                reason.append(f"{quality_diff:.0f}% lower quality")
            
            alternatives.append({
                "model": name,
                "provider": model.provider,
                "estimated_cost": float(model.estimated_cost),
                "estimated_latency_ms": model.estimated_latency_ms,
                "quality_score": model.quality_score,
                "reason_not_selected": " | ".join(reason) if reason else "lower overall score"
            })
        
        # Calculate savings vs most expensive suitable model
        most_expensive = max(suitable_models.values(), key=lambda m: m.estimated_cost)
        estimated_savings = float(most_expensive.estimated_cost - selected_model.estimated_cost)
        
        return {
            "selected_model": selected_name,
            "selected_provider": selected_model.provider,
            "reason": f"{optimize_for}_optimized",
            "estimated_cost": float(selected_model.estimated_cost),
            "estimated_latency_ms": selected_model.estimated_latency_ms,
            "quality_score": selected_model.quality_score,
            "complexity": complexity,
            "alternatives": alternatives,
            "estimated_savings_usd": estimated_savings if estimated_savings > 0 else 0
        }
    
    @staticmethod
    def explain_selection(routing_decision: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of model selection.
        
        Args:
            routing_decision: Dict returned by select_model()
            
        Returns:
            Explanation string
        """
        model = routing_decision["selected_model"]
        reason = routing_decision["reason"]
        complexity = routing_decision.get("complexity", "unknown")
        cost = routing_decision["estimated_cost"]
        latency = routing_decision["estimated_latency_ms"]
        
        explanations = {
            "cost_optimized": f"Selected {model} for {complexity} task - most cost-effective at ${cost:.6f}/1K tokens",
            "latency_optimized": f"Selected {model} for {complexity} task - fastest at ~{latency}ms",
            "quality_optimized": f"Selected {model} for {complexity} task - highest quality",
            "default_fallback": f"Using default {model} - no suitable models found for constraints"
        }
        
        return explanations.get(reason, f"Selected {model} for {complexity} task")
