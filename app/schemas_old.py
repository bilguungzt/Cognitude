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


# ============================================================================
# Organization Schemas
# ============================================================================

class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    name: str = Field(..., description="Organization name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Organization"
            }
        }


class Organization(BaseModel):
    """Schema for organization."""
    id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "My Organization"
            }
        }


class OrganizationWithAPIKey(BaseModel):
    """Schema for organization response with API key."""
    id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    api_key: str = Field(..., description="API key for authentication")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "My Organization",
                "api_key": "abc123def456..."
            }
        }


# ============================================================================
# Model Schemas
# ============================================================================

class ModelFeatureCreate(BaseModel):
    """Schema for creating a model feature."""
    feature_name: str = Field(..., description="Name of the feature")
    feature_type: str = Field(..., description="Type of the feature (numeric, categorical, etc.)")
    order: int = Field(..., description="Order of the feature")
    baseline_stats: Optional[Dict[str, Any]] = Field(None, description="Baseline statistics for the feature")


class ModelFeature(BaseModel):
    """Schema for model feature."""
    id: int = Field(..., description="Feature ID")
    feature_name: str = Field(..., description="Name of the feature")
    feature_type: str = Field(..., description="Type of the feature")
    order: int = Field(..., description="Order of the feature")
    baseline_stats: Optional[Dict[str, Any]] = Field(None, description="Baseline statistics")
    
    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    """Schema for creating a new model."""
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    description: Optional[str] = Field(None, description="Model description")
    model_type: Optional[str] = Field(None, description="Type of model")
    baseline_mean: Optional[float] = Field(None, description="Baseline mean for predictions")
    baseline_std: Optional[float] = Field(None, description="Baseline standard deviation for predictions")
    features: List[ModelFeatureCreate] = Field(default_factory=list, description="List of model features")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "fraud-detection-model",
                "version": "1.0.0",
                "description": "Model for detecting fraudulent transactions",
                "model_type": "classification",
                "features": [
                    {
                        "feature_name": "transaction_amount",
                        "feature_type": "numeric",
                        "order": 0
                    }
                ]
            }
        }


class Model(BaseModel):
    """Schema for model."""
    id: int = Field(..., description="Model ID")
    organization_id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    description: Optional[str] = Field(None, description="Model description")
    model_type: Optional[str] = Field(None, description="Type of model")
    baseline_mean: Optional[float] = Field(None, description="Baseline mean")
    baseline_std: Optional[float] = Field(None, description="Baseline standard deviation")
    features: List[ModelFeature] = Field(default_factory=list, description="Model features")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "organization_id": 1,
                "name": "fraud-detection-model",
                "version": "1.0.0",
                "description": "Model for detecting fraudulent transactions",
                "model_type": "classification",
                "features": []
            }
        }


# ============================================================================
# Prediction Schemas
# ============================================================================

class PredictionData(BaseModel):
    """Schema for prediction data."""
    timestamp: str = Field(..., description="Timestamp of the prediction")
    prediction_value: float = Field(..., description="Predicted value")
    actual_value: Optional[float] = Field(None, description="Actual value (if known)")
    features: Dict[str, Any] = Field(..., description="Feature values used for the prediction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-09T12:00:00Z",
                "prediction_value": 0.85,
                "actual_value": 1.0,
                "features": {
                    "transaction_amount": 150.50,
                    "account_age": 365
                }
            }
        }


class Prediction(BaseModel):
    """Schema for prediction."""
    id: int = Field(..., description="Prediction ID")
    time: str = Field(..., description="Timestamp")
    model_id: int = Field(..., description="Model ID")
    prediction_value: float = Field(..., description="Predicted value")
    actual_value: Optional[float] = Field(None, description="Actual value")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    features: Dict[str, Any] = Field(..., description="Feature values")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "time": "2025-11-09T12:00:00Z",
                "model_id": 1,
                "prediction_value": 0.85,
                "actual_value": 1.0,
                "latency_ms": 15.3,
                "features": {
                    "transaction_amount": 150.50
                }
            }
        }
