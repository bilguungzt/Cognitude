"""Initial schema for Cognitude LLM Monitoring Platform

Revision ID: 001
Revises: 
Create Date: 2025-11-14

This migration creates the complete database schema for Cognitude LLM monitoring platform.
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
    """Create complete LLM monitoring platform schema."""
    
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
    op.create_index('idx_organizations_name', 'organizations', ['name'])
    
    print("Creating llm_requests table...")
    op.create_table(
        'llm_requests',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('cache_key', sa.String(length=64), nullable=True),
        sa.Column('endpoint', sa.String(length=100), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_llm_requests_org_timestamp', 'llm_requests', ['organization_id', 'timestamp'])
    op.create_index('idx_llm_requests_model', 'llm_requests', ['model'])
    op.create_index('idx_llm_requests_provider', 'llm_requests', ['provider'])
    op.create_index('idx_llm_requests_cache_key', 'llm_requests', ['cache_key'])
    op.create_index('idx_llm_requests_timestamp', 'llm_requests', ['timestamp'])
    
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
    op.create_index('idx_llm_cache_prompt_hash', 'llm_cache', ['prompt_hash', 'model'])
    op.create_index('idx_llm_cache_created_at', 'llm_cache', ['created_at'])
    op.create_index('idx_llm_cache_last_accessed', 'llm_cache', ['last_accessed'])
    
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
    op.create_index('idx_provider_configs_org', 'provider_configs', ['organization_id'])
    op.create_index('idx_provider_configs_provider', 'provider_configs', ['provider'])
    op.create_index('idx_provider_configs_org_provider', 'provider_configs', ['organization_id', 'provider'])
    
    print("Creating alert_channels table...")
    op.create_table(
        'alert_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('channel_type', sa.String(length=50), nullable=False),
        sa.Column('configuration', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_alert_channels_org', 'alert_channels', ['organization_id'])
    op.create_index('idx_alert_channels_type', 'alert_channels', ['channel_type'])
    
    print("Creating alert_configs table...")
    op.create_table(
        'alert_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('threshold_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_triggered', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_alert_configs_org', 'alert_configs', ['organization_id'])
    op.create_index('idx_alert_configs_type', 'alert_configs', ['alert_type'])
    
    print("Creating rate_limit_configs table...")
    op.create_table(
        'rate_limit_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('requests_per_minute', sa.Integer(), server_default=sa.text('100'), nullable=False),
        sa.Column('requests_per_hour', sa.Integer(), server_default=sa.text('3000'), nullable=False),
        sa.Column('requests_per_day', sa.Integer(), server_default=sa.text('50000'), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id'),
    )
    op.create_index('idx_rate_limit_configs_org', 'rate_limit_configs', ['organization_id'])
    
    print("Creating reconciliation_reports table...")
    op.create_table(
        'reconciliation_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('internal_cost_usd', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('external_cost_usd', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('variance_usd', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('variance_percent', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_reconciliation_reports_org', 'reconciliation_reports', ['organization_id'])
    op.create_index('idx_reconciliation_reports_date', 'reconciliation_reports', ['start_date', 'end_date'])
    
    print("Creating schemas table...")
    op.create_table(
        'schemas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('schema_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_schemas_org', 'schemas', ['organization_id'])
    op.create_index('idx_schemas_name', 'schemas', ['name'])
    op.create_index('idx_schemas_org_name', 'schemas', ['organization_id', 'name'])
    
    print("Creating autopilot_logs table...")
    op.create_table(
        'autopilot_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('llm_request_id', sa.BigInteger(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('original_model', sa.String(length=100), nullable=False),
        sa.Column('selected_model', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=True),
        sa.Column('routing_reason', sa.Text(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('estimated_savings_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('is_cached_response', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('prompt_length', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['llm_request_id'], ['llm_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_autopilot_logs_org', 'autopilot_logs', ['organization_id'])
    op.create_index('idx_autopilot_logs_request', 'autopilot_logs', ['llm_request_id'])
    op.create_index('idx_autopilot_logs_timestamp', 'autopilot_logs', ['timestamp'])
    op.create_index('idx_autopilot_logs_models', 'autopilot_logs', ['original_model', 'selected_model'])
    
    print("Creating validation_logs table...")
    op.create_table(
        'validation_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('autopilot_log_id', sa.BigInteger(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('validation_type', sa.String(length=100), nullable=False),
        sa.Column('fix_attempted', sa.String(length=255), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('was_successful', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['autopilot_log_id'], ['autopilot_logs.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_validation_logs_autopilot', 'validation_logs', ['autopilot_log_id'])
    op.create_index('idx_validation_logs_type', 'validation_logs', ['validation_type'])
    
    print("Creating schema_validation_logs table...")
    op.create_table(
        'schema_validation_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('llm_request_id', sa.BigInteger(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('schema_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('provided_schema', postgresql.JSONB(), nullable=False),
        sa.Column('llm_response', sa.Text(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('validation_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('final_response', sa.Text(), nullable=True),
        sa.Column('was_successful', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['llm_request_id'], ['llm_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schema_id'], ['schemas.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_schema_validation_logs_org', 'schema_validation_logs', ['organization_id'])
    op.create_index('idx_schema_validation_logs_request', 'schema_validation_logs', ['llm_request_id'])
    op.create_index('idx_schema_validation_logs_schema', 'schema_validation_logs', ['schema_id'])
    op.create_index('idx_schema_validation_logs_timestamp', 'schema_validation_logs', ['timestamp'])
    
    print("✅ Initial schema migration complete")


def downgrade() -> None:
    """Drop all tables in reverse order to handle foreign key dependencies."""
    
    print("Dropping schema_validation_logs table...")
    op.drop_table('schema_validation_logs')
    
    print("Dropping validation_logs table...")
    op.drop_table('validation_logs')
    
    print("Dropping autopilot_logs table...")
    op.drop_table('autopilot_logs')
    
    print("Dropping schemas table...")
    op.drop_table('schemas')
    
    print("Dropping reconciliation_reports table...")
    op.drop_table('reconciliation_reports')
    
    print("Dropping rate_limit_configs table...")
    op.drop_table('rate_limit_configs')
    
    print("Dropping alert_configs table...")
    op.drop_table('alert_configs')
    
    print("Dropping alert_channels table...")
    op.drop_table('alert_channels')
    
    print("Dropping provider_configs table...")
    op.drop_table('provider_configs')
    
    print("Dropping llm_cache table...")
    op.drop_table('llm_cache')
    
    print("Dropping llm_requests table...")
    op.drop_table('llm_requests')
    
    print("Dropping organizations table...")
    op.drop_table('organizations')
    
    print("✅ Downgrade complete")