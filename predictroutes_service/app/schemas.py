from pydantic import BaseModel, EmailStr
from datetime import date, datetime, time
from typing import Optional

class SleepData(BaseModel):
    email: str
    sleep_time: datetime
    wake_time: datetime
    
class PredictRequest(BaseModel):
    email: EmailStr

class SavePredictionRequest(BaseModel):
    email: str
    prediction_result: int

class WeeklyPredictRequest(BaseModel):
    email: str

class SavePredictionRequestWeek(BaseModel):
    email: str
    prediction_result: int  # Mengharapkan input berupa integer

class MonthlyPredictRequest(BaseModel):
    email: str

class SavePredictionRequestMonth(BaseModel):
    email: str
    prediction_result: int  # Mengharapkan input berupa integer

class SleepDataResponse(BaseModel):
    sleep_time: str
    wake_time: str
    
    class Config:
        orm_mode = True

class SyncDailyRequest(BaseModel):
    email: str
    date: str
    upper_pressure: Optional[int] = 0
    lower_pressure: Optional[int] = 0
    daily_steps: Optional[int] = 0
    heart_rate: Optional[int] = 0
    duration: Optional[float] = 0.0
    prediction_result: Optional[int] = None

class SyncPredictionRequest(BaseModel):
    email: str
    prediction_result: int
    created_at: str 

