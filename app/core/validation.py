"""
Input validation and sanitization utilities for security.
"""
import re
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status

# SQL injection patterns to detect
SQL_INJECTION_PATTERNS = [
    r"(%27)|(')|(--)|(%23)|(#)",
    r"((%3D)|(=))[^\n]*((%27)|(')|(--)|(%3B)|(;))",
    r"\w*((%27)|('))((%6F)|o|(%4F))((%72)|r|(%52))",
    r"((%27)|('))union",
    r"((%27)|('))insert",
    r"((%27)|('))update",
    r"((%27)|('))delete",
    r"((%27)|('))drop",
    r"((%27)|('))create",
    r"((%27)|('))exec",
    r"((%27)|('))execute",
    r"((%27)|('))script",
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
]

# XSS patterns to detect
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>.*?</iframe>",
    r"<object[^>]*>.*?</object>",
    r"<embed[^>]*>.*?</embed>",
    r"<img[^>]*on\w+\s*=",
]

# Compiled regex patterns for performance
SQL_INJECTION_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_INJECTION_PATTERNS]
XSS_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in XSS_PATTERNS]

# Maximum allowed sizes
MAX_STRING_LENGTH = 10000
MAX_JSON_DEPTH = 10
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB


class ValidationError(HTTPException):
    """Custom validation error with security context."""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Validation failed", "message": detail, "field": field}
        )


