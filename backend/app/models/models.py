"""
FloodGuard AI — SQLAlchemy ORM models.

NO sensor/IoT tables. Domain entities: users, zones, weather observations &
forecasts, predictions, alerts, flood events, emergency resources.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(32), default="citizen", nullable=False)  # citizen | operator | admin
    created_at = Column(DateTime, default=_utcnow)

    alerts = relationship("Alert", back_populates="acknowledged_by_user")
    saved_locations = relationship("SavedLocation", back_populates="user", cascade="all, delete-orphan")
    alert_subscriptions = relationship("AlertSubscription", back_populates="user", cascade="all, delete-orphan")


class SavedLocation(Base):
    __tablename__ = "saved_locations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), index=True, nullable=False)
    label = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    user = relationship("User", back_populates="saved_locations")


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), index=True, nullable=False)
    risk_threshold = Column(String(16), default="HIGH", nullable=False)
    channels = Column(String(64), default="in_app", nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    user = relationship("User", back_populates="alert_subscriptions")


class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, default=0.0)
    slope = Column(Float, default=0.0)
    drainage_capacity = Column(Float, default=0.0)
    impervious_surface = Column(Float, default=0.0)
    population = Column(Integer, default=0)
    population_density = Column(Float, default=0.0)
    historical_flood_frequency = Column(Integer, default=0)

    predictions = relationship("Prediction", back_populates="zone")
    alerts = relationship("Alert", back_populates="zone")


class WeatherObservation(Base):
    __tablename__ = "weather_observations"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(32), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_at = Column(DateTime, default=_utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    precipitation = Column(Float)
    source = Column(String(32), default="openmeteo")  # provider name
    __table_args__ = (Index("ix_weather_observation_zone_observed", "zone_id", "observed_at"),)


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(32), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    forecast_at = Column(DateTime, default=_utcnow)
    time = Column(DateTime, nullable=False)
    precipitation = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    source = Column(String(32), default="openmeteo")
    __table_args__ = (Index("ix_weather_forecast_zone_time", "zone_id", "time"),)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), index=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    probability = Column(Float, nullable=False)        # 0..100
    risk = Column(String(16), nullable=False)          # LOW..CRITICAL
    is_demo = Column(Boolean, default=False)
    zone = relationship("Zone", back_populates="predictions")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(40), unique=True, index=True, nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), index=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    probability = Column(Float)
    risk = Column(String(16))
    forecast_rainfall_3h = Column(Float)
    reason = Column(Text)
    recommendation = Column(Text)
    status = Column(String(16), default="active")      # active | acknowledged
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_user = relationship("User", back_populates="alerts")
    zone = relationship("Zone", back_populates="alerts")
    __table_args__ = (Index("ix_alert_zone_status", "zone_id", "status"),)


class FloodEvent(Base):
    __tablename__ = "flood_events"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(32), index=True, nullable=False)
    occurred_at = Column(DateTime, default=_utcnow)
    severity = Column(String(16))
    description = Column(Text)
    source = Column(String(32))


class EmergencyResource(Base):
    __tablename__ = "emergency_resources"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(32), index=True, nullable=False)
    name = Column(String(128), nullable=False)
    kind = Column(String(32))              # shelter | pump | medical | boat
    capacity = Column(Integer)
    available = Column(Boolean, default=True)
