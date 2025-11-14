#!/usr/bin/env python3
"""
Script to reset migration state in Supabase database.
This script should be run when you need to clean up migration history
and start fresh with the consolidated migration.
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def reset_migration_state(database_url, stamp_only=False):
    """
    Reset the migration state in the database.
    
    Args:
        database_url: Database connection URL
        stamp_only: If True, only stamp the current revision without dropping tables
    """
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start transaction
            with conn.begin():
                if not stamp_only:
                    print("🔥 Dropping all existing tables...")
                    
                    # Get all table names
                    result = conn.execute(text("""
                        SELECT tablename 
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """))
                    
                    tables = [row[0] for row in result]
                    
                    # Drop tables in correct order (respecting foreign keys)
                    table_order = [
                        'schema_validation_logs', 'validation_logs', 'autopilot_logs',
                        'schemas', 'reconciliation_reports', 'rate_limit_configs',
                        'alert_configs', 'alert_channels', 'provider_configs',
                        'llm_cache', 'llm_requests', 'organizations'
                    ]
                    
                    for table in table_order:
                        if table in tables:
                            try:
                                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                                print(f"  ✓ Dropped {table}")
                            except SQLAlchemyError as e:
                                print(f"  ⚠️  Could not drop {table}: {e}")
                
                # Clear alembic_version table
                print("\n🗑️  Clearing alembic_version table...")
                conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                
                print("\n✅ Migration state reset complete")
                
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def stamp_database(database_url, revision='001'):
    """
    Stamp the database with the given migration revision.
    
    Args:
        database_url: Database connection URL
        revision: Migration revision to stamp
    """
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            with conn.begin():
                print(f"📋 Stamping database with revision {revision}...")
                
                # Create alembic_version table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    )
                """))
                
                # Insert the revision
                conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                    {"revision": revision}
                )
                
                print(f"✅ Database stamped with revision {revision}")
                
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Reset migration state in Supabase')
    parser.add_argument('--stamp-only', action='store_true', 
                       help='Only stamp the database, do not drop tables')
    parser.add_argument('--revision', default='001',
                       help='Revision to stamp (default: 001)')
    
    args = parser.parse_args()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set it with your Supabase connection string")
        sys.exit(1)
    
    print(f"🔄 Connecting to database...")
    print(f"📍 Revision to stamp: {args.revision}")
    
    if args.stamp_only:
        stamp_database(database_url, args.revision)
    else:
        reset_migration_state(database_url, stamp_only=False)
        stamp_database(database_url, args.revision)
    
    print("\n🎉 Migration reset complete!")
    print("\nNext steps:")
    print("1. Run: alembic current (should show revision 001)")
    print("2. Run: alembic history (should show only the initial migration")
    print("3. Test your API endpoints")


if __name__ == "__main__":
    main()