import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call

from sqlalchemy.orm import Session

from app.core.validator import ResponseValidator
from app.schemas import ChatCompletionRequest, ChatMessage
from app.models import ValidationLog

# Mock response classes to simulate OpenAI's response structure
class MockChoice:
    def __init__(self, content, finish_reason="stop"):
        self.message = ChatMessage(role="assistant", content=content)
        self.finish_reason = finish_reason

class MockCompletionResponse:
    def __init__(self, choices):
        self.choices = choices

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    db_session = MagicMock(spec=Session)
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    return db_session

@pytest.fixture
def mock_api_call():
    """Fixture for a mocked API call function."""
    return AsyncMock()

@pytest.fixture
def validator(mock_db_session):
    """Fixture for a ResponseValidator instance."""
    return ResponseValidator(db=mock_db_session, autopilot_log_id=1)

@pytest.mark.asyncio
async def test_valid_json_response_passes(validator, mock_api_call):
    """Test that a valid JSON response passes validation without any changes."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Give me a json object.")])
    response = MockCompletionResponse([MockChoice('{"key": "value"}')])
    
    result = await validator.validate_and_fix(response, request, mock_api_call)
    
    assert result == response
    mock_api_call.assert_not_called()

@pytest.mark.asyncio
async def test_non_json_response_triggers_fix(validator, mock_db_session, mock_api_call):
    """Test that a non-JSON response triggers the _attempt_fix method and retries."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Give me a json object.")])
    invalid_response = MockCompletionResponse([MockChoice("this is not json")])
    valid_response = MockCompletionResponse([MockChoice('{"key": "value"}')])
    
    mock_api_call.return_value = valid_response
    
    result = await validator.validate_and_fix(invalid_response, request, mock_api_call)
    
    assert result == valid_response
    mock_api_call.assert_called_once()
    # Check that a log was added for the failed validation and the successful fix
    assert mock_db_session.add.call_count == 2

@pytest.mark.asyncio
async def test_empty_response_triggers_fix(validator, mock_db_session, mock_api_call):
    """Test that an empty response triggers a retry."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Tell me a joke.")])
    empty_response = MockCompletionResponse([MockChoice("")])
    valid_response = MockCompletionResponse([MockChoice("Why did the chicken cross the road?")])
    
    mock_api_call.return_value = valid_response
    
    result = await validator.validate_and_fix(empty_response, request, mock_api_call)
    
    assert result == valid_response
    mock_api_call.assert_called_once()
    assert mock_db_session.add.call_count == 2

@pytest.mark.asyncio
async def test_truncated_response_triggers_fix(validator, mock_db_session, mock_api_call):
    """Test that a truncated response triggers a retry with increased max_tokens."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Tell me a long story.")], max_tokens=10)
    truncated_response = MockCompletionResponse([MockChoice("This is a very long story that got cut off", finish_reason="length")])
    full_response = MockCompletionResponse([MockChoice("This is a very long story that did not get cut off.")])
    
    mock_api_call.return_value = full_response
    
    result = await validator.validate_and_fix(truncated_response, request, mock_api_call)
    
    assert result == full_response
    mock_api_call.assert_called_once()
    # The modified request should have a higher max_tokens value
    called_request = mock_api_call.call_args[0][0]
    assert called_request.max_tokens == 15
    assert mock_db_session.add.call_count == 2

@pytest.mark.asyncio
async def test_successful_fix_after_one_retry(validator, mock_db_session, mock_api_call):
    """Test a scenario where a response is successfully fixed after one retry."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Give me a json object.")])
    invalid_response = MockCompletionResponse([MockChoice("not json")])
    valid_response = MockCompletionResponse([MockChoice('{"fixed": true}')])
    
    # The first call to the mock will return the invalid response, the second will return the valid one.
    mock_api_call.side_effect = [valid_response]
    
    result = await validator.validate_and_fix(invalid_response, request, mock_api_call)
    
    assert result == valid_response
    assert mock_api_call.call_count == 1
    assert mock_db_session.add.call_count == 2

@pytest.mark.asyncio
async def test_max_retries_reached(validator, mock_db_session, mock_api_call):
    """Test that the validator gives up after the maximum number of retries."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Give me a json object.")])
    invalid_response = MockCompletionResponse([MockChoice("not json")])
    
    # The API call will always return an invalid response
    mock_api_call.return_value = invalid_response
    
    result = await validator.validate_and_fix(invalid_response, request, mock_api_call)
    
    assert result == invalid_response
    assert mock_api_call.call_count == validator.MAX_RETRIES
    # One log for each failed attempt, and one for each failed fix
    assert mock_db_session.add.call_count == validator.MAX_RETRIES * 2

@pytest.mark.asyncio
async def test_logging_of_validation_failures(validator, mock_db_session, mock_api_call):
    """Ensure that validation failures and fix attempts are correctly logged."""
    request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="Give me a json object.")])
    invalid_response = MockCompletionResponse([MockChoice("not json")])
    valid_response = MockCompletionResponse([MockChoice('{"fixed": true}')])
    
    mock_api_call.return_value = valid_response
    
    await validator.validate_and_fix(invalid_response, request, mock_api_call)
    
    # Check that the logs were created correctly
    calls = mock_db_session.add.call_args_list
    assert len(calls) == 2

    # First log: the initial failure
    first_log_entry = calls[0].args[0]
    assert isinstance(first_log_entry, ValidationLog)
    assert getattr(first_log_entry, 'validation_type') == 'invalid_json'
    assert getattr(first_log_entry, 'was_successful') is False
    
    # Second log: the successful fix
    second_log_entry = calls[1].args[0]
    assert isinstance(second_log_entry, ValidationLog)
    assert getattr(second_log_entry, 'fix_attempted') == 'retry_with_stricter_prompt'
    assert getattr(second_log_entry, 'was_successful') is True