"""
Provider configuration API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
import logging
import traceback


router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/", response_model=schemas.ProviderConfig)
def create_provider(
    provider: schemas.ProviderConfigCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Create a new provider configuration.
    
    Requires API key authentication (X-API-Key header).
    """
    try:
        # create_provider_config expects (db, organization_id, provider, api_key_encrypted, enabled?, priority?)
        db_provider = crud.create_provider_config(
            db,
            organization.id,
            provider.provider,
            provider.api_key,
            provider.enabled,
            provider.priority,
        )
        return db_provider
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.ProviderConfig])
def list_providers(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    List all provider configurations for the organization.
    
    Query params:
    - enabled_only: If true, only return enabled providers
    """
    try:
        providers = crud.get_provider_configs(
            db,
            organization.id,
            enabled_only=enabled_only,
        )
        return providers
    except Exception as e:
        # Log full traceback for debugging and return a 500 with the message
        logging.error("Error listing providers: %s", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error listing providers: {str(e)}")


@router.get("/{provider_id}", response_model=schemas.ProviderConfig)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """Get a specific provider configuration."""
    providers = crud.get_provider_configs(db, organization.id)
    provider = next((p for p in providers if getattr(p, 'id', None) == provider_id), None)
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider


@router.get("/debug/whoami")
def debug_whoami(
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """Dev helper: return organization info for API key debugging."""
    return {"id": organization.id, "name": organization.name}


@router.put("/{provider_id}", response_model=schemas.ProviderConfig)
def update_provider(
    provider_id: int,
    provider_update: schemas.ProviderConfigUpdate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Update a provider configuration.
    
    Can update:
    - api_key_encrypted (new API key)
    - priority (routing priority)
    - enabled (enable/disable provider)
    """
    try:
        # update_provider_config expects (db, config_id, updates)
        updated_provider = crud.update_provider_config(
            db,
            provider_id,
            provider_update,
        )
        
        if not updated_provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        return updated_provider
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{provider_id}")
def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """Delete a provider configuration."""
    # delete_provider_config expects (db, config_id)
    success = crud.delete_provider_config(db, provider_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": "Provider deleted successfully"}
