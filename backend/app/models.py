from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    # Onboarding fields
    is_onboarded = Column(Boolean, default=False)
    energy_source_pic = Column(String, nullable=True) # Path to file
    supporting_doc = Column(String, nullable=True) # Path to file

class EnergyData(Base):
    __tablename__ = "energy_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    generated_energy = Column(Float)
    
    # We might want to link this to a user if multiple users have different sources
    # For now, per spec, it's global or implicit. Adding user_id for future proofing/best practice
    # but could be optional depending on exact interpretation. Given "user's energy source", likely per user.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    
    owner = relationship("User", back_populates="energy_data")

User.energy_data = relationship("EnergyData", back_populates="owner")
