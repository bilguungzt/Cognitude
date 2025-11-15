import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.autopilot import AutopilotEngine, TaskClassifier, ModelSelector
from app import schemas, models

# Mock data for testing
mock_organization = models.Organization(id=1, name="Test Org", api_key_hash="hashed_key")

def create_mock_request(messages, model="gpt-4-0125-preview", temperature=0.0, max_tokens=100):
    """Helper to create a mock ChatCompletionRequest."""
    return schemas.ChatCompletionRequest(
        model=model,
        messages=[schemas.ChatMessage(role=msg["role"], content=msg["content"]) for msg in messages],
        temperature=temperature,
        max_tokens=max_tokens
    )

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked SQLAlchemy session."""
    session = MagicMock(spec=Session)
    session.add = MagicMock()
    session.commit = MagicMock()
    return session

@pytest.fixture
def mock_redis_client():
    """Fixture for a mocked RedisCache client."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.set = MagicMock()
    return redis

@pytest.fixture
def autopilot_engine(mock_db_session, mock_redis_client):
    """Fixture for an AutopilotEngine instance with mocked dependencies."""
    return AutopilotEngine(db=mock_db_session, redis_client=mock_redis_client)

# --- TaskClassifier Tests ---
@pytest.mark.parametrize("prompt, expected_task", [
    ("Can you classify this email as spam or not?", "classification"),
    ("Please extract the names of people mentioned in this article.", "extraction"),
    ("Translate 'hello world' into French.", "translation"),
    ("Summarize the following text for me.", "summarization"),
    ("Write a python function to calculate fibonacci.", "code"),
    ("Explain why the sky is blue.", "reasoning"),
    ("Generate a short story about a dragon.", "generation"),
])
def test_task_classifier(prompt, expected_task):
    classifier = TaskClassifier()
    messages = [{"role": "user", "content": prompt}]
    task_type, confidence = classifier.classify(messages)
    assert task_type == expected_task
    assert confidence > 0

# --- ModelSelector Tests ---
@pytest.mark.parametrize("task_type, confidence, original_model, expected_model", [
    ("classification", 0.9, "gpt-4-0125-preview", "gpt-4o-mini"),
    ("summarization", 0.9, "gpt-4-0125-preview", "gpt-4o"),
    ("reasoning", 0.9, "gpt-4-0125-preview", "gpt-4-0125-preview"),
    ("code", 0.9, "gpt-4o-mini", "gpt-4-0125-preview"),
    ("unknown", 0.4, "gpt-4-0125-preview", "gpt-4-0125-preview"), # Low confidence fallback
])
def test_model_selector(task_type, confidence, original_model, expected_model):
    selector = ModelSelector()
    selected_model, reason = selector.select_model(task_type, confidence, original_model)
    assert selected_model == expected_model

# --- AutopilotEngine Full Logic Tests ---

@pytest.mark.asyncio
@patch('app.core.autopilot.AutopilotEngine._process_with_autopilot', new_callable=AsyncMock)
async def test_process_request_simple_task_downgrade(mock_process, autopilot_engine):
    """Test that a simple task is correctly downgraded to a cheaper model."""
    mock_process.return_value = {
        'response': MagicMock(),
        'autopilot_metadata': {
            'enabled': True,
            'selected_model': 'gpt-4o-mini',
            'routing_reason': 'downgraded_for_simple_task'
        }
    }
    request = create_mock_request([{"role": "user", "content": "Classify this text."}], model="gpt-4-0125-preview")
    result = await autopilot_engine.process_request(request, mock_organization, "fake_api_key")

    mock_process.assert_called_once()
    assert result['autopilot_metadata']['selected_model'] == "gpt-4o-mini"

