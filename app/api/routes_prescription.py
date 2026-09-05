from fastapi import APIRouter
from app.models.schemas import PrescriptionRequest, PrescriptionResponse

router = APIRouter(prefix="/api/prescription", tags=["Irrigation Prescription"])

EFFICIENCY_MAP = {
    "drip": 0.90,       # Precision micro-drip
    "sprinkler": 0.75,  # Center pivot / overhead sprinkler
    "surface": 0.60     # Furrow / flood basin
}

LITERS_TO_GALLONS = 0.264172

@router.post("/calculate", response_model=PrescriptionResponse)
def calculate_prescription(req: PrescriptionRequest):
    """
    Calculate precision irrigation run-time, water volume, pumping power,
    and cost breakdown based on soil deficit and delivery system efficiency.
    """
    efficiency = EFFICIENCY_MAP.get(req.irrigation_type.lower(), 0.85)

    # Net water needed at root zone adjusted for distribution uniformity & evaporation
    gross_water_liters = req.water_deficit_liters / efficiency if efficiency > 0 else req.water_deficit_liters
    gross_water_gallons = gross_water_liters * LITERS_TO_GALLONS

    # Convert to mm depth over acreage (1 mm over 1 acre = 4046.86 liters)
    depth_mm = (gross_water_liters / req.area_acres) / 4046.86 if req.area_acres > 0 else 0.0

    # Pump flow rate in liters per hour
    flow_rate_lph = req.pump_flow_rate_lpm * 60.0
    pump_hours = gross_water_liters / flow_rate_lph if flow_rate_lph > 0 else 0.0
    pump_minutes = round(pump_hours * 60.0, 0)

    # Energy calculations
    kwh_consumed = pump_hours * req.pump_power_kw
    energy_cost = kwh_consumed * req.electricity_cost_kwh

    # Weather hold warning logic (if user provided huge rain hold)
    weather_hold = False
    weather_rec = "Clear irrigation window: Apply prescribed cycle during early morning (04:00 - 08:00) to minimize evaporative losses."

    # Pulse schedule: Split into 2 pulses if run time > 3 hours to prevent soil saturation/runoff
    schedule = []
    if pump_hours > 3.0:
        half_hrs = pump_hours / 2.0
        schedule.append({
            "pulse": "Cycle 1 (Early Morning)",
            "start_time": "04:30 AM",
            "duration_hours": round(half_hrs, 2),
            "volume_liters": round(gross_water_liters / 2.0, 0)
        })
        schedule.append({
            "pulse": "Cycle 2 (Dusk / Evening)",
            "start_time": "07:00 PM",
            "duration_hours": round(half_hrs, 2),
            "volume_liters": round(gross_water_liters / 2.0, 0)
        })
    else:
        schedule.append({
            "pulse": "Single Deep Soak Cycle",
            "start_time": "05:00 AM",
            "duration_hours": round(pump_hours, 2),
            "volume_liters": round(gross_water_liters, 0)
        })

    return PrescriptionResponse(
        zone_id=req.zone_id,
        recommended_water_liters=round(gross_water_liters, 0),
        recommended_water_gallons=round(gross_water_gallons, 0),
        recommended_water_mm=round(depth_mm, 2),
        irrigation_efficiency_pct=round(efficiency * 100.0, 1),
        pump_runtime_hours=round(pump_hours, 2),
        pump_runtime_minutes=pump_minutes,
        estimated_energy_kwh=round(kwh_consumed, 1),
        estimated_energy_cost=round(energy_cost, 2),
        weather_hold_warning=weather_hold,
        weather_recommendation=weather_rec,
        schedule_breakdown=schedule
    )
