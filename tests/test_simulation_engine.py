import pytest
from app.services.simulation_engine import run_fao56_simulation
from app.models.schemas import WeatherForecastResponse, WeatherDaily

def create_mock_weather(days=14, rain_day=5, rain_amount=12.0):
    daily = []
    for i in range(days):
        rain = rain_amount if i == rain_day else 0.0
        daily.append(
            WeatherDaily(
                date=f"2026-09-{i+1:02d}",
                temp_max_c=28.0,
                temp_min_c=16.0,
                precipitation_sum_mm=rain,
                et0_mm=4.5,
                solar_radiation_mj=22.0,
                soil_temp_avg_c=20.0,
                soil_moisture_vol=0.25,
                vpd_kpa=1.3
            )
        )
    return WeatherForecastResponse(
        latitude=36.67,
        longitude=-121.65,
        elevation_m=50.0,
        timezone="UTC",
        daily=daily,
        is_live_data=False
    )

def test_fao56_taw_and_raw_calculation():
    """Verify that TAW and RAW match FAO-56 hydrological formulas."""
    weather = create_mock_weather(days=7)
    res = run_fao56_simulation(
        zone_id="test-zone",
        zone_name="Test Block",
        crop_key="tomato",
        soil_key="loam",
        area_acres=10.0,
        growth_stage="mid",
        weather=weather,
        initial_depletion_fraction=0.1
    )

    day0 = res.daily_results[0]
    # Loam: FC=0.28, WP=0.14 -> FC-WP = 0.14. Tomato Zr = 0.70m
    # Expected TAW = 1000 * 0.14 * 0.70 = 98.0 mm
    assert abs(day0.taw_mm - 98.0) < 1.0
    # Tomato baseline p = 0.40 -> RAW approx 0.40 * 98 = 39.2 mm
    assert 30.0 <= day0.raw_mm <= 50.0

def test_water_stress_coefficient_drops_under_drought():
    """Verify that when depletion exceeds RAW, Ks decreases below 1.0."""
    weather = create_mock_weather(days=14, rain_day=-1)  # Zero rain
    res = run_fao56_simulation(
        zone_id="test-drought",
        zone_name="Dry Block",
        crop_key="lettuce",  # Shallow roots Zr=0.3m, small TAW
        soil_key="sandy_loam",  # Low water holding capacity
        area_acres=5.0,
        growth_stage="mid",
        weather=weather,
        initial_depletion_fraction=0.60
    )

    # By the end of 14 days without rain on sandy loam, Ks should drop significantly
    last_day = res.daily_results[-1]
    assert last_day.stress_coefficient_ks < 1.0
    assert last_day.stress_status in ("MILD_STRESS", "CRITICAL_DROUGHT")

def test_rainfall_reduces_depletion():
    """Verify that rainfall replenishes the root zone and reduces Dr."""
    weather = create_mock_weather(days=7, rain_day=3, rain_amount=20.0)
    res = run_fao56_simulation(
        zone_id="test-rain",
        zone_name="Rain Block",
        crop_key="maize",
        soil_key="loam",
        area_acres=20.0,
        growth_stage="mid",
        weather=weather,
        initial_depletion_fraction=0.50
    )

    day_before_rain = res.daily_results[2]
    day_of_rain = res.daily_results[3]
    # After effective rain, Dr should drop compared to the day before
    assert day_of_rain.root_zone_depletion_mm < day_before_rain.root_zone_depletion_mm
