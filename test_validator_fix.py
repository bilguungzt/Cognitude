#!/usr/bin/env python3
"""
Test script to verify the ResponseValidator can handle both object and dictionary response formats
"""
import asyncio
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.validator import ResponseValidator


class MockDB:
    """Mock database session for testing"""
    def add(self, obj):
        pass
    
    def commit(self):
        pass


def test_response_formats():
    """Test that the validator can handle both object and dictionary response formats"""
    print("Testing ResponseValidator compatibility with both response formats...")
    
    # Create a validator instance
    db = MockDB()
    validator = ResponseValidator(db, autopilot_log_id=1)
    
    # Test 1: Object-style response (like OpenAI)
    class MockChoice:
        class MockMessage:
            def __init__(self, content):
                self.content = content
        def __init__(self, content, finish_reason="stop"):
            self.message = self.MockMessage(content)
            self.finish_reason = finish_reason
    
    class MockResponse:
        def __init__(self, content, finish_reason="stop"):
            self.choices = [MockChoice(content, finish_reason)]
    
    object_response = MockResponse("Hello, this is a test response", "stop")
    
    # Test _is_response_empty with object format
    is_empty = validator._is_response_empty(object_response)
    if not is_empty:
        print("✅ Test 1 PASSED: Object format handled correctly by _is_response_empty")
    else:
        print("❌ Test 1 FAILED: Object format not handled correctly by _is_response_empty")
        return False
    
    # Test _is_truncated with object format
    is_truncated = validator._is_truncated(object_response)
    if not is_truncated:
        print("✅ Test 1b PASSED: Object format handled correctly by _is_truncated")
    else:
        print("❌ Test 1b FAILED: Object format not handled correctly by _is_truncated")
        return False
    
    # Test 2: Dictionary-style response (like Google)
    dict_response = {
        "choices": [
            {
                "message": {
                    "content": "Hello, this is a test response from dict"
                },
                "finish_reason": "stop"
            }
        ]
    }
    
    # Test _is_response_empty with dictionary format
    is_empty = validator._is_response_empty(dict_response)
    if not is_empty:
        print("✅ Test 2 PASSED: Dictionary format handled correctly by _is_response_empty")
    else:
        print("❌ Test 2 FAILED: Dictionary format not handled correctly by _is_response_empty")
        return False
    
    # Test _is_truncated with dictionary format
    is_truncated = validator._is_truncated(dict_response)
    if not is_truncated:
        print("✅ Test 2b PASSED: Dictionary format handled correctly by _is_truncated")
    else:
        print("❌ Test 2b FAILED: Dictionary format not handled correctly by _is_truncated")
        return False
    
    # Test 3: Truncated response (finish_reason = 'length')
    truncated_dict_response = {
        "choices": [
            {
                "message": {
                    "content": "This is a truncated response"
                },
                "finish_reason": "length"  # This indicates truncation
            }
        ]
    }
    
    is_truncated = validator._is_truncated(truncated_dict_response)
    if is_truncated:
        print("✅ Test 3 PASSED: Truncated dictionary format correctly detected by _is_truncated")
    else:
        print("❌ Test 3 FAILED: Truncated dictionary format not detected by _is_truncated")
        return False
    
    # Test 4: Empty content in dictionary format
    empty_dict_response = {
        "choices": [
            {
                "message": {
                    "content": ""
                },
                "finish_reason": "stop"
            }
        ]
    }
    
    is_empty = validator._is_response_empty(empty_dict_response)
    if is_empty:
        print("✅ Test 4 PASSED: Empty dictionary format correctly detected by _is_response_empty")
    else:
        print("❌ Test 4 FAILED: Empty dictionary format not detected by _is_response_empty")
        return False
    
    print("\n✅ All ResponseValidator format compatibility tests passed!")
    return True


def test_json_validation():
    """Test JSON validation with both formats"""
    print("\nTesting JSON validation with both response formats...")
    
    # Create a validator instance
    db = MockDB()
    validator = ResponseValidator(db, autopilot_log_id=1)
    
    # Valid JSON in dictionary format
    valid_json_dict = {
        "choices": [
            {
                "message": {
                    "content": '{"valid": "json", "test": true}'
                },
                "finish_reason": "stop"
            }
        ]
    }
    
    is_invalid = validator._is_json_invalid(valid_json_dict, expects_json=True)
    if not is_invalid:
        print("✅ JSON Test 1 PASSED: Valid JSON in dictionary format correctly validated")
    else:
        print("❌ JSON Test 1 FAILED: Valid JSON in dictionary format incorrectly marked as invalid")
        return False
    
    # Invalid JSON in dictionary format
    invalid_json_dict = {
        "choices": [
            {
                "message": {
                    "content": 'This is not valid JSON { invalid: syntax'
                },
                "finish_reason": "stop"
            }
        ]
    }
    
    is_invalid = validator._is_json_invalid(invalid_json_dict, expects_json=True)
    if is_invalid:
        print("✅ JSON Test 2 PASSED: Invalid JSON in dictionary format correctly detected")
    else:
        print("❌ JSON Test 2 FAILED: Invalid JSON in dictionary format not detected")
        return False
    
    print("✅ All JSON validation tests passed!")
    return True


if __name__ == "__main__":
    success1 = test_response_formats()
    success2 = test_json_validation()
    
    if success1 and success2:
        print("\n🎉 ResponseValidator fixes are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some ResponseValidator tests failed!")
        sys.exit(1)