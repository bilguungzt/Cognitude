# Database Migration Cleanup Guide

## Overview
This guide will help you clean up the database migration history and reset the migration state in Supabase.

## What Was Done
✅ **Removed conflicting migration files:**
- `001_pivot_to_llm_monitoring.py` 
- `54cd24a12d09_add_is_active_to_schemas_table.py`

✅ **Created consolidated migration:**
- `001_initial_schema.py` - Single migration that creates all tables from scratch

## Next Steps Required

### 1. Reset Migration State in Supabase

**Option A: Using the reset script (Recommended)**

```bash
# Set your DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:password@host:port/dbname"

# Run the reset script (this will drop all tables and reset migration state)
python3 scripts/reset_migrations.py

# Or if you only want to stamp the database without dropping tables:
python3 scripts/reset_migrations.py --stamp-only
```

**Option B: Manual reset via Supabase SQL Editor**

If you prefer to run SQL commands directly in Supabase:

```sql
-- Drop all tables in correct order (respecting foreign keys)
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
```

### 2. Verify Migration Setup

After resetting, verify your migration setup:

```bash
# Check current migration (should show nothing initially)
alembic current

# Show migration history (should be empty)
alembic history

# Stamp the database with the initial migration
alembic stamp 001

# Verify the stamp worked
alembic current  # Should show "001"
```

### 3. Run the Initial Migration

```bash
# Run the migration to create all tables
alembic upgrade head

# Verify all tables were created
# You can check in Supabase dashboard or run:
python3 -c "
from app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print('Tables created:')
for table in sorted(inspector.get_table_names()):
    print(f'  - {table}')
"
```

### 4. Test API Endpoints

Once migrations are clean, test your API:

```bash
# Start your application
python3 app/main.py

# In another terminal, test key endpoints:
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'

# Test other endpoints
curl http://localhost:8000/api/v1/metrics
curl http://localhost:8000/api/v1/providers
```

### 5. Verify Database State

Check that the following tables exist in Supabase:
- `organizations`
- `llm_requests`
- `llm_cache`
- `provider_configs`
- `alert_channels`
- `alert_configs`
- `rate_limit_configs`
- `reconciliation_reports`
- `schemas`
- `autopilot_logs`
- `validation_logs`
- `schema_validation_logs`
- `alembic_version` (migration tracking)

## Troubleshooting

### If you get "Tenant or user not found" error:
- Verify your `DATABASE_URL` is correct
- Check that your Supabase project is active
- Ensure network access to Supabase is allowed

### If alembic commands fail:
- Make sure you're in the project root directory
- Verify `alembic.ini` exists and is properly configured
- Check that `DATABASE_URL` environment variable is set

### If tables are not created:
- Run `alembic current` to check migration state
- Run `alembic history` to see available migrations
- Check migration logs for errors

## Rollback Plan

If something goes wrong, you can always:

1. **Reset again**: Run the reset script again
2. **Restore from backup**: Use Supabase's built-in backup features
3. **Manual cleanup**: Use the SQL commands above to drop tables manually

## Success Criteria

✅ Migration state is clean with only revision `001`  
✅ All database tables are created successfully  
✅ API endpoints work without database errors  
✅ `alembic current` shows `001`  
✅ `alembic history` shows only the initial migration  

Once you've completed these steps, your database migrations will be clean and ready for production use!