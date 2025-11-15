from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.services.encryption import encryption_service


class ProviderRepository:
    """
    Repository responsible for ProviderConfig persistence and encryption concerns.
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _encrypt_api_key(api_key: str) -> str:
        try:
            return encryption_service.encrypt(api_key)
        except Exception:
            # Fail open for development environments where encryption may be disabled
            return api_key

    def create(self, organization_id: int, data: schemas.ProviderConfigCreate) -> models.ProviderConfig:
        encrypted_key = self._encrypt_api_key(data.api_key)
        provider = models.ProviderConfig(
            organization_id=organization_id,
            provider=data.provider,
            api_key_encrypted=encrypted_key,
            enabled=data.enabled,
            priority=data.priority,
        )
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def list(self, organization_id: int, enabled_only: bool = False) -> List[models.ProviderConfig]:
        query = self.db.query(models.ProviderConfig).filter(
            models.ProviderConfig.organization_id == organization_id
        )
        if enabled_only:
            query = query.filter(models.ProviderConfig.enabled == True)  # noqa: E712
        return query.order_by(models.ProviderConfig.priority.desc()).all()

    def get(self, provider_id: int, organization_id: int) -> Optional[models.ProviderConfig]:
        return (
            self.db.query(models.ProviderConfig)
            .filter(
                models.ProviderConfig.id == provider_id,
                models.ProviderConfig.organization_id == organization_id,
            )
            .first()
        )

    def update(
        self,
        provider_id: int,
        organization_id: int,
        updates: schemas.ProviderConfigUpdate,
    ) -> Optional[models.ProviderConfig]:
        provider = self.get(provider_id, organization_id)
        if not provider:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        if "api_key" in update_data and update_data["api_key"]:
            provider.api_key_encrypted = self._encrypt_api_key(update_data.pop("api_key"))

        if "enabled" in update_data:
            provider.enabled = update_data["enabled"]
        if "priority" in update_data:
            provider.priority = update_data["priority"]

        self.db.commit()
        self.db.refresh(provider)
        return provider

    def delete(self, provider_id: int, organization_id: int) -> bool:
        provider = self.get(provider_id, organization_id)
        if not provider:
            return False
        self.db.delete(provider)
        self.db.commit()
        return True

