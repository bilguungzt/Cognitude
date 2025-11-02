from sqlalchemy.orm import Session

from . import models, schemas


def get_organization_by_name(db: Session, name: str):
    return db.query(models.Organization).filter(models.Organization.name == name).first()


def get_organization_by_api_key(db: Session, api_key: str):
    return db.query(models.Organization).filter(models.Organization.api_key == api_key).first()


def create_organization(db: Session, organization: schemas.OrganizationCreate, api_key: str):
    db_organization = models.Organization(name=organization.name, api_key=api_key)
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


def create_model_for_organization(db: Session, model: schemas.ModelCreate, organization_id: int):
    db_model = models.Model(**model.model_dump(), organization_id=organization_id)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_models_by_organization(db: Session, organization_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Model).filter(models.Model.organization_id == organization_id).offset(skip).limit(limit).all()


def get_model_by_id(db: Session, model_id: int):
    return db.query(models.Model).filter(models.Model.id == model_id).first()


def create_prediction(db: Session, prediction: schemas.PredictionCreate, model_id: int):
    db_prediction = models.Prediction(**prediction.model_dump(), model_id=model_id)
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction