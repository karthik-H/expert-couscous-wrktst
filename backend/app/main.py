from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api import auth, onboarding, energy
from .services import scheduler
import logging

# Create tables
# In production, use Alembic for migrations
from . import models
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Energy Monitor")

# CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(energy.router, prefix="/api/energy", tags=["energy"])

@app.on_event("startup")
def startup_event():
    logging.info("Starting scheduler...")
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"message": "Welcome to Energy Monitor API"}
