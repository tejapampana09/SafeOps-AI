import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.seed import seed_database
from app.api.endpoints import router as api_router
from app.api.websockets import manager

from app.simulator.engine import simulator_engine

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("safeops.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("safeops")

# --- App Lifecycle Manager ---
@asynccontextmanager
async def lifecycle(app: FastAPI):
    # Startup: Initialize DB and Seed Data
    logger.info("Initializing database and seeding default datasets...")
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
    finally:
        db.close()
    
    # Start Simulator Engine
    simulator_engine.start()
    
    yield
    # Shutdown
    logger.info("Shutting down SafeOps AI backend...")
    simulator_engine.stop()

# --- FastAPI App Instantiation ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifecycle
)

# --- CORS Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon sandbox ease of development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register REST Routes ---
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- WebSocket Route Implementation ---
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket frame: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENV
    }
