from typing import cast
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..security import get_db
from ..core.validation import validate_organization_name, ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/register", 
    response_model=schemas.OrganizationWithAPIKey,
    summary="Register a new organization",
    description="""
    Register a new organization and receive an API key for authentication.
    
    The API key is only shown once - store it securely! Use it in the `X-API-Key` 
    header for all subsequent requests.
    
    **Example:**
    ```bash
    curl -X POST https://api.cognitude.io/auth/register \\
      -H "Content-Type: application/json" \\
      -d '{"name": "Acme Corp"}'
    ```
    
    **Response:**
    ```json
    {
      "name": "Acme Corp",
      "id": 1,
      "api_key": "deyektwSJJ..."
    }
    ```
    """,
    responses={
        200: {
            "description": "Organization created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Acme Corp",
                        "id": 1,
                        "api_key": "abc123def456..."
                    }
                }
            }
        },
        409: {
            "description": "Organization name already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Organization name already exists."}
                }
            }
        }
    }
)
def register_organization(
    organization: schemas.OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Validate and sanitize organization name
        sanitized_name = validate_organization_name(organization.name)
        
        # Create API key
        api_key = security.create_api_key()
        hashed_api_key = security.get_password_hash(api_key)
        api_key_digest = security.compute_api_key_digest(api_key)
        
        # Create organization with sanitized name
        db_organization = crud.create_organization(
            db=db,
            organization=schemas.OrganizationCreate(name=sanitized_name),
            api_key_hash=hashed_api_key,
            api_key_digest=api_key_digest
        )
        security.invalidate_api_key_cache()
        
        logger.info(f"Organization created successfully: {sanitized_name}")
        
        return schemas.OrganizationWithAPIKey(
            id=cast(int, db_organization.id),
            name=cast(str, db_organization.name),
            api_key=api_key,
            created_at=cast(datetime, db_organization.created_at),
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error during organization registration: {e.detail}")
        raise HTTPException(
            status_code=400,
            detail=e.detail
        )
    except IntegrityError as exc:
        db.rollback()
        logger.warning(f"Organization name already exists: {organization.name}")
        raise HTTPException(
            status_code=409,
            detail="Organization name already exists.",
        ) from exc
    except Exception as e:
        logger.error(f"Unexpected error during organization registration: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the organization. Please try again."
        )
