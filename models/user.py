from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional
from datetime import date, datetime

class UserRole(str, Enum):
    ATHLETE = "athlete"
    COACH = "coach"
    ADMIN = "admin"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    sport: Optional[str] = None
    position: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    sport: Optional[str] = None
    position: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
