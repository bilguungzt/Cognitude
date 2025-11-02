from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from .database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    api_key_hash = Column(String, unique=True)

    models = relationship("Model", back_populates="organization")
    alert_channels = relationship("AlertChannel", back_populates="organization")

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String, index=True)
    model_type = Column(String)
    baseline_mean = Column(Float)
    baseline_std = Column(Float)

    organization = relationship("Organization", back_populates="models")
    features = relationship("ModelFeature", back_populates="model")
    predictions = relationship("Prediction", back_populates="model")
    drift_alerts = relationship("DriftAlert", back_populates="model")

class ModelFeature(Base):
    __tablename__ = "model_features"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    feature_name = Column(String)
    feature_type = Column(String)
    order = Column(Integer)
    baseline_stats = Column(JSONB)

    model = relationship("Model", back_populates="features")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime(timezone=True), server_default=func.now())
    model_id = Column(Integer, ForeignKey("models.id"))
    prediction_value = Column(Float)
    features = Column(JSONB)

    model = relationship("Model", back_populates="predictions")

class DriftAlert(Base):
    __tablename__ = "drift_alerts"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    alert_type = Column(String)
    drift_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("Model", back_populates="drift_alerts")

class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    channel_type = Column(String)
    configuration = Column(JSONB)

    organization = relationship("Organization", back_populates="alert_channels")
