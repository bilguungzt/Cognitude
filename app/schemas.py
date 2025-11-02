from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import List, Optional

# ModelFeature Schemas
class ModelFeatureBase(BaseModel):
    name: str
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

# PredictionInput Schemas
class PredictionInputBase(BaseModel):
    feature_name: str
    feature_value: str

class PredictionInputCreate(PredictionInputBase):
    pass

class PredictionInput(PredictionInputBase):
    id: int
    prediction_id: UUID
    model_config = ConfigDict(from_attributes=True)

# PredictionOutput Schemas
class PredictionOutputBase(BaseModel):
    output_name: str
    output_value: str
    score: Optional[float] = None

class PredictionOutputCreate(PredictionOutputBase):
    pass

class PredictionOutput(PredictionOutputBase):
    id: int
    prediction_id: UUID
    model_config = ConfigDict(from_attributes=True)

# Prediction Schemas
class PredictionBase(BaseModel):
    status: str = "PENDING"

class PredictionCreate(BaseModel):
    model_id: int
    inputs: List[PredictionInputCreate]

class Prediction(PredictionBase):
    id: UUID
    model_id: int
    created_at: datetime
    updated_at: datetime
    inputs: List[PredictionInput] = []
    outputs: List[PredictionOutput] = []
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