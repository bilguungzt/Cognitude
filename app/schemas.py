"""
Pydantic schemas for Cognitude LLM Monitoring Platform API.
These models handle request/response validation and generate OpenAPI documentation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Organization Schemas
# ============================================================================

class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    name: str = Field(..., description="Organization name", min_length=3, max_length=100)
    
    class Config:
        json_schema_extra = {"example": {"name": "Acme Corp"}}


class Organization(BaseModel):
    """Schema for organization response."""
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationWithAPIKey(BaseModel):
    """Schema for organization response including API key."""
    id: int
    name: str
    api_key: str
    created_at: datetime


# ============================================================================
# LLM Request/Response Schemas (OpenAI Compatible)
# ============================================================================

class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: str
    content: str


# Alias for backwards compatibility
Message = ChatMessage


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stream: Optional[bool] = False


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    usage: UsageInfo
    choices: List[ChatCompletionChoice]
    cached: Optional[bool] = False
    provider: Optional[str] = None
    cost_usd: Optional[float] = None


# ============================================================================
# Analytics Schemas
# ============================================================================

class DailyUsage(BaseModel):
    """Daily usage statistics."""
    date: str
    requests: int
    cost: float
    cached_requests: int = 0
    cache_savings: float = 0.0


class ProviderUsage(BaseModel):
    """Usage breakdown by provider."""
    provider: str
    requests: int
    cost: float
    avg_latency_ms: float


class ModelUsage(BaseModel):
    """Usage breakdown by model."""
    model: str
    requests: int
    cost: float
    total_tokens: int


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response."""
    total_requests: int
    total_cost: float
    average_latency: float
    cache_hit_rate: float
    total_tokens: int
    usage_by_day: List[DailyUsage]
    usage_by_provider: List[ProviderUsage]
    usage_by_model: List[ModelUsage]


# ============================================================================
# Provider Configuration Schemas
# ============================================================================

class ProviderConfigCreate(BaseModel):
    """Schema for adding a provider configuration."""
    provider: str
    api_key: str
    enabled: bool = True
    priority: int = 0


class ProviderConfig(BaseModel):
    """Schema for provider configuration response."""
    id: int
    provider: str
    enabled: bool
    priority: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProviderConfigUpdate(BaseModel):
    """Schema for updating provider configuration."""
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    api_key: Optional[str] = None


# ============================================================================
# Cache Schemas
# ============================================================================

class CacheStats(BaseModel):
    """Cache statistics."""
    total_entries: int
    total_hits: int
    hit_rate: float
    estimated_savings_usd: float


class CacheClearRequest(BaseModel):
    """Request to clear cache entries."""
    model: Optional[str] = None
    older_than_hours: Optional[int] = None


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
