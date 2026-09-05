from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

class Coordinate(BaseModel):
    lat: float
    lng: float

class ZoneBase(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., examples=["North Field"])
    crop: str = Field(default="tomato", examples=["tomato"])
    soil: str = Field(default="loam", examples=["loam"])
    area_acres: float = Field(default=20.0, ge=0.1, le=10000.0)
    growth_stage: str = Field(default="mid", description="ini, mid, or end")
    irrigation_type: str = Field(default="drip", description="drip, sprinkler, or surface")
    coordinates: List[List[float]] = Field(default_factory=list, description="List of [lat, lng] pairs forming polygon")

class ZoneCreate(ZoneBase):
    pass

class ZoneResponse(ZoneBase):
    id: str
    crop_name: Optional[str] = None
    soil_name: Optional[str] = None
    color: Optional[str] = None

class FarmProfile(BaseModel):
    id: str
    name: str
    location_name: str
    latitude: float
    longitude: float
    total_area_acres: float
    default_soil: str
    zones: List[ZoneResponse]

class WeatherDaily(BaseModel):
    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_sum_mm: float
    et0_mm: float
    solar_radiation_mj: float
    soil_temp_avg_c: float
    soil_moisture_vol: float
    vpd_kpa: float

class WeatherForecastResponse(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float
    timezone: str
    daily: List[WeatherDaily]
    is_live_data: bool

class DailySimulationResult(BaseModel):
    date: str
    day_index: int
    kc: float
    et0_mm: float
    etc_mm: float
    precipitation_mm: float
    irrigation_applied_mm: float
    root_zone_depletion_mm: float
    taw_mm: float
    raw_mm: float
    soil_moisture_pct: float
    stress_coefficient_ks: float
    stress_status: str  # OPTIMAL, MILD_STRESS, CRITICAL_DROUGHT, WATERLOGGED
    simulated_ndvi: float
    temperature_c: float
    vpd_kpa: float
    deficit_liters_per_acre: float

class SimulationSummary(BaseModel):
    total_et0_mm: float
    total_etc_mm: float
    total_rain_mm: float
    current_moisture_pct: float
    current_status: str
    days_until_critical_stress: int
    recommended_irrigation_date: Optional[str]
    total_water_deficit_liters: float

class SimulationResponse(BaseModel):
    zone_id: str
    zone_name: str
    crop: str
    soil: str
    area_acres: float
    daily_results: List[DailySimulationResult]
    summary: SimulationSummary

class PrescriptionRequest(BaseModel):
    zone_id: str
    water_deficit_liters: float
    area_acres: float
    irrigation_type: str = "drip"  # drip (90%), sprinkler (75%), surface (60%)
    pump_flow_rate_lpm: float = 350.0  # liters per minute
    electricity_cost_kwh: float = 0.14  # USD/kWh or local currency
    pump_power_kw: float = 7.5  # kW motor rating

class PrescriptionResponse(BaseModel):
    zone_id: str
    recommended_water_liters: float
    recommended_water_gallons: float
    recommended_water_mm: float
    irrigation_efficiency_pct: float
    pump_runtime_hours: float
    pump_runtime_minutes: float
    estimated_energy_kwh: float
    estimated_energy_cost: float
    weather_hold_warning: bool
    weather_recommendation: str
    schedule_breakdown: List[Dict[str, Any]]

class AgronomicRisk(BaseModel):
    category: str
    severity: str  # CRITICAL, WARNING, INFO
    title: str
    description: str
    remediation: str

class AdvisorChatRequest(BaseModel):
    message: str
    zone_id: Optional[str] = None
    farm_id: Optional[str] = None
    simulation_context: Optional[Dict[str, Any]] = None

class AdvisorChatResponse(BaseModel):
    reply: str
    risks: List[AgronomicRisk]
    action_items: List[str]
    source: str  # AI_MODEL or AGRONOMIC_EXPERT_ENGINE
