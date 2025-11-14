#!/usr/bin/env python3
"""
Diagnostic script to identify database configuration issues.
This script will help determine which database is actually being used.
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from app.config import get_settings

def diagnose_database_config():
    """Diagnose current database configuration and connection."""
    print("=== DATABASE CONFIGURATION DIAGNOSIS ===\n")
    
    # Check environment variables
    print("1. ENVIRONMENT VARIABLES:")
    print(f"   DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
    if os.getenv('DATABASE_URL'):
        url = os.getenv('DATABASE_URL')
        # Mask password for security
        if '@' in url:
            masked_url = url.split('@')[0].split('://')[0] + '://***:***@' + url.split('@')[1]
            print(f"   DATABASE_URL value: {masked_url}")
        else:
            print(f"   DATABASE_URL value: {url}")
    
    print(f"   SUPABASE_URL: {'SET' if os.getenv('SUPABASE_URL') else 'NOT SET'}")
    print(f"   ENVIRONMENT: {os.getenv('ENVIRONMENT', 'NOT SET')}")
    print()
    
    # Check settings from config
    print("2. APP CONFIGURATION:")
    settings = get_settings()
    print(f"   Settings DATABASE_URL: {'SET' if settings.DATABASE_URL else 'NOT SET'}")
    if settings.DATABASE_URL:
        url = str(settings.DATABASE_URL)
        if '@' in url:
            masked_url = url.split('@')[0].split('://')[0] + '://***:***@' + url.split('@')[1]
            print(f"   Settings DATABASE_URL value: {masked_url}")
        else:
            print(f"   Settings DATABASE_URL value: {url}")
    print()
    
    # Test database connection
    print("3. DATABASE CONNECTION TEST:")
    try:
        engine = create_engine(str(settings.DATABASE_URL))
        with engine.connect() as conn:
            # Get database info
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"   ✓ Connected successfully")
            print(f"   Database version: {version}")
            
            # Check if we're connected to Supabase
            if 'supabase' in str(settings.DATABASE_URL).lower():
                print("   ✓ Configuration appears to be Supabase")
            else:
                print("   ⚠ Configuration appears to be local PostgreSQL")
            
            # List existing tables
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            print(f"   Existing tables: {len(tables)} found")
            if tables:
                for table in sorted(tables):
                    print(f"     - {table}")
            else:
                print("     No tables found - migrations may not have been run")
                
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
    print()
    
    # Check Alembic configuration
    print("4. ALEMBIC CONFIGURATION:")
    try:
        with open('alembic.ini', 'r') as f:
            content = f.read()
            if 'supabase' in content.lower():
                print("   ✓ Alembic.ini contains Supabase configuration")
            else:
                print("   ⚠ Alembic.ini does not contain Supabase configuration")
    except Exception as e:
        print(f"   ✗ Could not read alembic.ini: {e}")
    print()
    
    # Check migration status
    print("5. MIGRATION STATUS:")
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        
        print(f"   Migration scripts found: {len(list(script.walk_revisions()))}")
        heads = script.get_heads()
        print(f"   Latest migration: {heads[0] if heads else 'None'}")
        
    except Exception as e:
        print(f"   ✗ Could not check migration status: {e}")
    print()

if __name__ == "__main__":
    diagnose_database_config()