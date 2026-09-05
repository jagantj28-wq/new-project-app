from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.advisor_service import generate_advisor_response, assess_agronomic_risks
from app.models.schemas import AdvisorChatRequest, AdvisorChatResponse, AgronomicRisk, SimulationResponse

router = APIRouter(prefix="/api/advisor", tags=["AI Agronomist Copilot"])

class RiskAssessmentRequest(BaseModel):
    crop: str = "tomato"
    soil: str = "loam"
    simulation: SimulationResponse

@router.post("/chat", response_model=AdvisorChatResponse)
async def chat_with_agronomist(req: AdvisorChatRequest):
    """
    Interactive Agronomist Copilot consultation endpoint.
    Processes natural-language agronomy inquiries against current farm conditions.
    """
    zone_name = "Selected Field"
    crop = "tomato"
    soil = "loam"

    if req.simulation_context:
        zone_name = req.simulation_context.get("zone_name", zone_name)
        crop = req.simulation_context.get("crop", crop)
        soil = req.simulation_context.get("soil", soil)

    return await generate_advisor_response(
        query=req.message,
        zone_name=zone_name,
        crop=crop,
        soil=soil,
        simulation=None
    )

@router.post("/risks", response_model=List[AgronomicRisk])
def evaluate_risks(req: RiskAssessmentRequest):
    """
    Evaluate micro-climate trajectory to produce structured risk diagnoses.
    """
    return assess_agronomic_risks(req.simulation, req.crop, req.soil)
