from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    full_name: str

class User(UserBase):
    id: int
    is_active: bool
    is_onboarded: bool
    full_name: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class EnergyDataCreate(BaseModel):
    generated_energy: float

class EnergyData(EnergyDataCreate):
    id: int
    timestamp: datetime
    user_id: Optional[int] = None

    class Config:
        orm_mode = True
