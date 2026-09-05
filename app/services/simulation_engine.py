from typing import List, Dict, Any, Optional
from app.config import SOIL_PROPERTIES, CROP_PROPERTIES
from app.models.schemas import (
    WeatherForecastResponse,
    DailySimulationResult,
    SimulationResponse,
    SimulationSummary
)

LITERS_PER_MM_PER_ACRE = 4046.86  # 1 mm water depth over 1 acre = 4,046.86 liters

def run_fao56_simulation(
    zone_id: str,
    zone_name: str,
    crop_key: str,
    soil_key: str,
    area_acres: float,
    growth_stage: str,
    weather: WeatherForecastResponse,
    initial_depletion_fraction: float = 0.20
) -> SimulationResponse:
    """
    Execute standard FAO-56 Root Zone Soil Water-Balance Simulation over the weather forecast window.
    Computes TAW, RAW, daily depletion Dr, stress coefficient Ks, and crop evapotranspiration ETc.
    """
    soil_info = SOIL_PROPERTIES.get(soil_key, SOIL_PROPERTIES["loam"])
    crop_info = CROP_PROPERTIES.get(crop_key, CROP_PROPERTIES["tomato"])

    fc = soil_info["fc"]
    wp = soil_info["wp"]
    sat = soil_info["sat"]
    zr = crop_info["root_depth_m"]
    p_baseline = crop_info["depletion_fraction_p"]

    # Crop coefficient Kc based on growth stage
    if growth_stage == "ini":
        kc = crop_info["kc_ini"]
    elif growth_stage == "end":
        kc = crop_info["kc_end"]
    else:
        kc = crop_info["kc_mid"]

    # 1. Total Available Water (TAW) in root zone (mm)
    # TAW = 1000 * (FC - WP) * Zr
    taw_mm = round(1000.0 * (fc - wp) * zr, 1)

    # 2. Adjusted depletion fraction p for high ET0 (FAO-56 Eq. 89)
    # p = p_baseline + 0.04 * (5 - ET0)
    # Readily Available Water (RAW) in root zone (mm)
    # RAW = p * TAW
    daily_results: List[DailySimulationResult] = []

    # Initial root zone depletion Dr (mm)
    dr = initial_depletion_fraction * taw_mm

    total_et0 = 0.0
    total_etc = 0.0
    total_rain = 0.0
    days_until_critical = -1
    recommended_date = None

    for i, day in enumerate(weather.daily):
        et0 = day.et0_mm
        rain = day.precipitation_sum_mm

        # Adjust p for current ET0
        p_adj = max(0.1, min(0.8, p_baseline + 0.04 * (5.0 - et0)))
        raw_mm = round(p_adj * taw_mm, 1)

        # 3. Calculate Water Stress Coefficient Ks
        if dr <= raw_mm:
            ks = 1.0
        elif dr < taw_mm:
            ks = max(0.0, min(1.0, (taw_mm - dr) / ((1.0 - p_adj) * taw_mm)))
        else:
            ks = 0.0

        # 4. Actual Crop Evapotranspiration ETc (mm/day)
        etc = round(ks * kc * et0, 2)

        # 5. Effective rainfall (FAO approximation: 80% if rain > 5mm, else 0 if very light)
        eff_rain = max(0.0, rain * 0.85) if rain >= 3.0 else 0.0

        # 6. Water Balance Update for the end of the day:
        # Dr_new = Dr_prev - Eff_Rain + ETc
        dr = max(0.0, min(taw_mm, dr - eff_rain + etc))

        # Current volumetric soil moisture theta (m3/m3)
        theta = fc - (dr / (1000.0 * zr))
        moisture_pct = round(max(wp * 0.8, min(sat, theta)) * 100.0, 1)

        # 7. Stress Status Classification
        if theta > (fc + 0.03):
            status = "WATERLOGGED"
        elif dr <= raw_mm:
            status = "OPTIMAL"
        elif dr <= (0.85 * taw_mm):
            status = "MILD_STRESS"
        else:
            status = "CRITICAL_DROUGHT"
            if days_until_critical == -1:
                days_until_critical = i

        # Track first recommended irrigation trigger (when Dr reaches 90% of RAW)
        if dr >= (0.90 * raw_mm) and recommended_date is None:
            recommended_date = day.date

        # 8. Simulated NDVI
        # Mid-growth NDVI baseline ~0.82, reduced by moisture stress Ks
        base_ndvi = 0.82 if growth_stage == "mid" else (0.55 if growth_stage == "ini" else 0.70)
        simulated_ndvi = round(base_ndvi * (0.65 + 0.35 * ks), 3)

        # Deficit water needed in liters per acre
        deficit_liters_per_acre = round(dr * LITERS_PER_MM_PER_ACRE, 0)

        total_et0 += et0
        total_etc += etc
        total_rain += rain

        daily_results.append(
            DailySimulationResult(
                date=day.date,
                day_index=i,
                kc=round(kc, 2),
                et0_mm=et0,
                etc_mm=etc,
                precipitation_mm=rain,
                irrigation_applied_mm=0.0,
                root_zone_depletion_mm=round(dr, 1),
                taw_mm=taw_mm,
                raw_mm=raw_mm,
                soil_moisture_pct=moisture_pct,
                stress_coefficient_ks=round(ks, 2),
                stress_status=status,
                simulated_ndvi=simulated_ndvi,
                temperature_c=round((day.temp_max_c + day.temp_min_c) / 2.0, 1),
                vpd_kpa=day.vpd_kpa,
                deficit_liters_per_acre=deficit_liters_per_acre
            )
        )

    # Current snapshot (day 0)
    current_day = daily_results[0]
    total_water_deficit = round(current_day.root_zone_depletion_mm * LITERS_PER_MM_PER_ACRE * area_acres, 0)

    summary = SimulationSummary(
        total_et0_mm=round(total_et0, 1),
        total_etc_mm=round(total_etc, 1),
        total_rain_mm=round(total_rain, 1),
        current_moisture_pct=current_day.soil_moisture_pct,
        current_status=current_day.stress_status,
        days_until_critical_stress=days_until_critical if days_until_critical != -1 else 14,
        recommended_irrigation_date=recommended_date or weather.daily[-1].date,
        total_water_deficit_liters=total_water_deficit
    )

    return SimulationResponse(
        zone_id=zone_id,
        zone_name=zone_name,
        crop=crop_info["name"],
        soil=soil_info["name"],
        area_acres=area_acres,
        daily_results=daily_results,
        summary=summary
    )
