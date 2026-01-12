from sqlalchemy import Column, Integer, String, DateTime, Float, Date, Enum, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

# === PERHATIKAN: SEMUA FOREIGN KEY DIHAPUS ===

class SleepRecord(Base):
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True)
    # HAPUS ForeignKey, ganti jadi String biasa + index agar pencarian cepat
    email = Column(String(255), index=True, nullable=False) 
    sleep_time = Column(DateTime, nullable=False)
    wake_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False) 
    
class Daily(Base):
    __tablename__ = "daily"

    id = Column(Integer, primary_key=True, index=True)
    # HAPUS ForeignKey
    email = Column(String(255), index=True, nullable=False)
    date = Column(Date, nullable=False)
    upper_pressure = Column(Integer, nullable=True)
    lower_pressure = Column(Integer, nullable=True)
    daily_steps = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    duration = Column(Float, nullable=False)
    prediction_result = Column(Integer, nullable=True)
    
class WeeklyPrediction(Base):
    __tablename__ = "weekly_predictions"

    id = Column(Integer, primary_key=True, index=True)
    # HAPUS ForeignKey
    email = Column(String(255), index=True, nullable=False)
    prediction_result = Column(Enum('Insomnia', 'Normal', 'Sleep Apnea', name="prediction_enum"), nullable=False)
    prediction_date = Column(TIMESTAMP, server_default=func.now())

class MonthlyPrediction(Base):
    __tablename__ = "monthly_predictions"

    id = Column(Integer, primary_key=True, index=True)
    # Yang ini sudah benar dari awal
    email = Column(String(255), index=True, nullable=False) 
    prediction_result = Column(String(255), nullable=False)