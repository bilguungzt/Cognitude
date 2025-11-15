"""
Token counting utilities for different LLM models.
Uses tiktoken for OpenAI models, estimates for others.
"""
from typing import List, Dict, Any

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in text for a specific model.
    
    Args:
        text: Input text to count
        model: Model name for encoder selection
        
    Returns:
        Number of tokens
    """
    if not TIKTOKEN_AVAILABLE:
        # Fallback: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4
    
    try:
        # Get encoding for model
        if model.startswith("gpt-4") or model.startswith("gpt-4o"):
            encoding = tiktoken.encoding_for_model("gpt-4")
        elif model.startswith("gpt-3.5"):
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        elif model.startswith("claude"):
            # Claude uses similar tokenization to GPT
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            # Use cl100k_base as default
            encoding = tiktoken.get_encoding("cl100k_base")
        
        return len(encoding.encode(text))
    
    except Exception:
        # Fallback on error
        return len(text) // 4


def count_messages_tokens(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in a list of chat messages.
    Includes overhead for message formatting.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name for encoder selection
        
    Returns:
        Total number of tokens including formatting overhead
        
    Note:
        Based on OpenAI's token counting guide:
        https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    """
    if not TIKTOKEN_AVAILABLE:
        # Fallback estimate
        total_chars = sum(len(msg.get("content", "")) + len(msg.get("role", "")) for msg in messages)
        return total_chars // 4 + len(messages) * 4  # Add overhead per message
    
    try:
        # Get encoding
        if model.startswith("gpt-4") or model.startswith("gpt-4o"):
            encoding = tiktoken.encoding_for_model("gpt-4")
            tokens_per_message = 3
            tokens_per_name = 1
        elif model.startswith("gpt-3.5"):
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        else:
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens_per_message = 3
            tokens_per_name = 1
        
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
        
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        
        return num_tokens
    
    except Exception:
        # Fallback on error
        total_chars = sum(len(msg.get("content", "")) + len(msg.get("role", "")) for msg in messages)
        return total_chars // 4 + len(messages) * 4


def estimate_completion_tokens(prompt_tokens: int, max_tokens: int = None) -> int:
    """
    Estimate completion tokens based on prompt length.
    
    Args:
        prompt_tokens: Number of tokens in prompt
        max_tokens: Maximum tokens requested (if specified)
        
    Returns:
        Estimated completion tokens
        
    Note:
        Uses heuristic: typical completion is 30-50% of prompt length
        or max_tokens if specified and smaller
    """
    if max_tokens:
        estimated = min(int(prompt_tokens * 0.4), max_tokens)
    else:
        estimated = int(prompt_tokens * 0.4)
    
    # Minimum 10 tokens for very short prompts
    return max(estimated, 10)
