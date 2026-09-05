# 🌱 FarmTwin — Precision Agriculture Digital Twin & Micro-Climate Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Leaflet GIS](https://img.shields.io/badge/GIS-Leaflet%20%2B%20Esri%20Satellite-green.svg)](https://leafletjs.com/)
[![FAO-56 Standard](https://img.shields.io/badge/Model-FAO--56%20Penman--Monteith-orange.svg)](https://www.fao.org/3/x0490e/x0490e00.htm)
[![CI](https://github.com/jagantj28-wq/new-project-app/actions/workflows/ci.yml/badge.svg)](https://github.com/jagantj28-wq/new-project-app/actions)

> **Transform farmland parcels into dynamic, predictive digital twins.** FarmTwin pairs live hyper-local satellite agro-meteorological data with the internationally validated **FAO-56 Soil Water-Balance model** to simulate 14-day root zone moisture depletion, predict micro-climate drought and fungal disease risks, and generate precision irrigation prescriptions.

---

## 🌟 Why FarmTwin is Different

Most agricultural software projects are cookie-cutter leaf disease image classifiers or static weather dashboards. **FarmTwin is an operational farm digital twin** that bridges the gap between raw agro-meteorology, physics-based crop hydrology, and real-world farm machinery:

1. **No Hardware Required:** Uses real, free 1km-resolution multi-spectral atmospheric and soil data via the Open-Meteo Agricultural API.
2. **Scientifically Rigorous:** Adheres strictly to the **FAO Irrigation and Drainage Paper No. 56** (dual crop coefficient $K_c$, dynamic water stress coefficient $K_s$, and root zone depletion $D_r$).
3. **Interactive Visual Studio:** Draw custom crop zone polygons on real-world high-resolution **Esri World Imagery** satellite tiles.
4. **Time-Machine Simulation:** Scrub through an interactive 14-day timeline to watch soil moisture deplete day-by-day and see crop polygons dynamically transition from healthy green to stress amber and drought red.
5. **Machine-Ready Prescriptions:** Computes exact replenishment dosages (liters, gallons, mm depth), pump runtimes, and electrical energy costs adjusted for drip, sprinkler, or furrow delivery efficiency.
6. **AI Agronomist Copilot:** Context-aware agronomic expert system (supporting Google Gemini or the built-in agronomy rule engine) for disease scouting, fertigation recipes, and drought mitigation.

---

## 🏗️ Architecture

```
                                    FARMTWIN PLATFORM
                                    
  [ Real Farmland Coordinates ]              [ Open-Meteo Agro-API ]
                │                                       │
                ▼                                       ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                         FastAPI Backend Core                           │
  │                                                                        │
  │  1. Agro-Weather Ingestion ──► Solar Rad, ET0, VPD, Soil Temp/Moisture │
  │  2. FAO-56 Simulation Engine ──► TAW, RAW, Dr, Ks, Actual ETc          │
  │  3. Irrigation Prescriptions ──► Liters/Acre, Pump Runtime, Energy $   │
  │  4. Agronomist AI Copilot ──► Integrated Pest Mgmt & Fertigation       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ REST API / JSON
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                      Interactive Web Application                       │
  │                                                                        │
  │  • Esri World Imagery Satellite Map with Dynamic Zone Polygons         │
  │  • 14-Day Micro-Climate Timeline Scrubber & Animation Player           │
  │  • Chart.js Dual-Axis Soil Moisture & Evapotranspiration Telemetry     │
  │  • Multi-Pulse Drip & Sprinkler Execution Schedules                    │
  │  • Slide-Out AI Agronomist Copilot Chat Drawer                         │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 The Science: FAO-56 Soil Water-Balance

FarmTwin models the soil root reservoir as a dynamic bucket whose capacity is governed by USDA soil texture characteristics and crop rooting depth:

$$TAW = 1000 \cdot (\theta_{FC} - \theta_{WP}) \cdot Z_r$$

$$\text{Readily Available Water: } RAW = p \cdot TAW$$

$$\text{Root Zone Depletion: } D_{r, i} = D_{r, i-1} - (P_i - RO_i) - I_i + ET_{c, i}$$

$$\text{Water Stress Coefficient: } K_s = \frac{TAW - D_r}{(1 - p) \cdot TAW} \quad (\text{when } D_r > RAW)$$

$$\text{Actual Crop Evapotranspiration: } ET_c = K_s \cdot K_c \cdot ET_0$$

Where:
* $\theta_{FC}$: Volumetric soil water content at Field Capacity ($m^3/m^3$)
* $\theta_{WP}$: Volumetric soil water content at Wilting Point ($m^3/m^3$)
* $Z_r$: Effective rooting depth of crop ($m$)
* $p$: Soil water depletion fraction without water stress
* $ET_0$: FAO-56 Penman-Monteith reference evapotranspiration ($mm/\text{day}$)

---

## 🚀 Quickstart

### Prerequisites
* Python 3.10+ (or [uv](https://github.com/astral-sh/uv))
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/jagantj28-wq/new-project-app.git
cd new-project-app
```

### 2. Install Dependencies
Using standard `pip`:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

*Or using `uv` (lightning fast):*
```bash
uv pip install -r requirements.txt
```

### 3. (Optional) Configure AI Copilot
FarmTwin operates out of the box with its built-in agronomic expert knowledge engine. To connect full Gemini reasoning:
```bash
cp .env.example .env
# Add your GEMINI_API_KEY in .env
```

### 4. Run the Application
```bash
python run.py
```
Visit **`http://127.0.0.1:8000`** in your browser to explore the interactive digital twin!

---

## 🧪 Running the Test Suite

FarmTwin includes comprehensive unit and integration tests covering hydrological equations, crop stress coefficients, and API routes:

```bash
pytest tests/ -v
```

---

## 📂 Project Structure

```
new-project-app/
├── .github/workflows/ci.yml       # GitHub Actions automated test workflow
├── app/
│   ├── api/                       # Modular FastAPI route handlers
│   │   ├── routes_advisor.py      # AI Agronomist Copilot chat & alarms
│   │   ├── routes_farm.py         # Farm presets, crop & soil metadata
│   │   ├── routes_prescription.py # Pump runtime, volume & energy calculator
│   │   └── routes_simulation.py   # 14-day FAO-56 simulation trigger
│   ├── models/
│   │   └── schemas.py             # Pydantic v2 schemas and validation
│   ├── services/
│   │   ├── advisor_service.py     # Agronomic risk engine & LLM copilot
│   │   ├── simulation_engine.py   # FAO-56 soil water balance simulation math
│   │   └── weather_service.py     # Open-Meteo agro-weather API integration
│   ├── static/
│   │   ├── css/style.css          # Glassmorphism & agronomic theme styles
│   │   └── js/
│   │       ├── advisor.js         # Slide-out agronomist copilot controller
│   │       ├── app.js             # Main application orchestrator
│   │       ├── charts.js          # Chart.js telemetry visualization
│   │       └── map.js             # Leaflet GIS & Esri satellite polygon manager
│   ├── templates/
│   │   └── index.html             # Single-page interactive digital twin UI
│   ├── config.py                  # Global settings, USDA soils & FAO crops
│   └── main.py                    # FastAPI entrypoint & static mounts
├── tests/
│   ├── test_api_endpoints.py      # FastAPI endpoint integration tests
│   └── test_simulation_engine.py  # Hydrological & FAO-56 math unit tests
├── .env.example
├── .gitignore
├── LICENSE                        # MIT License
├── pyproject.toml
├── README.md
├── requirements.txt
└── run.py                         # Application runner
```

---

## 🗺️ Included Global Demo Farms

FarmTwin comes pre-loaded with three world-class agricultural presets with real satellite coordinates and multi-zone crops:
* **Salinas Valley Organic Estate, California, USA:** Heirloom Tomatoes, Crisp Lettuce, Strawberries (Loam & Silt Loam).
* **Punjab Golden Acre Farm, Ludhiana, India:** Basmati Paddy Rice & Sweet Corn (Clay Loam & Sandy Loam).
* **Chianti Valley Estate, Tuscany, Italy:** Hillside Sangiovese Grapevines & Century Olive Groves (Clay Loam & Silt Loam).

---

## 📚 Scientific References
* Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). *Crop evapotranspiration-Guidelines for computing crop water requirements-FAO Irrigation and drainage paper 56*. FAO, Rome, 300(9), D05109.
* United States Department of Agriculture (USDA) Natural Resources Conservation Service. *Soil Survey Manual & Hydrological Soil Groups*.
* Open-Meteo Meteorological Database (CC-BY 4.0).

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed with ❤️ by **[Jagan T. Jiju](https://github.com/jagantj28-wq)**.
