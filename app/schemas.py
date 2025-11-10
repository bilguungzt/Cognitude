"""
Pydantic schemas for API request/response models.
These models are used to generate OpenAPI/Swagger documentation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


# ============================================================================
# Proxy Endpoint Schemas
# ============================================================================

class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: str = Field(..., description="The role of the message author (system, user, or assistant)")
    content: str = Field(..., description="The content of the message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is the capital of France?"
            }
        }


class ChatCompletionRequest(BaseModel):
    """Request body for chat completions."""
    model: str = Field(..., description="ID of the model to use (e.g., gpt-4, gpt-3.5-turbo)")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(1.0, description="Sampling temperature (0-2)", ge=0, le=2)
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.7
            }
        }


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used (prompt + completion)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int = Field(..., description="Choice index")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: str = Field(..., description="Why the completion finished (stop, length, etc.)")


class ChatCompletionResponse(BaseModel):
    """Response from chat completions endpoint."""
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field(..., description="Object type (chat.completion)")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    usage: UsageInfo = Field(..., description="Token usage statistics")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1699492800,
                "model": "gpt-3.5-turbo",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                },
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello! How can I help you today?"
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
        }


# ============================================================================
# Analytics Endpoint Schemas
# ============================================================================

class DailyUsage(BaseModel):
    """Daily usage statistics."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    requests: int = Field(..., description="Number of API requests made on this day")
    cost: float = Field(..., description="Total cost in USD for this day")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-09",
                "requests": 1250,
                "cost": 12.30
            }
        }


class AnalyticsResponse(BaseModel):
    """Response from analytics usage endpoint."""
    total_requests: int = Field(..., description="Total number of API requests in the time period")
    total_cost: float = Field(..., description="Total cost in USD for all requests")
    average_latency: float = Field(..., description="Average response latency in milliseconds")
    usage_by_day: List[DailyUsage] = Field(..., description="Daily breakdown of usage and costs")
    
    class Config:
        json_schema_extra = {
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
