from sqlalchemy import Column, Integer, String, Time, DateTime, ForeignKey, Float, Date, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(20), default="user")
    name = Column(String(255), nullable=True)
    gender = Column(Integer, nullable=True)
    work = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    age = Column(Integer)
    weight = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    upper_pressure = Column(Integer, nullable=True)
    lower_pressure = Column(Integer, nullable=True)
    daily_steps = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    reset_token = Column(String(255), nullable=True)


class Work(Base):
    __tablename__ = "work_data"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, index=True)
    email = Column(String(255), ForeignKey("users.email"), nullable=False)
    work_id = Column(Integer, nullable=True)
    quality_of_sleep = Column(Float, nullable=True)
    physical_activity_level = Column(Float, nullable=True)
    stress_level = Column(Float, nullable=True)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    feedback = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)