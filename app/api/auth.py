from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..security import get_db

router = APIRouter()


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
    curl -X POST http://localhost:8000/auth/register \\
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
    organization: schemas.OrganizationCreate, db: Session = Depends(get_db)
):
    api_key = security.create_api_key()
    hashed_api_key = security.get_password_hash(api_key)
    try:
        db_organization = crud.create_organization(
            db=db, organization=organization, api_key_hash=hashed_api_key
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Organization name already exists.",
        ) from exc
    else:
        return schemas.OrganizationWithAPIKey(
            id=cast(int, db_organization.id),
            name=cast(str, db_organization.name),
            api_key=api_key,
        )
