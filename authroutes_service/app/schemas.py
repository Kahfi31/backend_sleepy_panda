from pydantic import BaseModel, EmailStr
from datetime import date, datetime, time
from typing import Optional

# =======================
# AUTHENTICATION SCHEMAS
# =======================

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "user"

class OtpRequest(BaseModel):
    email: EmailStr

# =======================
# USER PROFILE SCHEMAS
# =======================

class NameRequest(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    work: Optional[str] = None
    date_of_birth: Optional[str] = None
    weight: Optional[int] = None
    height: Optional[int] = None
    upper_pressure: Optional[int] = None
    lower_pressure: Optional[int] = None
    heart_rate: Optional[int] = None
    daily_steps: Optional[int] = None
    sleep_time: Optional[int] = None
    wake_time: Optional[int] = None

class UserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[int] = None
    date_of_birth: Optional[str] = None

class UserData(BaseModel):
    email: str
    name: str
    gender: int
    work: str
    work_id: int
    date_of_birth: date
    height: float
    weight: float 

class UserInfo(BaseModel):
    gender: int
    age: int
    work: str
    weight: float
    height: float

class UserListResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: Optional[str] = "user"
    
    class Config:
        from_attributes = True

# Diubah dari 'Feedback' menjadi 'FeedbackCreate' agar sesuai dengan main.py
class FeedbackCreate(BaseModel):
    email: EmailStr
    feedback: str

# =======================
# SYNC SCHEMAS (OFFLINE)
# =======================

class SyncUserRequest(BaseModel):
    email: str
    name: Optional[str] = None
    gender: Optional[int] = None
    work: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    upper_pressure: Optional[int] = None
    lower_pressure: Optional[int] = None
    daily_steps: Optional[int] = None
    heart_rate: Optional[int] = None

class SyncFeedbackRequest(BaseModel):
    email: str
    feedback: str
    created_at: str

class SyncWorkDataRequest(BaseModel):
    email: str
    quality_of_sleep: float
    physical_activity_level: float
    stress_level: float
    work_id: int

class UserInfo(BaseModel):
    gender : int
    age : int
    work : str
    weight : float
    height : float