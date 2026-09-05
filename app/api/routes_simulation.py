from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.weather_service import fetch_agro_weather
from app.services.simulation_engine import run_fao56_simulation
from app.models.schemas import SimulationResponse

router = APIRouter(prefix="/api/simulation", tags=["Digital Twin Simulation"])

class RunSimulationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    zone_id: str = "zone-1"
    zone_name: str = "Field 1"
    crop: str = "tomato"
    soil: str = "loam"
    area_acres: float = Field(default=25.0, gt=0.0)
    growth_stage: str = Field(default="mid", description="ini, mid, or end")
    initial_depletion_fraction: float = Field(default=0.25, ge=0.0, le=1.0)

@router.post("/run", response_model=SimulationResponse)
async def run_simulation(req: RunSimulationRequest):
    """
    Ingest hyper-local agro-weather for given coordinates and execute a 14-day
    FAO-56 Soil Water-Balance & Micro-Climate Digital Twin Simulation.
    """
    try:
        weather = await fetch_agro_weather(req.latitude, req.longitude, days=14)
        sim_result = run_fao56_simulation(
            zone_id=req.zone_id,
            zone_name=req.zone_name,
            crop_key=req.crop,
            soil_key=req.soil,
            area_acres=req.area_acres,
            growth_stage=req.growth_stage,
            weather=weather,
            initial_depletion_fraction=req.initial_depletion_fraction
        )
        return sim_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")
