import uvicorn
import os
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"🌱 Starting FarmTwin Digital Twin on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
