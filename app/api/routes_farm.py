from typing import List, Dict, Any
from fastapi import APIRouter
from app.config import DEMO_FARMS, CROP_PROPERTIES, SOIL_PROPERTIES
from app.models.schemas import FarmProfile, ZoneResponse

router = APIRouter(prefix="/api/farm", tags=["Farm Management"])

@router.get("/presets", response_model=List[Dict[str, Any]])
def get_farm_presets():
    """Retrieve pre-configured world-class demo farms with satellite coordinates and zones."""
    return DEMO_FARMS

@router.get("/crops", response_model=Dict[str, Any])
def get_crops():
    """Retrieve all supported crop models, Kc values, root depths and optimal parameters."""
    return CROP_PROPERTIES

@router.get("/soils", response_model=Dict[str, Any])
def get_soils():
    """Retrieve USDA soil texture classifications with Field Capacity and Wilting Points."""
    return SOIL_PROPERTIES
