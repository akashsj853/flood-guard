"""
FloodGuard AI — Pydantic request/response schemas.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# --- Weather ---------------------------------------------------------------
class CurrentWeather(BaseModel):
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    precipitation: float
    timestamp: Optional[str] = None


class ForecastHour(BaseModel):
    time: str
    precipitation: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None


class WeatherResponse(BaseModel):
    source: str = "openmeteo"
    is_demo: bool = False
    current: CurrentWeather
    forecast: list[ForecastHour] = []


# --- Zones -----------------------------------------------------------------
class ZoneBase(BaseModel):
    zone_id: str
    name: str
    latitude: float
    longitude: float
    elevation: float = 0.0
    slope: float = 0.0
    drainage_capacity: float = 0.0
    impervious_surface: float = 0.0
    population: int = 0
    population_density: float = 0.0
    historical_flood_frequency: int = 0


# --- Auth ------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = "citizen"


class AdminRegisterRequest(RegisterRequest):
    pass


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: str


class AuthResponse(BaseModel):
    user: UserResponse
    message: str = "Authenticated"


class SavedLocationRequest(BaseModel):
    zone_id: str
    label: str = Field(min_length=1, max_length=64)


class SubscriptionRequest(BaseModel):
    zone_id: str
    risk_threshold: str = "HIGH"
    channels: list[str] = ["in_app"]


class HistoryPoint(BaseModel):
    timestamp: str
    probability: float
    risk: str
    is_demo: bool = False


# --- Prediction ------------------------------------------------------------
class PredictionRequest(BaseModel):
    zone_id: str
    scenario: Optional[dict] = None  # What-If adjustments


class BulkPredictionRequest(BaseModel):
    zone_ids: list[str] = Field(min_length=1, max_length=100)
    scenario: Optional[dict] = None


class RiskFactor(BaseModel):
    feature: str
    label: str
    emoji: str
    impact: str          # HIGH | MEDIUM | LOW
    contribution: float  # signed SHAP-ish value (0..1 magnitude normalised)


class PredictionResponse(BaseModel):
    zone_id: str
    zone_name: str
    probability: float
    risk: str
    forecast: dict = Field(default_factory=dict)  # NOW/+1h/+3h/+6h
    risk_factors: list[RiskFactor] = []
    explanation: list[str] = []
    population_exposure_estimate: float = 0.0
    is_demo: bool = False


class ZonePrediction(BaseModel):
    zone_id: str
    zone_name: str
    probability: float
    risk: str
    population_exposure_estimate: float = 0.0


class AllZonesResponse(BaseModel):
    is_demo: bool = False
    zones: list[ZonePrediction] = []


# --- Alerts ----------------------------------------------------------------
class AlertResponse(BaseModel):
    alert_id: str
    zone_id: str
    zone_name: Optional[str] = None
    created_at: str
    probability: Optional[float] = None
    risk: Optional[str] = None
    forecast_rainfall_3h: Optional[float] = None
    reason: Optional[str] = None
    recommendation: Optional[str] = None
    status: str
    risk_level: Optional[str] = None
    acknowledged: bool = False


class AcknowledgeResponse(BaseModel):
    alert_id: str
    status: str


# --- Simulation ------------------------------------------------------------
class SimulationRequest(BaseModel):
    zone_id: str
    adjustments: dict = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    zone_id: str
    zone_name: str
    baseline_probability: float
    baseline_risk: str
    scenario_probability: float
    scenario_risk: str
    delta: float
    risk_factors: list[RiskFactor] = []
    explanation: list[str] = []


# --- Analytics -------------------------------------------------------------
class AnalyticsResponse(BaseModel):
    rainfall_last_24h: list[dict] = []
    forecast_next_12h: list[dict] = []
    zone_distribution: dict = {}
    risk_trend: dict = {}
    model_performance: dict = {}
