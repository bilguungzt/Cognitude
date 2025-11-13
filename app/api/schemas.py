from typing import List, cast
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db
from app.security import get_organization_from_api_key
from app.core.schema_enforcer import validate_user_schema

router = APIRouter(prefix="/schemas", tags=["schemas"])

@router.post("/upload", response_model=schemas.ResponseMessage)
def upload_schema(
    schema_in: schemas.SchemaCreate,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key)
):
    """
    Upload and validate a new JSON schema.
    """
    try:
        validate_user_schema(schema_in.schema_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db_schema = crud.create_schema(db, name=schema_in.name, schema_data=schema_in.schema_data, organization_id=cast(int, organization.id))
    return {"message": f"Schema '{db_schema.name}' uploaded successfully"}

@router.get("/active", response_model=List[schemas.SchemaStat])
def get_active_schemas(
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key)
):
    """
    Get active schemas with statistics.
    """
    print("get_active_schemas endpoint called")
    # This should call a function that returns schema statistics
    return crud.get_schema_stats(db, organization_id=cast(int, organization.id))

@router.get("/validation-logs/failed", response_model=List[schemas.SchemaValidationLog])
def get_failed_validation_logs(
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key)
):
    """
    Get failed validation logs.
    """
    return crud.get_failed_validation_logs(db, organization_id=cast(int, organization.id))