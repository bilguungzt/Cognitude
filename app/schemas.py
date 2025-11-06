from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

# ModelFeature Schemas
class ModelFeatureBase(BaseModel):
    feature_name: str
    feature_type: str
    order: int

class ModelFeatureCreate(ModelFeatureBase):
    pass

class ModelFeature(ModelFeatureBase):
    id: int
    model_id: int
    model_config = ConfigDict(from_attributes=True)

# Model Schemas
class ModelBase(BaseModel):
    name: str
    version: str
    description: Optional[str] = None

class ModelCreate(ModelBase):
    features: List[ModelFeatureCreate]

class Model(ModelBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    features: List[ModelFeature] = []
    model_config = ConfigDict(from_attributes=True)

# Prediction Schemas
class PredictionData(BaseModel):
    features: Dict[str, Any]
    prediction_value: float
    actual_value: Optional[float] = None
    timestamp: datetime


class Prediction(BaseModel):
    id: int
    time: datetime
    model_id: int
    prediction_value: float
    actual_value: Optional[float] = None
    latency_ms: Optional[float] = None
    features: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)

# Organization Schemas
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class OrganizationWithAPIKey(Organization):
    api_key: str
