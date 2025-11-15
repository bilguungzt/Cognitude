#!/usr/bin/env python3
"""
Debug script to diagnose API internal server errors
Run this inside the Docker container to identify issues
"""
import sys
import os
import traceback
import asyncio

# Add the code directory to the path
sys.path.insert(0, '/code')

def test_database():
    """Test database connectivity"""
    print("🔍 Testing database connection...")
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        # Try a simple query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()
        print(f"✅ Database connection successful: {result}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_google_provider():
    """Test Google provider configuration"""
    print("\n🔍 Testing Google provider...")
    try:
        from app.database import SessionLocal
        from app import models, crud
        from app.services.router import ProviderRouter
        
        db = SessionLocal()
        
        # Check if Google provider exists
        providers = crud.get_provider_configs(db, organization_id=1, enabled_only=True)
        google_providers = [p for p in providers if str(p.provider) == 'google']
        
        if not google_providers:
            print("❌ No Google provider configured")
            db.close()
            return False
            
        google_provider = google_providers[0]
        print(f"✅ Found Google provider: ID={google_provider.id}")
        print(f"   Enabled: {google_provider.enabled}")
        print(f"   Priority: {google_provider.priority}")
        
        # Test API key
        try:
            api_key = google_provider.get_api_key()
            if api_key:
                print(f"✅ API key retrieved (length: {len(api_key)})")
                print(f"   Key starts with: {api_key[:10]}...")
            else:
                print("❌ API key is empty")
                db.close()
                return False
        except Exception as e:
            print(f"❌ Error getting API key: {e}")
            traceback.print_exc()
            db.close()
            return False
        
        # Test router
        router = ProviderRouter(db, organization_id=1)
        selected = router.select_provider('gemini-flash')
        if selected:
            print(f"✅ Router selected provider: {selected.provider}")
        else:
            print("❌ Router could not select provider")
            
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Google provider test failed: {e}")
        traceback.print_exc()
        return False

async def test_google_api_call():
    """Test actual Google API call"""
    print("\n🔍 Testing Google API call...")
    try:
        from app.database import SessionLocal
        from app.services.router import ProviderRouter
        
        db = SessionLocal()
        router = ProviderRouter(db, organization_id=1)
        
        # Get Google provider
        providers = router.get_providers(enabled_only=True)
        google_provider = next((p for p in providers if str(p.provider) == 'google'), None)
        
        if not google_provider:
            print("❌ No Google provider found")
            db.close()
            return False
            
        # Test API call
        messages = [{"role": "user", "content": "Hello, test!"}]
        result = await router.call_provider(
            google_provider, 
            "gemini-flash", 
            messages,
            max_tokens=50
        )
        
        print("✅ Google API call successful")
        print(f"Response: {result['choices'][0]['message']['content'][:100]}...")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Google API call failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment variables...")
    critical_vars = ['DATABASE_URL', 'SECRET_KEY']
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)}")
        else:
            print(f"❌ {var}: NOT SET")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🔧 API Error Debug Script")
    print("=" * 60)
    
    # Run synchronous tests
    db_ok = test_database()
    env_ok = test_environment()
    google_ok = test_google_provider()
    
    # Run async test
    api_ok = asyncio.run(test_google_api_call())
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   Environment: {'✅' if env_ok else '❌'}")
    print(f"   Google Provider: {'✅' if google_ok else '❌'}")
    print(f"   Google API Call: {'✅' if api_ok else '❌'}")
    
    if all([db_ok, env_ok, google_ok, api_ok]):
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())