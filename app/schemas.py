"""
Pydantic schemas for Cognitude LLM Monitoring Platform API.
These models handle request/response validation and generate OpenAPI documentation.
"""
from pydantic import BaseModel, Field, validator
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

    @validator("messages")
    def validate_message_size(cls, v):
        """Validate the total size of the message content."""
        from app.config import get_settings
        settings = get_settings()
        
        total_length = sum(len(msg.content) for msg in v)
        max_size = settings.MAX_TOTAL_MESSAGE_SIZE_KB * 1024  # Convert KB to bytes
        
        if total_length > max_size:
            raise ValueError(f"Total message content exceeds the maximum allowed size of {settings.MAX_TOTAL_MESSAGE_SIZE_KB}KB.")
        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        """Validate max_tokens doesn't exceed configured limit."""
        from app.config import get_settings
        settings = get_settings()
        
        if v is not None and v > settings.MAX_TOKENS_PER_REQUEST:
            raise ValueError(f"max_tokens cannot exceed {settings.MAX_TOKENS_PER_REQUEST}")
        return v


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
    provider: str = Field(..., min_length=2, max_length=50, description="Provider name")
    api_key: str = Field(..., min_length=10, max_length=500, description="API key for the provider")
    enabled: bool = True
    priority: int = Field(0, ge=0, le=100, description="Routing priority (0-100)")
    
    @validator('provider')
    def validate_provider_name(cls, v):
        """Validate provider name against allowed providers."""
        allowed_providers = ['openai', 'anthropic', 'cohere', 'google', 'azure', 'huggingface']
        if v.lower() not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v.lower()
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format."""
        if not v.strip():
            raise ValueError('API key cannot be empty')
        # Check for common API key patterns (basic validation)
        if len(v) < 10:
            raise ValueError('API key must be at least 10 characters')
        return v.strip()


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

# ============================================================================
# Schema Validation Schemas
# ============================================================================

class SchemaValidationLogBase(BaseModel):
    """Base schema for schema validation logs."""
    organization_id: int
    llm_request_id: Optional[int] = None
    provided_schema: Dict[str, Any]
    llm_response: Dict[str, Any]
    is_valid: bool
    validation_error: Optional[str] = None
    retry_count: int = 0
    final_response: Optional[str] = None
    was_successful: bool

class SchemaValidationLogCreate(SchemaValidationLogBase):
    """Schema for creating a new schema validation log."""
    pass

class SchemaValidationLog(SchemaValidationLogBase):
    """Schema for schema validation log response."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class SchemaCreate(BaseModel):
    """Schema for creating a new schema."""
    name: str
    schema_data: Dict[str, Any]


class ResponseMessage(BaseModel):
    """Standard message response."""
    message: str


# ============================================================================
# Dashboard Schemas
# ============================================================================

class SchemaStat(BaseModel):
    """Statistics for a single schema."""
    schema_name: str
    total_attempts: int
    failure_rate: float
    avg_retries: float

    class Config:
        from_attributes = True


class Schema(BaseModel):
    """Schema for schema response."""
    id: int
    name: str
    schema_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class TopSchemaStatsResponse(BaseModel):
    """Response model for top 5 most used schemas."""
    top_5_most_used: List[SchemaStat]

class DashboardSummaryStats(BaseModel):
    """Summary statistics for the dashboard."""
    total_cost_savings: float
    autopilot_decisions_today: int
    validation_failures_last_24h: int
    active_schemas: int


# ============================================================================
# Model & Feature Schemas
# ============================================================================

class ModelFeatureBase(BaseModel):
    feature_name: str
    feature_type: str  # 'numeric' or 'categorical'
    order: int

class ModelFeatureCreate(ModelFeatureBase):
    pass

class ModelFeature(ModelFeatureBase):
    id: int
    model_id: int

    class Config:
        from_attributes = True


class ModelBase(BaseModel):
    name: str
    version: str
    description: Optional[str] = None

class ModelCreate(ModelBase):
    features: List[ModelFeatureCreate]

class Model(ModelBase):
    id: int
    organization_id: int
    features: List[ModelFeature] = []

    class Config:
        from_attributes = True