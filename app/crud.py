from sqlalchemy.orm import Session
from . import models, schemas

def get_organization_by_api_key_hash(db: Session, api_key_hash: str):
    return db.query(models.Organization).filter(models.Organization.api_key_hash == api_key_hash).first()

def create_organization(db: Session, organization: schemas.OrganizationCreate, api_key_hash: str):
    db_organization = models.Organization(**organization.dict(), api_key_hash=api_key_hash)
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization

def get_models(db: Session, organization_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Model).filter(models.Model.organization_id == organization_id).offset(skip).limit(limit).all()

def create_model(db: Session, model: schemas.ModelCreate, organization_id: int):
    db_model = models.Model(**model.dict(), organization_id=organization_id)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def create_prediction(db: Session, prediction: schemas.PredictionCreate, model_id: int):
    db_prediction = models.Prediction(**prediction.dict(), model_id=model_id)
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction

def get_latest_predictions(db: Session, model_id: int, limit: int = 100):
    return db.query(models.Prediction).filter(models.Prediction.model_id == model_id).order_by(models.Prediction.timestamp.desc()).limit(limit).all()