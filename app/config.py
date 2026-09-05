import os
from typing import Dict, Any
from functools import lru_cache

class Settings:
    PROJECT_NAME: str = "FarmTwin"
    PROJECT_DESCRIPTION: str = "Precision Agriculture Digital Twin & Micro-Climate Simulator"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# USDA Soil Physical Hydrological Properties
# FC: Field Capacity (m3/m3), WP: Wilting Point (m3/m3), SAT: Saturation (m3/m3)
SOIL_PROPERTIES: Dict[str, Dict[str, float]] = {
    "sandy_loam": {
        "name": "Sandy Loam",
        "fc": 0.18,
        "wp": 0.08,
        "sat": 0.43,
        "infiltration_rate_mm_hr": 25.0,
        "description": "Fast draining, low water retention. Requires frequent light irrigation."
    },
    "loam": {
        "name": "Loam",
        "fc": 0.28,
        "wp": 0.14,
        "sat": 0.47,
        "infiltration_rate_mm_hr": 13.0,
        "description": "Ideal agricultural soil. Balanced water retention and aeration."
    },
    "silt_loam": {
        "name": "Silt Loam",
        "fc": 0.31,
        "wp": 0.13,
        "sat": 0.50,
        "infiltration_rate_mm_hr": 10.0,
        "description": "High water holding capacity, fertile and smooth textured."
    },
    "clay_loam": {
        "name": "Clay Loam",
        "fc": 0.36,
        "wp": 0.22,
        "sat": 0.51,
        "infiltration_rate_mm_hr": 8.0,
        "description": "Moderately heavy soil, excellent nutrient retention, moderate drainage."
    },
    "clay": {
        "name": "Clay Soil",
        "fc": 0.40,
        "wp": 0.27,
        "sat": 0.53,
        "infiltration_rate_mm_hr": 3.0,
        "description": "Dense, high water retention. Prone to waterlogging and compaction."
    }
}

# FAO-56 Crop Coefficients & Agronomic Characteristics
CROP_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "tomato": {
        "name": "Tomato (Solanum lycopersicum)",
        "kc_ini": 0.60,
        "kc_mid": 1.15,
        "kc_end": 0.80,
        "root_depth_m": 0.70,
        "depletion_fraction_p": 0.40,
        "optimal_temp_c": (18.0, 27.0),
        "vpd_stress_threshold_kpa": 1.8,
        "color": "#ef4444"
    },
    "maize": {
        "name": "Maize / Corn (Zea mays)",
        "kc_ini": 0.30,
        "kc_mid": 1.20,
        "kc_end": 0.50,
        "root_depth_m": 1.00,
        "depletion_fraction_p": 0.55,
        "optimal_temp_c": (20.0, 30.0),
        "vpd_stress_threshold_kpa": 2.2,
        "color": "#eab308"
    },
    "wheat": {
        "name": "Wheat (Triticum aestivum)",
        "kc_ini": 0.30,
        "kc_mid": 1.15,
        "kc_end": 0.30,
        "root_depth_m": 0.90,
        "depletion_fraction_p": 0.55,
        "optimal_temp_c": (15.0, 24.0),
        "vpd_stress_threshold_kpa": 2.0,
        "color": "#f59e0b"
    },
    "grapevine": {
        "name": "Grapevine (Vitis vinifera)",
        "kc_ini": 0.30,
        "kc_mid": 0.85,
        "kc_end": 0.45,
        "root_depth_m": 1.30,
        "depletion_fraction_p": 0.45,
        "optimal_temp_c": (16.0, 28.0),
        "vpd_stress_threshold_kpa": 2.5,
        "color": "#8b5cf6"
    },
    "olive": {
        "name": "Olive Tree (Olea europaea)",
        "kc_ini": 0.65,
        "kc_mid": 0.70,
        "kc_end": 0.65,
        "root_depth_m": 1.40,
        "depletion_fraction_p": 0.65,
        "optimal_temp_c": (18.0, 32.0),
        "vpd_stress_threshold_kpa": 3.0,
        "color": "#84cc16"
    },
    "lettuce": {
        "name": "Lettuce (Lactuca sativa)",
        "kc_ini": 0.70,
        "kc_mid": 1.00,
        "kc_end": 0.95,
        "root_depth_m": 0.30,
        "depletion_fraction_p": 0.30,
        "optimal_temp_c": (14.0, 22.0),
        "vpd_stress_threshold_kpa": 1.4,
        "color": "#10b981"
    },
    "strawberry": {
        "name": "Strawberry (Fragaria)",
        "kc_ini": 0.40,
        "kc_mid": 0.85,
        "kc_end": 0.75,
        "root_depth_m": 0.35,
        "depletion_fraction_p": 0.30,
        "optimal_temp_c": (15.0, 25.0),
        "vpd_stress_threshold_kpa": 1.5,
        "color": "#f43f5e"
    },
    "cotton": {
        "name": "Cotton (Gossypium hirsutum)",
        "kc_ini": 0.35,
        "kc_mid": 1.20,
        "kc_end": 0.60,
        "root_depth_m": 1.10,
        "depletion_fraction_p": 0.65,
        "optimal_temp_c": (22.0, 34.0),
        "vpd_stress_threshold_kpa": 2.8,
        "color": "#06b6d4"
    },
    "rice": {
        "name": "Paddy Rice (Oryza sativa)",
        "kc_ini": 1.05,
        "kc_mid": 1.20,
        "kc_end": 0.90,
        "root_depth_m": 0.50,
        "depletion_fraction_p": 0.20,
        "optimal_temp_c": (22.0, 32.0),
        "vpd_stress_threshold_kpa": 1.8,
        "color": "#14b8a6"
    }
}

