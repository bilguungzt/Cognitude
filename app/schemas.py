from datetime import datetime
from pydantic import BaseModel, ConfigDict

# Organization Schemas
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrganizationWithAPIKey(Organization):
    api_key: str

# Model Schemas
class ModelBase(BaseModel):
    name: str
    model_type: str
    baseline_mean: float
    baseline_std: float

class ModelCreate(ModelBase):
    pass

class Model(ModelBase):
    id: int
    organization_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Prediction Schemas
class PredictionBase(BaseModel):
    prediction_value: float
    features: dict

class PredictionCreate(PredictionBase):
    pass

class Prediction(PredictionBase):
    time: datetime
    model_id: int
    model_config = ConfigDict(from_attributes=True)

# ModelFeature Schemas
class ModelFeatureBase(BaseModel):
    name: str
    feature_type: str

class ModelFeatureCreate(ModelFeatureBase):
    pass

class ModelFeature(ModelFeatureBase):
    id: int
    model_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# DriftAlert Schemas
class DriftAlertBase(BaseModel):
    alert_type: str
    message: str
    details: dict

class DriftAlertCreate(DriftAlertBase):
    pass

class DriftAlert(DriftAlertBase):
    id: int
    model_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# AlertChannel Schemas
class AlertChannelBase(BaseModel):
    channel_type: str
    configuration: dict

class AlertChannelCreate(AlertChannelBase):
    pass

class AlertChannel(AlertChannelBase):
    id: int
    organization_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)