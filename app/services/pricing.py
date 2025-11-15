"""
Pricing calculations for different LLM providers and models.
"""
from decimal import Decimal
from typing import Dict

# Pricing per 1M tokens (input/output in USD)
PRICING: Dict[str, Dict[str, Decimal]] = {
    # OpenAI
    "gpt-4": {"input": Decimal("30.00"), "output": Decimal("60.00")},
    "gpt-4o": {"input": Decimal("12.00"), "output": Decimal("35.00")},
    "gpt-4o-mini": {"input": Decimal("1.00"), "output": Decimal("2.50")},
    "gpt-4-0125-preview": {"input": Decimal("10.00"), "output": Decimal("30.00")},
    "gpt-4-turbo-preview": {"input": Decimal("10.00"), "output": Decimal("30.00")},
    
    # Anthropic Claude
    "claude-3-opus-20240229": {"input": Decimal("15.00"), "output": Decimal("75.00")},
    "claude-3-sonnet-20240229": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-haiku-20240307": {"input": Decimal("0.25"), "output": Decimal("1.25")},
    "claude-3-opus": {"input": Decimal("15.00"), "output": Decimal("75.00")},
    "claude-3-sonnet": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-haiku": {"input": Decimal("0.25"), "output": Decimal("1.25")},
    
    # Hugging Face / community models (Llama 3 family examples)
    "hf/llama-3-70b": {"input": Decimal("0.70"), "output": Decimal("0.80")},
    "hf/llama-3-13b": {"input": Decimal("0.10"), "output": Decimal("0.20")},
    
    # Groq
    "llama3-70b-8192": {"input": Decimal("0.70"), "output": Decimal("0.80")},
    "llama3-8b-8192": {"input": Decimal("0.05"), "output": Decimal("0.10")},
    "mixtral-8x7b-32768": {"input": Decimal("0.27"), "output": Decimal("0.27")},
    "gemma-7b-it": {"input": Decimal("0.07"), "output": Decimal("0.07")},
    
    # Google Gemini
    "gemini-2.0-flash-exp": {"input": Decimal("0.00"), "output": Decimal("0.00")},  # Free during preview
    "gemini-2.5-flash-lite": {"input": Decimal("0.00"), "output": Decimal("0.00")},  # Free during preview
    "gemini-pro": {"input": Decimal("0.50"), "output": Decimal("1.50")},
    "gemini-flash": {"input": Decimal("0.075"), "output": Decimal("0.30")},
    "gemini-1.5-pro": {"input": Decimal("3.50"), "output": Decimal("10.50")},
    "gemini-1.5-flash": {"input": Decimal("0.075"), "output": Decimal("0.30")},
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
