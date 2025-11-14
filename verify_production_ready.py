#!/usr/bin/env python3
"""
Comprehensive verification script to check if production is ready.
Run this to verify all components are working correctly.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def check_local_env():
    """Check local .env configuration."""
    print("=" * 60)
    print("1. CHECKING LOCAL .ENV CONFIGURATION")
    print("=" * 60)
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Local .env file not found")
        return False
    
    with open(env_path) as f:
        content = f.read()
        if 'DATABASE_URL=postgresql://postgres:jllDZQmL4kRLBOOz@db.svssbodchjapyeiuoxjm.supabase.co:5432/postgres' in content:
            print("✅ Local DATABASE_URL is correct")
            return True
        else:
            print("❌ Local DATABASE_URL is incorrect")
            return False

def check_production_env():
    """Check production .env configuration."""
    print("\n" + "=" * 60)
    print("2. CHECKING PRODUCTION .ENV CONFIGURATION")
    print("=" * 60)
    
    try:
        # Check if we can connect to production
        result = subprocess.run([
            'sshpass', '-p', 'GAzette4ever', 
            'ssh', 'root@165.22.158.75', 
            'cat /root/driftguard_mvp/.env | grep DATABASE_URL'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if 'postgresql://postgres:jllDZQmL4kRLBOOz@db.svssbodchjapyeiuoxjm.supabase.co:5432/postgres' in result.stdout:
                print("✅ Production DATABASE_URL is correct")
                return True
            else:
                print("❌ Production DATABASE_URL is incorrect")
                print(f"Found: {result.stdout.strip()}")
                return False
        else:
            print("❌ Cannot connect to production server")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking production: {e}")
        return False

def check_migration_files():
    """Check migration files integrity."""
    print("\n" + "=" * 60)
    print("3. CHECKING MIGRATION FILES")
    print("=" * 60)
    
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        
        heads = script.get_heads()
        print(f"✅ Migration heads: {heads}")
        
        revisions = list(script.walk_revisions())
        print(f"✅ Available revisions: {len(revisions)}")
        for rev in reversed(revisions):
            print(f"   - {rev.revision}: {rev.doc}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking migrations: {e}")
        return False

def check_database_connectivity():
    """Check database connectivity."""
    print("\n" + "=" * 60)
    print("4. CHECKING DATABASE CONNECTIVITY")
    print("=" * 60)
    
    try:
        from app.config import get_settings
        from sqlalchemy import create_engine, text
        
        settings = get_settings()
        engine = create_engine(str(settings.DATABASE_URL))
        
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Database connection successful")
            print(f"✅ Database version: {version.split(',')[0]}")
            
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                );
            """))
            exists = result.scalar()
            
            if exists:
                result = conn.execute(text("SELECT version_num FROM alembic_version;"))
                version_num = result.scalar()
                print(f"✅ Alembic version: {version_num}")
            else:
                print("⚠️  Alembic version table not found (run fix_alembic_version.sql)")
            
            # Count tables
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE';
            """))
            table_count = result.scalar()
            print(f"✅ Total tables: {table_count}")
            
            if table_count >= 12:
                print("✅ All expected tables present")
            else:
                print(f"⚠️  Expected 12+ tables, found {table_count}")
            
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_docker_containers():
    """Check Docker containers on production."""
    print("\n" + "=" * 60)
    print("5. CHECKING DOCKER CONTAINERS (PRODUCTION)")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            'sshpass', '-p', 'GAzette4ever', 
            'ssh', 'root@165.22.158.75', 
            'docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Docker containers running:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
            return True
        else:
            print("❌ Cannot check Docker containers")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False

def check_api_endpoint():
    """Check if API endpoint is responding."""
    print("\n" + "=" * 60)
    print("6. CHECKING API ENDPOINT")
    print("=" * 60)
    
    try:
        # Try to access the API
        response = requests.get('http://165.22.158.75:8000/api/v1/metrics', timeout=10)
        
        if response.status_code == 200:
            print("✅ API endpoint responding (200 OK)")
            return True
        else:
            print(f"⚠️  API returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API endpoint")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

def main():
    """Run all checks."""
    print("🔍 PRODUCTION READINESS VERIFICATION")
    print("=" * 60)
    print("Checking if production is ready for deployment...")
    print()
    
    checks = [
        ("Local .env", check_local_env),
        ("Production .env", check_production_env),
        ("Migration files", check_migration_files),
        ("Database connectivity", check_database_connectivity),
        ("Docker containers", check_docker_containers),
        ("API endpoint", check_api_endpoint),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 PRODUCTION IS READY!")
        print("\nNext steps:")
        print("1. Run: alembic current (should show 001)")
        print("2. Run: alembic upgrade head (if needed)")
        print("3. Test API endpoints")
        print("4. Monitor logs for any errors")
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("Please review the errors above and fix them before deploying.")

if __name__ == "__main__":
    main()