def sanitize_string(input_str: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """
    Sanitize string input by removing control characters and limiting length.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(input_str, str):
        raise ValidationError("Input must be a string")
    
    if len(input_str) > max_length:
        raise ValidationError(f"Input exceeds maximum length of {max_length} characters")
    
    # Remove control characters except whitespace
    sanitized = "".join(char for char in input_str if char.isprintable() or char in " \t\n\r")
    
    return sanitized


def detect_sql_injection(input_str: str) -> bool:
    """
    Detect potential SQL injection attempts in input string.
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if SQL injection detected, False otherwise
    """
    if not isinstance(input_str, str):
        return False
    
    for pattern in SQL_INJECTION_REGEX:
        if pattern.search(input_str):
            return True
    return False


def detect_xss(input_str: str) -> bool:
    """
    Detect potential XSS attempts in input string.
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if XSS detected, False otherwise
    """
    if not isinstance(input_str, str):
        return False
    
    for pattern in XSS_REGEX:
        if pattern.search(input_str):
            return True
    return False


def validate_and_sanitize_dict(
    data: Dict[str, Any], 
    max_depth: int = MAX_JSON_DEPTH,
    current_depth: int = 0
) -> Dict[str, Any]:
    """
    Recursively validate and sanitize a dictionary.
    
    Args:
        data: Dictionary to validate
        max_depth: Maximum allowed nesting depth
        current_depth: Current nesting depth
        
    Returns:
        Sanitized dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if current_depth > max_depth:
        raise ValidationError(f"JSON nesting exceeds maximum depth of {max_depth}")
    
    if not isinstance(data, dict):
        raise ValidationError("Input must be a dictionary")
    
    sanitized = {}
    
    for key, value in data.items():
        # Validate key
        if not isinstance(key, str):
            raise ValidationError("Dictionary keys must be strings")
        
        sanitized_key = sanitize_string(key, max_length=255)
        
        # Validate and sanitize value
        if isinstance(value, str):
            # Check for SQL injection and XSS
            if detect_sql_injection(value):
                raise ValidationError("Potential SQL injection detected", field=key)
            if detect_xss(value):
                raise ValidationError("Potential XSS detected", field=key)
            
            sanitized_value = sanitize_string(value)
            
        elif isinstance(value, dict):
            sanitized_value = validate_and_sanitize_dict(value, max_depth, current_depth + 1)
            
        elif isinstance(value, list):
            sanitized_value = validate_and_sanitize_list(value, max_depth, current_depth + 1)
            
        elif isinstance(value, (int, float, bool, type(None))):
            sanitized_value = value
            
        else:
            raise ValidationError(f"Unsupported data type for field: {key}")
        
        sanitized[sanitized_key] = sanitized_value
    
    return sanitized


def validate_and_sanitize_list(
    data: List[Any], 
    max_depth: int = MAX_JSON_DEPTH,
    current_depth: int = 0
) -> List[Any]:
    """
    Recursively validate and sanitize a list.
    
    Args:
        data: List to validate
        max_depth: Maximum allowed nesting depth
        current_depth: Current nesting depth
        
    Returns:
        Sanitized list
        
    Raises:
        ValidationError: If validation fails
    """
    if current_depth > max_depth:
        raise ValidationError(f"JSON nesting exceeds maximum depth of {max_depth}")
    
    if not isinstance(data, list):
        raise ValidationError("Input must be a list")
    
    sanitized = []
    
    for item in data:
        if isinstance(item, str):
            # Check for SQL injection and XSS
            if detect_sql_injection(item):
                raise ValidationError("Potential SQL injection detected in list item")
            if detect_xss(item):
                raise ValidationError("Potential XSS detected in list item")
            
            sanitized_item = sanitize_string(item)
            
        elif isinstance(item, dict):
            sanitized_item = validate_and_sanitize_dict(item, max_depth, current_depth + 1)
            
        elif isinstance(item, list):
            sanitized_item = validate_and_sanitize_list(item, max_depth, current_depth + 1)
            
        elif isinstance(item, (int, float, bool, type(None))):
            sanitized_item = item
            
        else:
            raise ValidationError("Unsupported data type in list")
        
        sanitized.append(sanitized_item)
    
    return sanitized


def validate_request_size(request_body: bytes) -> None:
    """
    Validate that request body size is within limits.
    
    Args:
        request_body: Raw request body as bytes
        
    Raises:
        ValidationError: If request size exceeds limit
    """
    if len(request_body) > MAX_REQUEST_SIZE:
        raise ValidationError(
            f"Request size exceeds maximum allowed limit of {MAX_REQUEST_SIZE} bytes"
        )


def validate_api_key(api_key: str) -> str:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        Sanitized API key
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValidationError("API key is required")
    
    sanitized = sanitize_string(api_key, max_length=255)
    
    # API keys should be alphanumeric with limited special characters
    if not re.match(r'^[a-zA-Z0-9-_]+$', sanitized):
        raise ValidationError("Invalid API key format")
    
    return sanitized


def validate_organization_name(name: str) -> str:
    """
    Validate organization name.
    
    Args:
        name: Organization name to validate
        
    Returns:
        Sanitized organization name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Organization name is required")
    
    sanitized = sanitize_string(name, max_length=100)
    
    # Organization names should be reasonable
    if len(sanitized) < 2:
        raise ValidationError("Organization name must be at least 2 characters")
    
    if len(sanitized) > 100:
        raise ValidationError("Organization name must not exceed 100 characters")
    
    return sanitized


def validate_model_name(model: str) -> str:
    """
    Validate model name.
    
    Args:
        model: Model name to validate
        
    Returns:
        Sanitized model name
        
    Raises:
        ValidationError: If model name is invalid
    """
    if not model or not isinstance(model, str):
        raise ValidationError("Model name is required")
    
    sanitized = sanitize_string(model, max_length=100)
    
    # Model names typically contain letters, numbers, hyphens, dots, and forward slashes
    if not re.match(r'^[a-zA-Z0-9-._/]+$', sanitized):
        raise ValidationError("Invalid model name format")
    
    return sanitized


def validate_provider_name(provider: str) -> str:
    """
    Validate provider name.
    
    Args:
        provider: Provider name to validate
        
    Returns:
        Sanitized provider name
        
    Raises:
        ValidationError: If provider name is invalid
    """
    if not provider or not isinstance(provider, str):
        raise ValidationError("Provider name is required")
    
    sanitized = sanitize_string(provider, max_length=50)
    
    # Provider names should be simple
    if not re.match(r'^[a-zA-Z0-9-_]+$', sanitized):
        raise ValidationError("Invalid provider name format")
    
    return sanitized