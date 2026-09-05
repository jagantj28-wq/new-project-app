import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import routes_farm, routes_simulation, routes_prescription, routes_advisor

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Templates
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API Routers
app.include_router(routes_farm.router)
app.include_router(routes_simulation.router)
app.include_router(routes_prescription.router)
app.include_router(routes_advisor.router)

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the FarmTwin digital twin single-page application."""
    index_file = templates_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>FarmTwin API is active. index.html not found.</h1>")

@app.get("/api/health")
def health_check():
    """System health check and diagnostic status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "features": {
            "satellite_map": True,
            "fao56_simulation": True,
            "agro_weather_open_meteo": True,
            "precision_prescription": True,
            "ai_copilot": True
        }
    }
