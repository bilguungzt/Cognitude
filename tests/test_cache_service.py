import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app import models, schemas
from app.core.cache_keys import CacheKeyBuilder
from app.services.cache_service import CacheService


@compiles(JSONB, "sqlite")
def _compile_jsonb(element, compiler, **kw):
    return "JSON"


class DummyRedisCache:
    def __init__(self):
        self.available = True
        self.redis = True
        self._data = {}

    def get(self, organization_id, request_or_key, **kwargs):
        cache_key = request_or_key if isinstance(request_or_key, str) else CacheKeyBuilder.chat_completion_key(
            organization_id,
            request_or_key,
            model_override=kwargs.get("model_override"),
            extra_metadata=kwargs.get("extra_metadata"),
        )
        entry = self._data.get(cache_key)
        return entry

    def set(self, organization_id, request_or_key, response_data, **kwargs):
        cache_key = request_or_key if isinstance(request_or_key, str) else CacheKeyBuilder.chat_completion_key(
            organization_id,
            request_or_key,
            model_override=kwargs.get("model_override"),
            extra_metadata=kwargs.get("extra_metadata"),
        )
        self._data[cache_key] = {
            "response_data": response_data,
            "provider": kwargs.get("provider"),
            "cost_usd": kwargs.get("cost_usd", 0),
        }
        return True

    def delete(self, organization_id, request_or_key, **kwargs):
        cache_key = request_or_key if isinstance(request_or_key, str) else CacheKeyBuilder.chat_completion_key(
            organization_id,
            request_or_key,
            model_override=kwargs.get("model_override"),
            extra_metadata=kwargs.get("extra_metadata"),
        )
        self._data.pop(cache_key, None)
        return 1

    def clear(self, organization_id):
        keys_to_remove = [key for key in self._data if key.startswith(f"{organization_id}:")]
        for key in keys_to_remove:
            self._data.pop(key, None)
        return len(keys_to_remove)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    org = models.Organization(name="Acme", api_key_hash="hash", api_key_digest=None)
    session.add(org)
    session.commit()
    yield session
    session.close()


def _sample_request():
    return schemas.ChatCompletionRequest(
        model="gpt-4o",
        messages=[schemas.ChatMessage(role="user", content="Hello world!")],
    )


def test_cache_key_is_deterministic():
    request = _sample_request()
    key1 = CacheKeyBuilder.chat_completion_key(1, request)
    key2 = CacheKeyBuilder.chat_completion_key(1, request)
    assert key1 == key2


def test_cache_service_round_trip(db_session):
    dummy_redis = DummyRedisCache()
    service = CacheService(dummy_redis)
    request = _sample_request()
    response_payload = {
        "id": "chatcmpl-123",
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
        "choices": [],
        "x-cognitude": {"provider": "openai", "cost": 0.01},
    }

    key = service.set_response(
        db=db_session,
        organization_id=1,
        request=request,
        response_data=response_payload,
        model="gpt-4o",
        provider="openai",
        prompt_tokens=5,
        completion_tokens=7,
        cost_usd=0.01,
    )

    cache_hit = service.get_response(db_session, 1, request)
    assert cache_hit is not None
    assert cache_hit.cache_key == key
    assert cache_hit.payload["response_data"]["id"] == "chatcmpl-123"


def test_cache_service_cache_miss(db_session):
    dummy_redis = DummyRedisCache()
    service = CacheService(dummy_redis)
    cache_hit = service.get_response(db_session, 1, _sample_request())
    assert cache_hit is None

