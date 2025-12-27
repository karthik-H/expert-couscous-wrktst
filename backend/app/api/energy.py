from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
from .auth import get_current_user

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/current", response_model=schemas.EnergyData)
def get_current_energy(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.is_onboarded:
        raise HTTPException(status_code=403, detail="Access denied. Complete onboarding first.")
    
    # Assuming "current" means the latest data point
    latest = db.query(models.EnergyData).order_by(models.EnergyData.timestamp.desc()).first()
    if not latest:
        # Return a dummy if no data yet, or 404
        raise HTTPException(status_code=404, detail="No energy data found")
    return latest

@router.get("/history", response_model=list[schemas.EnergyData])
def get_energy_history(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.is_onboarded:
        raise HTTPException(status_code=403, detail="Access denied. Complete onboarding first.")

    # Returns last N records
    history = db.query(models.EnergyData).order_by(models.EnergyData.timestamp.desc()).limit(limit).all()
    return history
