from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
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
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String)
    model_type = Column(String)
    baseline_mean = Column(Float)
    baseline_std = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization", back_populates="models")
    features = relationship(
        "ModelFeature",
        back_populates="model",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    predictions = relationship("Prediction", back_populates="model")
    drift_alerts = relationship("DriftAlert", back_populates="model")

class ModelFeature(Base):
    __tablename__ = "model_features"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String)
    feature_type = Column(String)
    order = Column(Integer)
    baseline_stats = Column(JSONB, nullable=True)

    model = relationship("Model", back_populates="features")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    prediction_value = Column(Float, nullable=False)
    actual_value = Column(Float)
    latency_ms = Column(Float)
    features = Column(JSONB, nullable=False)

    model = relationship("Model", back_populates="predictions")

class DriftAlert(Base):
    __tablename__ = "drift_alerts"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    alert_type = Column(String)
    drift_score = Column(Float)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("Model", back_populates="drift_alerts")

class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    channel_type = Column(String)
    configuration = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="alert_channels")
