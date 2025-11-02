from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMPTZ
from sqlalchemy.sql import func

from .database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    models = relationship("Model", back_populates="organization")
    alert_channels = relationship("AlertChannel", back_populates="organization")

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)
    baseline_mean = Column(Float)
    baseline_std = Column(Float)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="models")
    features = relationship("ModelFeature", back_populates="model")
    predictions = relationship("Prediction", back_populates="model")
    alerts = relationship("DriftAlert", back_populates="model")

class ModelFeature(Base):
    __tablename__ = "model_features"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    feature_name = Column(String, nullable=False)
    feature_type = Column(String, nullable=False)
    baseline_stats = Column(JSONB)

    model = relationship("Model", back_populates="features")

class Prediction(Base):
    __tablename__ = "predictions"

    time = Column(TIMESTAMPTZ, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), primary_key=True)
    prediction_value = Column(Float)
    features = Column(JSONB)

    model = relationship("Model", back_populates="predictions")

class DriftAlert(Base):
    __tablename__ = "drift_alerts"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    alert_type = Column(String, nullable=False)
    drift_score = Column(Float)
    triggered_at = Column(DateTime, server_default=func.now(), nullable=False)

    model = relationship("Model", back_populates="alerts")

class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    channel_type = Column(String, nullable=False)
    configuration = Column(JSONB)

    organization = relationship("Organization", back_populates="alert_channels")