# Supabase SQL Editor - Migration Reset Guide

## Quick Steps to Reset Database

### Step 1: Access Supabase SQL Editor
1. Go to **https://supabase.com** and log in
2. Select your project: **svssbodchjapyeiuoxjm**
3. In the left sidebar, click **SQL Editor**
4. Click **New Query** (or use the existing query editor)

### Step 2: Copy and Run the Reset Script

Copy the entire contents of `scripts/supabase_manual_reset.sql` and paste it into the SQL Editor:

```bash
# Open the SQL file
cat scripts/supabase_manual_reset.sql

# Or copy it to clipboard (macOS)
cat scripts/supabase_manual_reset.sql | pbcopy
```

### Step 3: Execute the SQL
1. Paste the SQL into the editor
2. Click the **Run** button (or press `Ctrl+Enter` / `Cmd+Enter`)
3. Wait for execution to complete (should take 5-10 seconds)

### Step 4: Verify the Reset
Run these verification queries in the SQL Editor:

```sql
-- Check migration version
SELECT version_num FROM alembic_version;
-- Expected result: 001

-- Check all tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;
-- Expected: 14 tables including alembic_version
```

### Step 5: Update Your Local Environment
Make sure your `.env` file has the correct database URL:

```bash
# .env file should contain:
DATABASE_URL="postgresql://postgres:jllDZQmL4kRLBOOz@db.svssbodchjapyeiuoxjm.supabase.co:5432/postgres"
```

### Step 6: Verify Alembic State Locally
```bash
# Check current migration
alembic current
# Should show: 001

# Check migration history
alembic history
# Should show only: 001 -> initial schema
```

### Step 7: Test Your Application
```bash
# Start your app
python3 app/main.py

# In another terminal, test an endpoint
curl http://localhost:8000/api/v1/metrics
```

## What the SQL Script Does

The `scripts/supabase_manual_reset.sql` script:

1. **Drops all existing tables** (if they exist) in the correct order to handle foreign key dependencies
2. **Creates all 13 tables** with proper schema, indexes, and foreign keys:
   - organizations
   - llm_requests
   - llm_cache
   - provider_configs
   - alert_channels
   - alert_configs
   - rate_limit_configs
   - reconciliation_reports
   - schemas
   - autopilot_logs
   - validation_logs
   - schema_validation_logs
   - alembic_version (for migration tracking)

3. **Stamps the database** with migration revision `001`

## Troubleshooting

### If you get errors when running the SQL:
- **"table does not exist"**: This is normal for DROP IF EXISTS commands, ignore these warnings
- **"relation already exists"**: Some tables weren't dropped properly, run the script again
- **Connection issues**: Make sure your Supabase project is active and not paused

### If alembic commands don't work locally:
- Make sure you're in the project root directory
- Verify `DATABASE_URL` is set correctly in `.env`
- Check that `alembic.ini` exists

## Success Checklist

- [ ] SQL script executed successfully in Supabase
- [ ] `SELECT version_num FROM alembic_version;` returns `001`
- [ ] All 13 tables appear in the table list
- [ ] `alembic current` shows `001` locally
- [ ] Application starts without database errors
- [ ] API endpoints respond correctly

Once you've completed these steps, your database migrations will be fully cleaned up and ready for production use!