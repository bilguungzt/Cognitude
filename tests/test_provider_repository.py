from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app import models, schemas
from app.repositories.provider_repository import ProviderRepository


@compiles(JSONB, "sqlite")
def _compile_jsonb(element, compiler, **kw):
    return "JSON"


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


@pytest.fixture
def repo(db_session):
    return ProviderRepository(db_session)


def _provider_payload():
    return schemas.ProviderConfigCreate(
        provider="openai",
        api_key="secret-key",
        enabled=True,
        priority=10,
    )


@patch("app.repositories.provider_repository.encryption_service")
def test_repository_create_encrypts_api_key(mock_encryption, repo, db_session):
    mock_encryption.encrypt.side_effect = lambda value: f"enc::{value}"

    provider = repo.create(organization_id=1, data=_provider_payload())
    assert provider.id is not None
    assert provider.api_key_encrypted == "enc::secret-key"


@patch("app.repositories.provider_repository.encryption_service")
def test_repository_update_handles_api_key_rotation(mock_encryption, repo, db_session):
    mock_encryption.encrypt.side_effect = lambda value: f"enc::{value}"
    provider = repo.create(organization_id=1, data=_provider_payload())

    update_payload = schemas.ProviderConfigUpdate(
        api_key="new-secret",
        priority=5,
        enabled=False,
    )
    updated = repo.update(provider.id, 1, update_payload)
    assert updated.priority == 5
    assert updated.enabled is False
    assert updated.api_key_encrypted == "enc::new-secret"


def test_repository_delete(repo):
    provider = repo.create(organization_id=1, data=_provider_payload())
    assert repo.delete(provider.id, 1) is True
    assert repo.delete(provider.id, 1) is False

