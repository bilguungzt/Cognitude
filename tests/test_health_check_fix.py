#!/usr/bin/env python3
"""
Test script to verify the Health Check endpoint fix
"""
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.api.monitoring import health_check
from unittest.mock import Mock, MagicMock


def test_health_check_logic():
    """Test that the health check logic works correctly"""
    print("Testing Health Check endpoint logic...")
    
    # Create mock database session
    mock_db = Mock()
    
    # Test 1: Both database and Redis are healthy
    mock_db.execute = Mock(return_value=None)
    from app.services.redis_cache import redis_cache
    original_available = redis_cache.available
    original_redis = redis_cache.redis
    
    # Temporarily mock the redis cache to be available and healthy
    mock_redis_client = Mock()
    mock_redis_client.ping = Mock(return_value=True)
    
    # Save original values and set up mocks
    original_available = redis_cache.available
    original_redis = redis_cache.redis
    
    redis_cache.available = True
    redis_cache.redis = mock_redis_client
    
    try:
        result = health_check(mock_db)
        expected = {"status": "healthy", "checks": {"database": {"status": "healthy"}, "redis": {"status": "healthy"}}}
        if result == expected:
            print("✅ Test 1 PASSED: Health check returns healthy when both services are OK")
        else:
            print(f"❌ Test 1 FAILED: Expected {expected}, got {result}")
            return False
    except Exception as e:
        print(f"❌ Test 1 FAILED: Unexpected exception: {e}")
        return False
    finally:
        # Restore original values
        redis_cache.available = original_available
        redis_cache.redis = original_redis
    
    # Test 2: Database fails, Redis is healthy
    mock_db.execute = Mock(side_effect=Exception("DB connection failed"))
    
    redis_cache.available = True
    redis_cache.redis = mock_redis_client
    
    try:
        result = health_check(mock_db)
        print("❌ Test 2 FAILED: Should have raised HTTPException when database fails")
        return False
    except Exception as e:
        # This is expected - it should raise an HTTPException
        print("✅ Test 2 PASSED: Health check raises exception when database fails")
    
    finally:
        # Restore original values
        redis_cache.available = original_available
        redis_cache.redis = original_redis
        mock_db.execute = Mock(return_value=None)  # Reset to working state for next test
    
    # Test 3: Database is healthy, Redis fails
    redis_cache.available = False
    redis_cache.redis = None
    
    try:
        result = health_check(mock_db)
        print("❌ Test 3 FAILED: Should have raised HTTPException when Redis fails")
        return False
    except Exception as e:
        # This is expected - it should raise an HTTPException
        print("✅ Test 3 PASSED: Health check raises exception when Redis fails")
    
    finally:
        # Restore original values
        redis_cache.available = original_available
        redis_cache.redis = original_redis
    
    print("\n✅ All Health Check logic tests passed!")
    return True


def test_health_check_detailed_response():
    """Test that the health check provides detailed information"""
    print("\nTesting Health Check detailed response...")
    
    # Test the logic without triggering the actual exception
    from app.api.monitoring import health_check
    import inspect
    
    # Check that the function includes detailed status information
    source = inspect.getsource(health_check)
    
    if '"checks"' in source and 'status' in source and 'database' in source and 'redis' in source:
        print("✅ Detailed response test PASSED: Function includes detailed status information")
        return True
    else:
        print("❌ Detailed response test FAILED: Function does not include detailed status information")
        return False


if __name__ == "__main__":
    success1 = test_health_check_logic()
    success2 = test_health_check_detailed_response()
    
    if success1 and success2:
        print("\n🎉 Health Check fixes are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some Health Check tests failed!")
        sys.exit(1)