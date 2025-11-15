#!/usr/bin/env python3
"""
Validation script to test production configuration after container restart.
This script tests Redis, database, and authentication functionality.
"""

import sys
import os
from pathlib import Path

def test_configuration_loading():
    """Test that configuration is loaded correctly from environment."""
    print("=== CONFIGURATION LOADING VALIDATION ===\n")
    
    # Test 1: Environment variables
    print("1. Testing environment variable loading...")
    required_vars = ["DATABASE_URL", "REDIS_URL", "REDIS_TOKEN", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: SET")
        else:
            print(f"   ❌ {var}: NOT SET")
            return False
    
    print("   ✅ All required environment variables are set\n")
    return True

def test_redis_connection():
    """Test Redis connection."""
    print("2. Testing Redis connection...")
    
    try:
        from app.services.redis_cache import redis_cache
        health = redis_cache.health_check()
        
        if health["status"] == "healthy":
            print(f"   ✅ Redis connected successfully")
            print(f"      - Connected clients: {health.get('connected_clients', 'N/A')}")
            print(f"      - Memory usage: {health.get('used_memory_human', 'N/A')}")
            print(f"      - Uptime: {health.get('uptime_in_seconds', 0)} seconds")
            return True
        else:
            print(f"   ❌ Redis connection failed: {health.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Redis test failed with exception: {e}")
        return False

def test_database_connection():
    """Test database connection."""
    print("\n3. Testing database connection...")
    
    try:
        from app.config import get_settings
        from sqlalchemy import create_engine, text
        
        settings = get_settings()
        engine = create_engine(str(settings.DATABASE_URL))
        
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("   ✅ Database connection successful")
                
                # Get database info
                result = conn.execute(text("SELECT version();"))
                version = result.scalar()
                print(f"   Database version: {version}")
                
                # Check if it's Supabase
                if 'supabase' in str(settings.DATABASE_URL).lower():
                    print("   ✅ Connected to Supabase")
                else:
                    print("   ⚠️  Connected to local PostgreSQL (not Supabase)")
                
                return True
            else:
                print("   ❌ Database test query failed")
                return False
                
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_authentication():
    """Test authentication functionality."""
    print("\n4. Testing authentication service...")
    
    try:
        from app import crud, schemas, security
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Test API key generation
            api_key = security.create_api_key()
            if not api_key:
                print("   ❌ API key generation failed")
                return False
            
            print("   ✅ API key generation successful")
            
            # Test password hashing
            hashed = security.get_password_hash(api_key)
            if not hashed:
                print("   ❌ Password hashing failed")
                return False
            
            print("   ✅ Password hashing successful")
            
            # Test database operations
            orgs = crud.get_organizations(db)
            print(f"   ✅ Database query successful ({len(orgs)} organizations found)")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

def test_smart_routing():
    """Test smart routing with Gemini models."""
    print("\n5. Testing smart routing configuration...")
    
    try:
        from app.services.smart_router import smart_router
        from app.config import get_settings
        
        settings = get_settings()
        
        # Check if Gemini is configured
        if hasattr(settings, 'ALLOWED_PROVIDERS') and 'google' in settings.ALLOWED_PROVIDERS:
            print("   ✅ Google provider is enabled in smart routing")
        else:
            print("   ⚠️  Google provider not found in ALLOWED_PROVIDERS")
        
        # Test router initialization
        if smart_router:
            print("   ✅ Smart router initialized successfully")
            return True
        else:
            print("   ❌ Smart router initialization failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Smart routing test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Cognitude Production Configuration Validator")
    print("=" * 50)
    print("")
    
    tests = [
        test_configuration_loading,
        test_redis_connection,
        test_database_connection,
        test_authentication,
        test_smart_routing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"\n❌ Test {test.__name__} FAILED")
        except Exception as e:
            print(f"\n❌ Test {test.__name__} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Production configuration is working correctly.")
        print("\nNext steps:")
        print("1. Test API endpoints with real requests")
        print("2. Verify Gemini smart routing with actual LLM calls")
        print("3. Monitor application logs for any issues")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above for details.")
        print("\nRecommended actions:")
        print("1. Check environment variables in /opt/cognitude/.env")
        print("2. Verify Redis REST API URL and token")
        print("3. Confirm Supabase database credentials")
        print("4. Check container logs: docker logs -f driftguard_mvp_api_1")
        return 1

if __name__ == "__main__":
    sys.exit(main())