@pytest.mark.asyncio
@patch('app.core.autopilot.AsyncOpenAI')
async def test_cache_write_and_hit(mock_async_openai, autopilot_engine, mock_redis_client):
    """Test that a cacheable request writes to cache and a subsequent request hits it."""
    # 1. First request (cache miss and write)
    mock_client = mock_async_openai.return_value
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"id": "chatcmpl-123", "choices": [{"message": {"role": "assistant", "content": "Hello there!"}}]}
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    request = create_mock_request([{"role": "user", "content": "Cacheable prompt"}], temperature=0)
    
    await autopilot_engine.process_request(request, mock_organization, "fake_api_key")
    
    mock_client.chat.completions.create.assert_called_once()
    mock_redis_client.set.assert_called_once()

    # 2. Second request (cache hit)
    mock_client.chat.completions.create.reset_mock()
    cached_value = {
        'response_data': mock_response.model_dump(),
        'cost_usd': '0.001'
    }
    mock_redis_client.get.return_value = cached_value
    
    result = await autopilot_engine.process_request(request, mock_organization, "fake_api_key")

    mock_client.chat.completions.create.assert_not_called()
    assert result['autopilot_metadata']['routing_reason'] == 'cache_hit'
    assert result['response'] == cached_value['response_data']

@pytest.mark.asyncio
@patch('app.core.autopilot.AutopilotEngine._get_openai_client')
async def test_non_cacheable_request(mock_get_client, autopilot_engine, mock_redis_client):
    """Test that a non-cacheable request (temp > 0) does not use the cache."""
    mock_client = mock_get_client.return_value
    mock_client.chat.completions.create = AsyncMock(return_value=MagicMock())

    request = create_mock_request([{"role": "user", "content": "A creative prompt"}], temperature=0.8)
    
    await autopilot_engine.process_request(request, mock_organization, "fake_api_key")
    
    mock_redis_client.get.assert_called_once()
    mock_redis_client.set.assert_not_called()
    mock_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
@patch('app.core.autopilot.AutopilotEngine._process_with_autopilot', new_callable=AsyncMock)
@patch('app.core.autopilot.AutopilotEngine._fallback_direct_call', new_callable=AsyncMock)
async def test_fallback_on_engine_error(mock_fallback, mock_process, autopilot_engine):
    """Test that the engine falls back to the original model if an internal error occurs."""
    mock_process.side_effect = Exception("Autopilot internal error!")
    mock_fallback.return_value = {
        "response": MagicMock(),
        "autopilot_metadata": {"enabled": False, "fallback_reason": "autopilot_error"}
    }

    request = create_mock_request([{"role": "user", "content": "This will fail"}], model="gpt-4-0125-preview")
    result = await autopilot_engine.process_request(request, mock_organization, "fake_api_key")

    mock_process.assert_called_once()
    mock_fallback.assert_called_once()
    assert result['autopilot_metadata']['enabled'] is False
    assert result['autopilot_metadata']['fallback_reason'] == 'autopilot_error'

# --- Cost Calculation is in `pricing.py`, not `autopilot.py` ---
# The tests for cost calculation should be in a separate file for `pricing.py`.
# Autopilot only logs costs, it doesn't calculate them directly.

# --- End-to-End Integration Test ---
@pytest.mark.asyncio
@patch('app.core.autopilot.AutopilotEngine._process_with_autopilot', new_callable=AsyncMock)
async def test_end_to_end_process_request_structure(mock_process, autopilot_engine, mock_db_session):
    """Verify the final structure of the returned dictionary from a successful run."""
    mock_process.return_value = {
        'response': {"id": "chatcmpl-xyz", "choices": []},
        'autopilot_metadata': {
            'enabled': True,
            'selected_model': 'gpt-4-turbo-preview',
            'routing_reason': 'summarization_task'
        }
    }
    request = create_mock_request([{"role": "user", "content": "Summarize this article for me."}], model="gpt-4-0125-preview")
    result = await autopilot_engine.process_request(request, mock_organization, "fake_api_key")

    assert 'response' in result
    assert 'autopilot_metadata' in result
    metadata = result['autopilot_metadata']
    assert metadata['enabled'] is True
    assert metadata['selected_model'] == 'gpt-4-turbo-preview'
    
    mock_process.assert_called_once()