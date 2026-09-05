import re
from typing import List, Dict, Any, Optional
import httpx
from app.config import get_settings, CROP_PROPERTIES, SOIL_PROPERTIES
from app.models.schemas import AgronomicRisk, AdvisorChatResponse, SimulationResponse

def assess_agronomic_risks(
    simulation: SimulationResponse,
    crop_key: str,
    soil_key: str
) -> List[AgronomicRisk]:
    """
    Evaluate 14-day simulation trajectory and identify biological/hydrological risks.
    """
    risks: List[AgronomicRisk] = []
    crop_info = CROP_PROPERTIES.get(crop_key, CROP_PROPERTIES["tomato"])
    opt_min, opt_max = crop_info["optimal_temp_c"]
    vpd_thresh = crop_info["vpd_stress_threshold_kpa"]

    days = simulation.daily_results

    # 1. Check for Drought & Transpiration Suppression
    stressed_days = [d for d in days if d.stress_coefficient_ks < 0.70]
    if len(stressed_days) >= 2:
        first_day = stressed_days[0]
        risks.append(
            AgronomicRisk(
                category="Moisture Stress",
                severity="CRITICAL" if len(stressed_days) > 4 else "WARNING",
                title=f"Root Zone Moisture Deficit in {simulation.zone_name}",
                description=(
                    f"Crop transpiration coefficient (Ks) drops to {first_day.stress_coefficient_ks} "
                    f"on {first_day.date}. Soil moisture falls below readily available threshold (RAW)."
                ),
                remediation=(
                    f"Schedule drip irrigation of ~{first_day.deficit_liters_per_acre:,.0f} L/acre "
                    f"before {first_day.date} to prevent stomatal closure and yield penalty."
                )
            )
        )

    # 2. Check for Atmospheric Vapour Pressure Deficit (VPD) Stress
    high_vpd_days = [d for d in days if d.vpd_kpa > vpd_thresh]
    if high_vpd_days:
        peak_vpd = max(d.vpd_kpa for d in high_vpd_days)
        risks.append(
            AgronomicRisk(
                category="Atmospheric Demand",
                severity="WARNING",
                title="Elevated Vapour Pressure Deficit (VPD)",
                description=(
                    f"Atmospheric dryness reaches {peak_vpd} kPa (optimal threshold is < {vpd_thresh} kPa). "
                    f"High evaporative demand may cause transient leaf wilting during solar noon."
                ),
                remediation="Consider short mid-day micro-sprinkler pulses or anti-transpirant foliar sprays if dry winds persist."
            )
        )

    # 3. Check for Fungal Disease Incubation Window (High humidity / low VPD + moderate temp)
    fungal_risk_days = [d for d in days if d.vpd_kpa < 0.5 and 18.0 <= d.temperature_c <= 25.0 and d.precipitation_mm > 1.0]
    if fungal_risk_days:
        risks.append(
            AgronomicRisk(
                category="Pathogen Pressure",
                severity="WARNING",
                title="Fungal / Mildew Infection Climate Window",
                description=(
                    f"Persistent humid conditions (VPD < 0.5 kPa, temp {fungal_risk_days[0].temperature_c}°C) "
                    f"with rain provide an ideal environment for spore germination (e.g. Downy/Powdery Mildew, Phytophthora)."
                ),
                remediation="Ensure canopy aeration, inspect lower foliage for sporulation, and apply preventive organic/copper-based protectants."
            )
        )

    # 4. Thermal Stress
    extreme_heat_days = [d for d in days if d.temperature_c > (opt_max + 3.0)]
    if extreme_heat_days:
        risks.append(
            AgronomicRisk(
                category="Thermal Stress",
                severity="WARNING",
                title="Heat Wave Above Crop Thermal Optimum",
                description=f"Canopy temperatures exceed optimal maximum ({opt_max}°C), risking pollen sterility and flower abortion.",
                remediation="Maintain soil moisture buffer near Field Capacity to maximize evaporative cooling through transpiration."
            )
        )

    return risks

