"""
Pricing calculations for different LLM providers and models.
"""
from decimal import Decimal
from typing import Dict

# Pricing per 1M tokens (input/output in USD)
PRICING: Dict[str, Dict[str, Decimal]] = {
    # OpenAI - Latest Models (2025)
    "gpt-5-nano": {"input": Decimal("0.10"), "output": Decimal("0.40")},
    "gpt-5.1": {"input": Decimal("20.00"), "output": Decimal("80.00")},
    "gpt-5.1-instant": {"input": Decimal("18.00"), "output": Decimal("72.00")},
    "gpt-5.1-thinking": {"input": Decimal("25.00"), "output": Decimal("100.00")},
    "gpt-5.1-codex": {"input": Decimal("25.00"), "output": Decimal("100.00")},
    "gpt-5": {"input": Decimal("18.00"), "output": Decimal("70.00")},
    "gpt-4.5": {"input": Decimal("12.00"), "output": Decimal("40.00")},
    "gpt-4.1": {"input": Decimal("11.00"), "output": Decimal("35.00")},
    "o4-mini": {"input": Decimal("4.00"), "output": Decimal("16.00")},
    "o1-preview": {"input": Decimal("15.00"), "output": Decimal("60.00")},
    "o1-mini": {"input": Decimal("3.00"), "output": Decimal("12.00")},
    "gpt-4-turbo": {"input": Decimal("10.00"), "output": Decimal("30.00")},
    "gpt-4-turbo-preview": {"input": Decimal("10.00"), "output": Decimal("30.00")},
    "gpt-4o": {"input": Decimal("2.50"), "output": Decimal("10.00")},
    "gpt-4o-mini": {"input": Decimal("0.15"), "output": Decimal("0.60")},
    "gpt-4": {"input": Decimal("30.00"), "output": Decimal("60.00")},
    "gpt-4-0125-preview": {"input": Decimal("10.00"), "output": Decimal("30.00")},
    
    # Anthropic Claude - Latest Models (2025)
    "claude-sonnet-4.5": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-haiku-4.5": {"input": Decimal("1.00"), "output": Decimal("5.00")},
    "claude-opus-4.1": {"input": Decimal("15.00"), "output": Decimal("75.00")},
    # Existing Anthropic Models
    "claude-3-5-sonnet-20241022": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-5-sonnet-20240620": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-opus-20240229": {"input": Decimal("15.00"), "output": Decimal("75.00")},
    "claude-3-sonnet-20240229": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-haiku-20240307": {"input": Decimal("0.25"), "output": Decimal("1.25")},
    "claude-3-opus": {"input": Decimal("15.00"), "output": Decimal("75.00")},
    "claude-3-sonnet": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-haiku": {"input": Decimal("0.25"), "output": Decimal("1.25")},
    
    # Google Gemini - Latest Models (2025)
    "gemini-2.5-pro": {"input": Decimal("2.50"), "output": Decimal("10.00")},
    "gemini-2.5-flash": {"input": Decimal("0.15"), "output": Decimal("0.60")},
    "gemini-2.5-flash-lite": {"input": Decimal("0.05"), "output": Decimal("0.20")},
    "gemini-2.5-pro-deep-think": {"input": Decimal("3.50"), "output": Decimal("14.00")},
    "gemini-2.0-flash-exp": {"input": Decimal("0.00"), "output": Decimal("0.00")},  # Free during preview
    "gemini-1.5-pro": {"input": Decimal("1.25"), "output": Decimal("5.00")},
    "gemini-1.5-flash": {"input": Decimal("0.075"), "output": Decimal("0.30")},
    "gemini-pro": {"input": Decimal("0.50"), "output": Decimal("1.50")},
    "gemini-flash": {"input": Decimal("0.075"), "output": Decimal("0.30")},
    
    # Groq - Latest Models (2025)
    "groq-4": {"input": Decimal("2.50"), "output": Decimal("12.00")},
    "grok-3-mini": {"input": Decimal("0.20"), "output": Decimal("0.80")},
    "grok-code-fast-1": {"input": Decimal("0.80"), "output": Decimal("3.20")},
    "grok-4-fast": {"input": Decimal("2.00"), "output": Decimal("8.00")},
    "grok-4-heavy": {"input": Decimal("2.80"), "output": Decimal("11.00")},
    "fast-1": {"input": Decimal("2.00"), "output": Decimal("10.00")},
    # Llama 4 (2025)
    "llama-4-scout": {"input": Decimal("0.80"), "output": Decimal("1.00")},
    "llama-4-maverick": {"input": Decimal("0.90"), "output": Decimal("1.20")},
    # Existing Groq Models
    "llama-3.3-70b-versatile": {"input": Decimal("0.59"), "output": Decimal("0.79")},
    "llama-3.1-70b-versatile": {"input": Decimal("0.59"), "output": Decimal("0.79")},
    "llama3-70b-8192": {"input": Decimal("0.70"), "output": Decimal("0.80")},
    "llama3-8b-8192": {"input": Decimal("0.05"), "output": Decimal("0.10")},
    "mixtral-8x7b-32768": {"input": Decimal("0.24"), "output": Decimal("0.24")},
    "gemma-7b-it": {"input": Decimal("0.07"), "output": Decimal("0.07")},
}

