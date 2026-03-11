from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from database import engine, Base
from routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Water Quality Monitoring API")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down Water Quality Monitoring API")

app = FastAPI(
    title="Water Quality Monitoring API",
    description="IoT Water Quality Monitoring & Analytics System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = Path(__file__).resolve().parent

# Ensure static and templates directories exist (avoid RuntimeError on startup)
static_dir = base_dir / "static"
if not static_dir.exists():
    logger.warning("Static directory '%s' does not exist. Creating it.", static_dir)
    static_dir.mkdir(parents=True, exist_ok=True)

templates_dir = base_dir / "templates"
if not templates_dir.exists():
    logger.warning("Templates directory '%s' does not exist. Creating it.", templates_dir)
    templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

app.include_router(router, prefix="/api", tags=["telemetry"])

@app.get("/")
async def dashboard(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "water-quality-monitoring"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
