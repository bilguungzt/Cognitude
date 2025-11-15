"""
Provider configuration API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..repositories.provider_repository import ProviderRepository
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
        # Validate provider configuration
        if not provider.provider or not provider.api_key:
            raise ValueError("Provider name and API key are required")
            
        # create_provider_config expects (db, organization_id, provider, api_key_encrypted, enabled?, priority?)
        repo = ProviderRepository(db)
        return repo.create(organization.id, provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the error but don't expose internal details
        logging.error(f"Error creating provider config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create provider configuration")


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
        repo = ProviderRepository(db)
        return repo.list(organization.id, enabled_only=enabled_only)
    except Exception as e:
        # Log full traceback for debugging and return a 500 with the message
        logging.error("Error listing providers: %s", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Server error listing providers. Please try again later.")


@router.get("/{provider_id}", response_model=schemas.ProviderConfig)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """Get a specific provider configuration."""
    repo = ProviderRepository(db)
    provider = repo.get(provider_id, organization.id)

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider


# Debug endpoint removed for security - avoid exposing organization details
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
        repo = ProviderRepository(db)
        updated = repo.update(provider_id, organization.id, provider_update)
        if not updated:
            raise HTTPException(status_code=404, detail="Provider not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{provider_id}")
def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """Delete a provider configuration."""
    repo = ProviderRepository(db)
    success = repo.delete(provider_id, organization.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": "Provider deleted successfully"}


@router.post("/test", response_model=dict)
def test_provider_connection(
    provider: schemas.ProviderConfigCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Test connection to a provider API.
    
    This endpoint validates that the provided API key works with the specified provider.
    It does not save the provider configuration.
    
    Requires API key authentication (X-API-Key header).
    """
    try:
        from ..services.router import ProviderRouter
        
        # Validate provider configuration
        if not provider.provider or not provider.api_key:
            raise HTTPException(status_code=400, detail="Provider name and API key are required")
        
        # Create a temporary router to test the connection
        router = ProviderRouter(db, organization.id)
        
        # Test with a simple message
        test_messages = [{"role": "user", "content": "Hello, this is a test message."}]
        
        # Determine appropriate model for testing
        # Use modern, commonly-available test models by default
        test_model = "gpt-4o-mini"  # default modern OpenAI-compatible model
        if provider.provider == "anthropic":
            test_model = "claude-3-haiku-20240307"
        elif provider.provider == "google":
            test_model = "gemini-flash"
        elif provider.provider == "groq":
            test_model = "llama-3.1-70b-versatile"
        
        # Try to make a test call
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                router.test_provider_connection(
                    provider.provider,
                    provider.api_key,
                    test_model,
                    test_messages,
                    max_tokens=50,
                    temperature=0
                )
            )
            
            return {
                "success": True,
                "message": "Connection test successful",
                "provider": provider.provider,
                "model": test_model,
                "response": result["choices"][0]["message"]["content"][:100] + "..." if len(result["choices"][0]["message"]["content"]) > 100 else result["choices"][0]["message"]["content"]
            }
            
        except Exception as test_error:
            raise HTTPException(
                status_code=400, 
                detail=f"Connection test failed: {str(test_error)}"
            )
        finally:
            loop.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error testing provider connection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test provider connection")
