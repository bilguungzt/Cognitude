"""pivot_to_llm_monitoring

Revision ID: 001
Revises: 
Create Date: 2025-11-10

This migration pivots Cognitude from ML model monitoring to LLM monitoring platform:
- Drops old tables: models, model_features, predictions, drift_alerts, drift_history
- Keeps: organizations, alert_channels
- Renames: api_logs → llm_requests (with schema changes)
- Adds: llm_cache, provider_configs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema for LLM monitoring platform."""
    
    # ============================================================================
    # Step 1: Drop old ML monitoring tables
    # ============================================================================
    print("Dropping old ML monitoring tables...")
    
    op.drop_table('drift_history', if_exists=True)
    op.drop_table('drift_alerts', if_exists=True)
    op.drop_table('predictions', if_exists=True)
    op.drop_table('model_features', if_exists=True)
    op.drop_table('models', if_exists=True)
    
    # Drop api_logs if it exists (will recreate as llm_requests)
    op.drop_table('api_logs', if_exists=True)
    
    # ============================================================================
    # Step 2: Create Organizations table
    # ============================================================================
    print("Creating organizations table...")
    
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('api_key_hash')
    )

    # ============================================================================
    # Step 3: Create LLM Requests table
    # ============================================================================
    print("Creating llm_requests table...")
    
    op.create_table(
        'llm_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Request details
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        
        # Token tracking
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        
        # Cost tracking
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        
        # Performance
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        
        # Caching
        sa.Column('cache_hit', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('cache_key', sa.String(length=64), nullable=True),
        
        # Metadata
        sa.Column('endpoint', sa.String(length=100), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Indexes
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for common queries
    op.create_index('idx_llm_requests_org_timestamp', 'llm_requests', ['organization_id', 'timestamp'])
    op.create_index('idx_llm_requests_model', 'llm_requests', ['model'])
    op.create_index('idx_llm_requests_provider', 'llm_requests', ['provider'])
    op.create_index('idx_llm_requests_cache_key', 'llm_requests', ['cache_key'])
    
    # ============================================================================
    # Step 3: Create LLM Cache table
    # ============================================================================
    print("Creating llm_cache table...")
    
    op.create_table(
        'llm_cache',
        sa.Column('cache_key', sa.String(length=64), nullable=False),
        sa.Column('prompt_hash', sa.String(length=64), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('response_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('hit_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('ttl_hours', sa.Integer(), server_default=sa.text('24'), nullable=False),
        
        sa.PrimaryKeyConstraint('cache_key'),
    )
    
    # Create indexes for cache lookups
    op.create_index('idx_llm_cache_prompt_hash', 'llm_cache', ['prompt_hash', 'model'])
    op.create_index('idx_llm_cache_created_at', 'llm_cache', ['created_at'])
    
    # ============================================================================
    # Step 4: Create Provider Configs table
    # ============================================================================
    print("Creating provider_configs table...")
    
    op.create_table(
        'provider_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('priority', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_provider_configs_org', 'provider_configs', ['organization_id'])
    op.create_index('idx_provider_configs_provider', 'provider_configs', ['provider'])
    
    print("✅ Migration complete: Cognitude pivoted to LLM monitoring platform")


def downgrade() -> None:
    """Downgrade - recreate old ML monitoring schema."""
    
    print("⚠️  Downgrading to ML monitoring schema...")
    
    # Drop LLM tables
    op.drop_table('provider_configs')
    op.drop_table('llm_cache')
    op.drop_table('llm_requests')
    
    # Recreate old tables (basic structure)
    op.create_table(
        'models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('model_type', sa.String(), nullable=True),
        sa.Column('baseline_mean', sa.Float(), nullable=True),
        sa.Column('baseline_std', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
    )
    
    op.create_table(
        'model_features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(), nullable=True),
        sa.Column('feature_type', sa.String(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('baseline_stats', postgresql.JSONB(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
    )
    
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('prediction_value', sa.Float(), nullable=False),
        sa.Column('actual_value', sa.Float(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('features', postgresql.JSONB(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
    )
    
    print("✅ Downgrade complete: Restored ML monitoring schema")