async def generate_advisor_response(
    query: str,
    zone_name: str = "Primary Field",
    crop: str = "tomato",
    soil: str = "loam",
    simulation: Optional[SimulationResponse] = None
) -> AdvisorChatResponse:
    """
    Generate agronomic advisory response using Gemini if key is provided,
    or our high-precision Agronomic Expert System.
    """
    settings = get_settings()
    q_lower = query.lower()

    # If Gemini API key is configured, query Gemini model
    if settings.GEMINI_API_KEY:
        try:
            return await _query_gemini_agronomist(query, zone_name, crop, soil, simulation, settings.GEMINI_API_KEY)
        except Exception as e:
            print(f"[Advisor] Gemini query error: {e}. Falling back to internal agronomic expert engine.")

    # Rule-based Agronomic Knowledge Engine
    return _query_expert_knowledge_engine(query, zone_name, crop, soil, simulation)

async def _query_gemini_agronomist(
    query: str,
    zone_name: str,
    crop: str,
    soil: str,
    simulation: Optional[SimulationResponse],
    api_key: str
) -> AdvisorChatResponse:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    current_status = simulation.summary.current_status if simulation else "OPTIMAL"
    moisture = simulation.summary.current_moisture_pct if simulation else 24.0
    deficit = simulation.summary.total_water_deficit_liters if simulation else 0.0

    prompt = f"""You are the FarmTwin AI Senior Agronomist and Soil Hydrologist.
Context:
- Zone: {zone_name}
- Crop: {crop}
- Soil: {soil}
- Current Soil Moisture: {moisture}%
- Hydrological Status: {current_status}
- Total Root Zone Deficit: {deficit:,.0f} Liters

Farmer Query: "{query}"

Respond concisely and professionally in 2-3 structured paragraphs with precise agronomic scientific guidance, specific irrigation timings, nutrient considerations, and climate protection steps."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            reply_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return AdvisorChatResponse(
                reply=reply_text,
                risks=[],
                action_items=["Follow agronomic prescription guidelines", "Re-run simulation after irrigation"],
                source="AI_MODEL"
            )
        raise Exception(f"Status {resp.status_code}: {resp.text}")

def _query_expert_knowledge_engine(
    query: str,
    zone_name: str,
    crop: str,
    soil: str,
    simulation: Optional[SimulationResponse]
) -> AdvisorChatResponse:
    q = query.lower()
    crop_info = CROP_PROPERTIES.get(crop, CROP_PROPERTIES.get("tomato", {}))
    soil_info = SOIL_PROPERTIES.get(soil, SOIL_PROPERTIES.get("loam", {}))

    cur_moist = simulation.summary.current_moisture_pct if simulation else 24.5
    deficit = simulation.summary.total_water_deficit_liters if simulation else 45000.0
    rec_date = simulation.summary.recommended_irrigation_date if simulation else "Tomorrow"
    status = simulation.summary.current_status if simulation else "OPTIMAL"

    action_items: List[str] = []
    risks: List[AgronomicRisk] = []

    if any(w in q for w in ["water", "irrigate", "irrigation", "schedule", "thirsty", "deficit"]):
        reply = (
            f"💧 **Precision Irrigation Prescription for {zone_name} ({crop_info.get('name', crop)})**:\n\n"
            f"Based on the FAO-56 dual crop coefficient model and local atmospheric demand, your soil moisture is currently at **{cur_moist}%** "
            f"(Status: **{status}**).\n\n"
            f"• **Recommended Action Date:** Initiate watering by **{rec_date}** before root zone depletion exceeds Readily Available Water (RAW).\n"
            f"• **Total Soil Deficit:** **{deficit:,.0f} Liters** across the block.\n"
            f"• **Best Timing:** Run drip irrigation between 4:00 AM – 8:00 AM or after 6:30 PM to minimize evaporative losses and prevent solar scorch on wet foliage."
        )
        action_items = [
            f"Run morning irrigation before {rec_date}",
            f"Verify drip emitter flow rate across {zone_name}",
            "Check soil probe at 15cm depth 2 hours post-irrigation"
        ]

    elif any(w in q for w in ["fertilizer", "nutrient", "npk", "nitrogen", "feed", "chlorosis", "yellow"]):
        reply = (
            f"🌿 **Nutrient Management & Fertigation Strategy for {crop_info.get('name', crop)}**:\n\n"
            f"In **{soil_info.get('name', soil)}**, nutrient availability is closely coupled with soil volumetric moisture. "
            f"At **{cur_moist}%** moisture, root ion exchange is active.\n\n"
            f"• **Nitrogen (N):** Apply water-soluble nitrate/urea via fertigation during peak vegetative development. Avoid over-applying right before heavy rain to prevent leaching below root depth ({crop_info.get('root_depth_m', 0.8)}m).\n"
            f"• **Potassium (K) & Calcium (Ca):** Essential for cell wall turgor and stomatal regulation, which protects against drought stress.\n"
            f"• **Foliar Micronutrients:** If interveinal chlorosis appears on young leaves, apply a chelated iron/zinc foliar spray in early morning."
        )
        action_items = [
            "Inject water-soluble fertilizer in the middle 50% of the irrigation cycle",
            "Test electrical conductivity (EC) of drip effluent (target 1.8 - 2.4 dS/m)",
            "Flush lines with clean water for 15 minutes post-fertigation"
        ]

    elif any(w in q for w in ["disease", "fungus", "blight", "pest", "rot", "mildew", "bug", "spray"]):
        reply = (
            f"🛡️ **Integrated Pest & Disease Management (IPM)**:\n\n"
            f"Micro-climate conditions (Vapour Pressure Deficit and canopy temperature) dictate spore germination kinetics:\n\n"
            f"• **Fungal Window:** When relative humidity exceeds 85% with leaf wetness for >4 consecutive hours, fungal spores (such as Botrytis, powdery/downy mildew, and late blight) can establish within 12–24 hours.\n"
            f"• **Preventive Cultural Control:** Utilize drip irrigation rather than overhead sprinklers to keep foliage dry. Maintain open canopy pruning to optimize internal air exchange.\n"
            f"• **Biological/Organic Defense:** Consider preventative applications of *Bacillus subtilis* or copper hydroxide formulations prior to forecasted rain events."
        )
        action_items = [
            "Scout perimeter rows and dense foliage areas for early lesions",
            "Avoid overhead irrigation during humid evenings",
            "Sanitize pruning shears between row passes"
        ]

    elif any(w in q for w in ["soil", "texture", "organic", "clay", "sand", "drainage", "aeration"]):
        reply = (
            f"🌱 **Soil Physical Profile: {soil_info.get('name', soil)}**:\n\n"
            f"{soil_info.get('description', '')}\n\n"
            f"• **Field Capacity (FC):** {soil_info.get('fc', 0.28) * 100:.0f}% volumetric water content.\n"
            f"• **Permanent Wilting Point (WP):** {soil_info.get('wp', 0.14) * 100:.0f}% volumetric water content.\n"
            f"• **Infiltration Rate:** ~{soil_info.get('infiltration_rate_mm_hr', 12.0)} mm/hour. Keep irrigation application rates below this value to prevent surface runoff and erosion.\n"
            f"• **Health Recommendation:** Incorporate compost or cover crops (vetch, clover) to improve soil organic carbon, aggregate stability, and infiltration capacity."
        )
        action_items = [
            "Monitor infiltration rate to avoid pooling",
            "Add 2-3 inches of organic mulch around root zones to cut evaporative loss by 30%",
            "Perform comprehensive soil organic matter (SOM) testing annually"
        ]

    else:
        reply = (
            f"🌾 **FarmTwin Agronomic Copilot Briefing for {zone_name}**:\n\n"
            f"I have analyzed your **{crop_info.get('name', crop)}** on **{soil_info.get('name', soil)}**:\n"
            f"• **Current Soil Moisture:** **{cur_moist}%** (FAO-56 Status: **{status}**)\n"
            f"• **Next Irrigation Window:** Scheduled for **{rec_date}**\n"
            f"• **Active Root Depth:** **{crop_info.get('root_depth_m', 0.8)} meters**\n\n"
            f"Feel free to ask me about:\n"
            f"1. *'When should I irrigate and how many gallons?'*\n"
            f"2. *'What fertilizer ratios are optimal right now?'*\n"
            f"3. *'How to manage disease risks during humid weather?'*\n"
            f"4. *'How to improve water retention in {soil_info.get('name', soil)}?'*"
        )
        action_items = [
            "Review 14-day moisture depletion graph on the dashboard",
            "Inspect irrigation prescription pump run-time calculations"
        ]

    return AdvisorChatResponse(
        reply=reply,
        risks=risks,
        action_items=action_items,
        source="AGRONOMIC_EXPERT_ENGINE"
    )
