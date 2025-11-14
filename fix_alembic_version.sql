-- Fix alembic_version table for Cognitude MVP
-- Run this in Supabase SQL Editor to restore migration tracking

-- First, check if alembic_version table exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_name = 'alembic_version') THEN
        -- Create alembic_version table if it doesn't exist
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
        RAISE NOTICE 'Created alembic_version table';
    ELSE
        RAISE NOTICE 'alembic_version table already exists';
    END IF;
END $$;

-- Insert or update the version number to 001 (initial schema)
-- This indicates that migration 001 has been applied
INSERT INTO alembic_version (version_num) 
VALUES ('001')
ON CONFLICT (version_num) 
DO UPDATE SET version_num = '001';

-- Verify the result
SELECT version_num FROM alembic_version;

-- Expected output:
--  version_num 
-- -------------
--  001
-- (1 row)

-- Verify all tables exist (should be 12-13 tables including alembic_version)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Expected tables:
-- alembic_version
-- alert_channels
-- alert_configs
-- autopilot_logs
-- llm_cache
-- llm_requests
-- organizations
-- provider_configs
-- rate_limit_configs
-- reconciliation_reports
-- schemas
-- schema_validation_logs
-- validation_logs