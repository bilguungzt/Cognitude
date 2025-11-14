-- ============================================
-- Supabase Migration Reset Script
-- Run this directly in Supabase SQL Editor
-- ============================================

-- Step 1: Drop all existing tables in correct order
-- (respecting foreign key dependencies)

DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Drop tables in reverse dependency order
    DROP TABLE IF EXISTS schema_validation_logs CASCADE;
    DROP TABLE IF EXISTS validation_logs CASCADE;
    DROP TABLE IF EXISTS autopilot_logs CASCADE;
    DROP TABLE IF EXISTS schemas CASCADE;
    DROP TABLE IF EXISTS reconciliation_reports CASCADE;
    DROP TABLE IF EXISTS rate_limit_configs CASCADE;
    DROP TABLE IF EXISTS alert_configs CASCADE;
    DROP TABLE IF EXISTS alert_channels CASCADE;
    DROP TABLE IF EXISTS provider_configs CASCADE;
    DROP TABLE IF EXISTS llm_cache CASCADE;
    DROP TABLE IF EXISTS llm_requests CASCADE;
    DROP TABLE IF EXISTS organizations CASCADE;
    
    -- Clear alembic_version table
    DROP TABLE IF EXISTS alembic_version CASCADE;
    
    RAISE NOTICE '✅ All tables dropped successfully';
END $$;

-- Step 2: Create organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_organizations_name ON organizations(name);

-- Step 3: Create llm_requests table
CREATE TABLE llm_requests (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    latency_ms INTEGER NOT NULL,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    cache_key VARCHAR(64),
    endpoint VARCHAR(100),
    status_code INTEGER,
    error_message TEXT
);

CREATE INDEX idx_llm_requests_org_timestamp ON llm_requests(organization_id, timestamp);
CREATE INDEX idx_llm_requests_model ON llm_requests(model);
CREATE INDEX idx_llm_requests_provider ON llm_requests(provider);
CREATE INDEX idx_llm_requests_cache_key ON llm_requests(cache_key);
CREATE INDEX idx_llm_requests_timestamp ON llm_requests(timestamp);

-- Step 4: Create llm_cache table
CREATE TABLE llm_cache (
    cache_key VARCHAR(64) PRIMARY KEY,
    prompt_hash VARCHAR(64) NOT NULL,
    model VARCHAR(100) NOT NULL,
    response_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hit_count INTEGER NOT NULL DEFAULT 0,
    ttl_hours INTEGER NOT NULL DEFAULT 24
);

CREATE INDEX idx_llm_cache_prompt_hash ON llm_cache(prompt_hash, model);
CREATE INDEX idx_llm_cache_created_at ON llm_cache(created_at);
CREATE INDEX idx_llm_cache_last_accessed ON llm_cache(last_accessed);

-- Step 5: Create provider_configs table
CREATE TABLE provider_configs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_provider_configs_org ON provider_configs(organization_id);
CREATE INDEX idx_provider_configs_provider ON provider_configs(provider);
CREATE INDEX idx_provider_configs_org_provider ON provider_configs(organization_id, provider);

-- Step 6: Create alert_channels table
CREATE TABLE alert_channels (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_channels_org ON alert_channels(organization_id);
CREATE INDEX idx_alert_channels_type ON alert_channels(channel_type);

-- Step 7: Create alert_configs table
CREATE TABLE alert_configs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    threshold_usd NUMERIC(10, 2) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_configs_org ON alert_configs(organization_id);
CREATE INDEX idx_alert_configs_type ON alert_configs(alert_type);

-- Step 8: Create rate_limit_configs table
CREATE TABLE rate_limit_configs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
    requests_per_minute INTEGER NOT NULL DEFAULT 100,
    requests_per_hour INTEGER NOT NULL DEFAULT 3000,
    requests_per_day INTEGER NOT NULL DEFAULT 50000,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rate_limit_configs_org ON rate_limit_configs(organization_id);

-- Step 9: Create reconciliation_reports table
CREATE TABLE reconciliation_reports (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    internal_cost_usd NUMERIC(12, 6) NOT NULL,
    external_cost_usd NUMERIC(12, 6) NOT NULL,
    variance_usd NUMERIC(12, 6) NOT NULL,
    variance_percent FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reconciliation_reports_org ON reconciliation_reports(organization_id);
CREATE INDEX idx_reconciliation_reports_date ON reconciliation_reports(start_date, end_date);

-- Step 10: Create schemas table
CREATE TABLE schemas (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    schema_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_schemas_org ON schemas(organization_id);
CREATE INDEX idx_schemas_name ON schemas(name);
CREATE INDEX idx_schemas_org_name ON schemas(organization_id, name);

-- Step 11: Create autopilot_logs table
CREATE TABLE autopilot_logs (
    id BIGSERIAL PRIMARY KEY,
    llm_request_id BIGINT REFERENCES llm_requests(id) ON DELETE SET NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    original_model VARCHAR(100) NOT NULL,
    selected_model VARCHAR(100) NOT NULL,
    task_type VARCHAR(50),
    routing_reason TEXT NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    estimated_savings_usd NUMERIC(10, 6),
    confidence_score FLOAT,
    is_cached_response BOOLEAN NOT NULL DEFAULT FALSE,
    prompt_length INTEGER,
    temperature FLOAT,
    error_message TEXT
);

CREATE INDEX idx_autopilot_logs_org ON autopilot_logs(organization_id);
CREATE INDEX idx_autopilot_logs_request ON autopilot_logs(llm_request_id);
CREATE INDEX idx_autopilot_logs_timestamp ON autopilot_logs(timestamp);
CREATE INDEX idx_autopilot_logs_models ON autopilot_logs(original_model, selected_model);

-- Step 12: Create validation_logs table
CREATE TABLE validation_logs (
    id BIGSERIAL PRIMARY KEY,
    autopilot_log_id BIGINT NOT NULL REFERENCES autopilot_logs(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validation_type VARCHAR(100) NOT NULL,
    fix_attempted VARCHAR(255) NOT NULL,
    retry_count INTEGER NOT NULL,
    was_successful BOOLEAN NOT NULL
);

CREATE INDEX idx_validation_logs_autopilot ON validation_logs(autopilot_log_id);
CREATE INDEX idx_validation_logs_type ON validation_logs(validation_type);

-- Step 13: Create schema_validation_logs table
CREATE TABLE schema_validation_logs (
    id BIGSERIAL PRIMARY KEY,
    llm_request_id BIGINT REFERENCES llm_requests(id) ON DELETE SET NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    schema_id INTEGER REFERENCES schemas(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    provided_schema JSONB NOT NULL,
    llm_response TEXT NOT NULL,
    is_valid BOOLEAN NOT NULL,
    validation_error TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    final_response TEXT,
    was_successful BOOLEAN NOT NULL
);

CREATE INDEX idx_schema_validation_logs_org ON schema_validation_logs(organization_id);
CREATE INDEX idx_schema_validation_logs_request ON schema_validation_logs(llm_request_id);
CREATE INDEX idx_schema_validation_logs_schema ON schema_validation_logs(schema_id);
CREATE INDEX idx_schema_validation_logs_timestamp ON schema_validation_logs(timestamp);

-- Step 14: Create alembic_version table and stamp with revision 001
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('001');

-- ============================================
-- ✅ Migration Complete!
-- ============================================
-- All tables have been created and migration state has been set to revision 001
-- You can now run your application and it should work with the clean database
-- ============================================

-- To verify the setup, run these commands in Supabase SQL Editor:
/*
SELECT version_num FROM alembic_version;  -- Should show '001'

SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;  -- Should show all 13 tables + alembic_version
*/