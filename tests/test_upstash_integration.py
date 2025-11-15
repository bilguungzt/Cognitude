#!/usr/bin/env python3
"""
Test script to verify Upstash Redis integration
"""
import os
import sys
sys.path.append('.')

from app.config import get_settings
settings = get_settings()
from app.services.redis_cache import redis_cache

def test_upstash_connection():
    """Test Upstash Redis connection and basic operations"""
    print("🧪 Testing Upstash Redis Integration")
    print("=" * 50)
    
    # Check configuration
    print(f"REDIS_URL: {settings.REDIS_URL}")
    print(f"REDIS_TOKEN: {'Set' if settings.REDIS_TOKEN else 'Not Set'}")
    print(f"Redis available: {redis_cache.available}")
    
    if not redis_cache.available:
        print("❌ Redis cache is not available")
        return False
    
    # Test basic operations
    try:
        # Test set
        print("\n📤 Testing SET operation...")
        test_key = "test:cognitude:integration"
        test_value = {"message": "Hello from Upstash Redis!", "status": "working"}
        
        # Use the underlying redis client directly for this test
        if hasattr(redis_cache.redis, 'set'):
            redis_cache.redis.set(test_key, str(test_value))
            print("✅ SET successful")
        
        # Test get
        print("\n📥 Testing GET operation...")
        result = redis_cache.redis.get(test_key)
        print(f"✅ GET successful: {result}")
        
        # Test ping
        print("\n🏓 Testing PING...")
        pong = redis_cache.redis.ping()
        print(f"✅ PING successful: {pong}")
        
        # Test cache stats
        print("\n📊 Testing cache stats...")
        stats = redis_cache.get_stats(organization_id=1)
        print(f"✅ Stats retrieved: {stats}")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Upstash Redis is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upstash_connection()
    sys.exit(0 if success else 1)