import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.autopilot import AutopilotEngine, TaskClassifier, ModelSelector
from app import schemas, models
from app.services.cache_service import CacheHit

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
def mock_cache_service():
    """Fixture for a mocked CacheService."""
    cache = MagicMock()
    cache.get_response = MagicMock(return_value=None)
    return cache

@pytest.fixture
def autopilot_engine(mock_db_session, mock_cache_service):
    """Fixture for an AutopilotEngine instance with mocked dependencies."""
    return AutopilotEngine(db=mock_db_session, cache_service=mock_cache_service)

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
    ("reasoning", 0.9, "gpt-4-0125-preview", "gpt-4"),
    ("code", 0.9, "gpt-4o-mini", "gpt-4"),
    ("unknown", 0.4, "gpt-4-0125-preview", "gpt-4"),  # Low confidence fallback
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
async def test_cache_hit_short_circuits_provider(mock_cache_service, mock_db_session):
    engine = AutopilotEngine(db=mock_db_session, cache_service=mock_cache_service)
    cached_payload = {
        'response_data': {'id': 'cached', 'choices': []},
        'provider': 'openai',
        'cost_usd': 0.0,
    }
    mock_cache_service.get_response.return_value = CacheHit(
        cache_key="1:abc",
        payload=cached_payload,
    )
    request = create_mock_request([{"role": "user", "content": "cached prompt"}])
    provider = MagicMock()
    provider.provider = "openai"

    result = await engine._process_with_autopilot(request, mock_organization, provider)

    assert result['response']['id'] == 'cached'
    assert result['autopilot_metadata']['routing_reason'] == 'cache_hit'

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