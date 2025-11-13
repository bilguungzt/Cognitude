"""
SQLAlchemy ORM models for Cognitude LLM Monitoring Platform.

This module defines the database schema for:
- Multi-tenant organizations
- LLM request logging and analytics
- Response caching
- Multi-provider configurations
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Numeric, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from .database import Base
from passlib.context import CryptContext

# Setup bcrypt for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Organizations & Authentication
# ============================================================================

class Organization(Base):
    """Multi-tenant organization model."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    api_key_hash = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    llm_requests = relationship("LLMRequest", back_populates="organization", cascade="all, delete-orphan")
    provider_configs = relationship("ProviderConfig", back_populates="organization", cascade="all, delete-orphan")
    alert_channels = relationship("AlertChannel", back_populates="organization", cascade="all, delete-orphan")
    rate_limit_config = relationship("RateLimitConfig", back_populates="organization", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hashes an API key using bcrypt."""
        return pwd_context.hash(api_key)

    def verify_api_key(self, api_key: str) -> bool:
        """Verifies a plain-text API key against the stored hash.

        For local/dev convenience the database may contain plaintext API keys
        (not hashed). Detect common bcrypt hash prefixes and use bcrypt
        verification in that case; otherwise fall back to direct equality.
        """
        try:
            stored = getattr(self, 'api_key_hash', '') or ''
            # bcrypt hashes start with $2b$ or $2a$ etc. Use that to choose
            # verification strategy.
            if isinstance(stored, str) and stored.startswith("$2"):
                return pwd_context.verify(api_key, stored)
            # Fallback for dev: stored API key may be plaintext
            return api_key == stored
        except Exception:
            # On any unexpected error, be conservative and return False
            return False


# ============================================================================
# LLM Request Logging
# ============================================================================

class LLMRequest(Base):
    """Logs every LLM API request for analytics and monitoring."""
    __tablename__ = "llm_requests"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Request details
    model = Column(String(100), nullable=False, index=True)  # gpt-4, claude-3-opus, etc.
    provider = Column(String(50), nullable=False, index=True)  # openai, anthropic, mistral
    
    # Token tracking
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    
    # Cost tracking
    cost_usd = Column(Numeric(precision=10, scale=6), nullable=False)
    
    # Performance metrics
    latency_ms = Column(Integer, nullable=False)
    
    # Caching information
    cache_hit = Column(Boolean, server_default='false', nullable=False)
    cache_key = Column(String(64), nullable=True, index=True)
    
    # Request metadata
    endpoint = Column(String(100), nullable=True)  # /v1/chat/completions
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="llm_requests")

    def __repr__(self):
        return f"<LLMRequest(id={self.id}, model='{self.model}', provider='{self.provider}', cache_hit={self.cache_hit})>"


# ============================================================================
# LLM Response Cache
# ============================================================================

class LLMCache(Base):
    """Caches LLM responses to reduce costs and improve latency."""
    __tablename__ = "llm_cache"

    cache_key = Column(String(64), primary_key=True)
    prompt_hash = Column(String(64), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    response_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    hit_count = Column(Integer, server_default='0', nullable=False)
    ttl_hours = Column(Integer, server_default='24', nullable=False)

    def __repr__(self):
        return f"<LLMCache(cache_key='{self.cache_key}', model='{self.model}', hit_count={self.hit_count})>"


# ============================================================================
# Multi-Provider Configuration
# ============================================================================

class ProviderConfig(Base):
    """Stores API keys and configuration for multiple LLM providers per organization."""
    __tablename__ = "provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # openai, anthropic, mistral, groq
    api_key_encrypted = Column(Text, nullable=False)
    enabled = Column(Boolean, server_default='true', nullable=False)
    priority = Column(Integer, server_default='0', nullable=False)  # For routing/fallback
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="provider_configs")

    def __repr__(self):
        return f"<ProviderConfig(id={self.id}, provider='{self.provider}', enabled={self.enabled})>"

    def get_api_key(self) -> str:
        # TODO: Decrypt in production
        return str(self.api_key_encrypted)


# ============================================================================
# Alert Channels (kept from original - for future notifications)
# ============================================================================

class AlertChannel(Base):
    """Configuration for alert notifications (email, Slack, webhook)."""
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    channel_type = Column(String(50), nullable=False)  # email, slack, webhook
    configuration = Column(JSONB, nullable=False)  # Stores channel-specific config
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="alert_channels")

    def __repr__(self):
        return f"<AlertChannel(id={self.id}, type='{self.channel_type}', active={self.is_active})>"


class AlertConfig(Base):
    """Configuration for cost threshold alerts."""
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # daily_cost, weekly_cost, monthly_cost, spike
    threshold_usd = Column(Numeric(10, 2), nullable=False)  # Alert when cost exceeds this
    enabled = Column(Boolean, server_default='true', nullable=False)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AlertConfig(id={self.id}, type='{self.alert_type}', threshold=${self.threshold_usd})>"


class RateLimitConfig(Base):
    """Rate limiting configuration per organization."""
    __tablename__ = "rate_limit_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    requests_per_minute = Column(Integer, server_default='100', nullable=False)  # Default: 100 req/min
    requests_per_hour = Column(Integer, server_default='3000', nullable=False)  # Default: 3000 req/hour
    requests_per_day = Column(Integer, server_default='50000', nullable=False)  # Default: 50k req/day
    enabled = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="rate_limit_config")

    def __repr__(self):
        return f"<RateLimitConfig(org_id={self.organization_id}, minute={self.requests_per_minute}, hour={self.requests_per_hour})>"

# ============================================================================
# Autopilot Engine Logging
# ============================================================================

class AutopilotLog(Base):
    """Logs the decision-making process of the Autopilot routing engine."""
    __tablename__ = "autopilot_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    llm_request_id = Column(BigInteger, ForeignKey("llm_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Routing decision details
    original_model = Column(String(100), nullable=False, index=True)
    selected_model = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=True, index=True)
    routing_reason = Column(String(255), nullable=False)
    
    # Cost and performance metrics
    cost_usd = Column(Numeric(precision=10, scale=6), nullable=False)
    estimated_savings_usd = Column(Numeric(precision=10, scale=6), nullable=True)
    
    # Confidence and metadata
    confidence_score = Column(Float, nullable=True)
    is_cached_response = Column(Boolean, server_default='false', nullable=False)
    
    # New fields for debugging and analysis
    prompt_length = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization")
    llm_request = relationship("LLMRequest")
    validation_logs = relationship("ValidationLog", back_populates="autopilot_log", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AutopilotLog(id={self.id}, original='{self.original_model}', selected='{self.selected_model}')>"

# ============================================================================
# Response Validation Logging
# ============================================================================

class ValidationLog(Base):
    """Logs response validation failures and fix attempts."""
    __tablename__ = "validation_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    autopilot_log_id = Column(BigInteger, ForeignKey("autopilot_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    validation_type = Column(String(100), nullable=False, index=True) # e.g., 'invalid_json', 'empty_response'
    fix_attempted = Column(String(255), nullable=False) # e.g., 'retry_with_stricter_prompt'
    retry_count = Column(Integer, nullable=False)
    was_successful = Column(Boolean, nullable=False)

    # Relationship to AutopilotLog
    autopilot_log = relationship("AutopilotLog", back_populates="validation_logs")

    def __repr__(self):
        return f"<ValidationLog(id={self.id}, type='{self.validation_type}', success={self.was_successful})>"

class SchemaValidationLog(Base):
    """Logs the schema validation and enforcement process."""
    __tablename__ = "schema_validation_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    llm_request_id = Column(BigInteger, ForeignKey("llm_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    schema_id = Column(Integer, ForeignKey("schemas.id", ondelete="CASCADE"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Schema and validation details
    provided_schema = Column(JSONB, nullable=False)
    llm_response = Column(Text, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    validation_error = Column(Text, nullable=True)

    # Retry logic
    retry_count = Column(Integer, server_default='0', nullable=False)
    final_response = Column(Text, nullable=True)
    was_successful = Column(Boolean, nullable=False)

    # Relationships
    organization = relationship("Organization")
    llm_request = relationship("LLMRequest")

    def __repr__(self):
        return f"<SchemaValidationLog(id={self.id}, is_valid={self.is_valid}, success={self.was_successful})>"


class Schema(Base):
    """Stores uploaded JSON schemas."""
    __tablename__ = "schemas"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    schema_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)

    organization = relationship("Organization")

    def __repr__(self):
        return f"<Schema(id={self.id}, name='{self.name}')>"