# Worldwide Demo Farm Presets
DEMO_FARMS = [
    {
        "id": "salinas-valley",
        "name": "Salinas Valley Precision Organic Farm",
        "location_name": "Salinas Valley, California, USA",
        "latitude": 36.6777,
        "longitude": -121.6555,
        "total_area_acres": 125.0,
        "default_soil": "loam",
        "zones": [
            {
                "id": "zone-1",
                "name": "North Field - Heirloom Tomatoes",
                "crop": "tomato",
                "soil": "loam",
                "area_acres": 35.0,
                "growth_stage": "mid",
                "irrigation_type": "drip",
                "coordinates": [
                    [36.6795, -121.6580],
                    [36.6820, -121.6540],
                    [36.6790, -121.6515],
                    [36.6765, -121.6555]
                ]
            },
            {
                "id": "zone-2",
                "name": "Central Tier - Crisp Lettuce",
                "crop": "lettuce",
                "soil": "silt_loam",
                "area_acres": 45.0,
                "growth_stage": "mid",
                "irrigation_type": "sprinkler",
                "coordinates": [
                    [36.6765, -121.6555],
                    [36.6790, -121.6515],
                    [36.6750, -121.6480],
                    [36.6725, -121.6520]
                ]
            },
            {
                "id": "zone-3",
                "name": "South Berry Terrace",
                "crop": "strawberry",
                "soil": "sandy_loam",
                "area_acres": 45.0,
                "growth_stage": "mid",
                "irrigation_type": "drip",
                "coordinates": [
                    [36.6725, -121.6520],
                    [36.6750, -121.6480],
                    [36.6710, -121.6450],
                    [36.6685, -121.6490]
                ]
            }
        ]
    },
    {
        "id": "punjab-belt",
        "name": "Punjab Golden Acre Farm",
        "location_name": "Ludhiana, Punjab, India",
        "latitude": 30.9010,
        "longitude": 75.8573,
        "total_area_acres": 90.0,
        "default_soil": "sandy_loam",
        "zones": [
            {
                "id": "zone-1",
                "name": "Sector A - Basmati Paddy",
                "crop": "rice",
                "soil": "clay_loam",
                "area_acres": 40.0,
                "growth_stage": "mid",
                "irrigation_type": "surface",
                "coordinates": [
                    [30.9030, 75.8540],
                    [30.9060, 75.8590],
                    [30.9020, 75.8620],
                    [30.8990, 75.8570]
                ]
            },
            {
                "id": "zone-2",
                "name": "Sector B - Sweet Corn",
                "crop": "maize",
                "soil": "sandy_loam",
                "area_acres": 50.0,
                "growth_stage": "mid",
                "irrigation_type": "sprinkler",
                "coordinates": [
                    [30.8990, 75.8570],
                    [30.9020, 75.8620],
                    [30.8980, 75.8650],
                    [30.8950, 75.8600]
                ]
            }
        ]
    },
    {
        "id": "tuscany-estate",
        "name": "Chianti Valley Olive & Vineyard",
        "location_name": "Siena, Tuscany, Italy",
        "latitude": 43.3188,
        "longitude": 11.3308,
        "total_area_acres": 80.0,
        "default_soil": "clay_loam",
        "zones": [
            {
                "id": "zone-1",
                "name": "Hillside Sangiovese Vines",
                "crop": "grapevine",
                "soil": "clay_loam",
                "area_acres": 45.0,
                "growth_stage": "mid",
                "irrigation_type": "drip",
                "coordinates": [
                    [43.3210, 11.3280],
                    [43.3235, 11.3330],
                    [43.3195, 11.3360],
                    [43.3170, 11.3310]
                ]
            },
            {
                "id": "zone-2",
                "name": "Ancient Olive Grove",
                "crop": "olive",
                "soil": "silt_loam",
                "area_acres": 35.0,
                "growth_stage": "mid",
                "irrigation_type": "drip",
                "coordinates": [
                    [43.3170, 11.3310],
                    [43.3195, 11.3360],
                    [43.3155, 11.3390],
                    [43.3130, 11.3340]
                ]
            }
        ]
    }
]