# Default pricing for unknown models
DEFAULT_PRICING = {"input": Decimal("1.00"), "output": Decimal("2.00")}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    """
    Calculate cost for an LLM request based on token usage.
    
    Args:
        model: Model name/identifier
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        
    Returns:
        Total cost in USD as Decimal
    """
    try:
        prompt_tokens = int(prompt_tokens)
        completion_tokens = int(completion_tokens)
    except (ValueError, TypeError):
        prompt_tokens = 0
        completion_tokens = 0
        
    pricing = PRICING.get(model, DEFAULT_PRICING)
    
    # Calculate costs (pricing is per 1M tokens)
    input_cost = (Decimal(prompt_tokens) / Decimal("1000000")) * pricing["input"]
    output_cost = (Decimal(completion_tokens) / Decimal("1000000")) * pricing["output"]
    
    total_cost = input_cost + output_cost
    
    # Round to 6 decimal places (sub-cent precision)
    return total_cost.quantize(Decimal("0.000001"))
    """
    Calculate cost for an LLM request based on token usage.
    
    Args:
        model: Model name/identifier
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        
    Returns:
        Total cost in USD as Decimal
        
    Example:
        >>> calculate_cost("gpt-3.5-turbo", 100, 50)
        Decimal('0.000125')  # $0.000125
    """
    pricing = PRICING.get(model, DEFAULT_PRICING)
    
    # Calculate costs (pricing is per 1M tokens)
    input_cost = (Decimal(str(prompt_tokens)) / Decimal("1000000")) * pricing["input"]
    output_cost = (Decimal(str(completion_tokens)) / Decimal("1000000")) * pricing["output"]
    
    total_cost = input_cost + output_cost
    
    # Round to 6 decimal places (sub-cent precision)
    return total_cost.quantize(Decimal("0.000001"))


def get_model_pricing(model: str) -> Dict[str, Decimal]:
    """
    Get pricing information for a specific model.
    
    Args:
        model: Model name/identifier
        
    Returns:
        Dict with 'input' and 'output' pricing per 1M tokens
    """
    return PRICING.get(model, DEFAULT_PRICING)


def estimate_cost(model: str, estimated_tokens: int) -> Decimal:
    """
    Estimate cost for a request assuming typical input/output ratio.
    Uses 60/40 split (60% input, 40% output) as typical.
    
    Args:
        model: Model name/identifier
        estimated_tokens: Total estimated tokens
        
    Returns:
        Estimated cost in USD
    """
    input_tokens = int(estimated_tokens * 0.6)
    output_tokens = int(estimated_tokens * 0.4)
    
    return calculate_cost(model, input_tokens, output_tokens)
