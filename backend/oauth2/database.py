import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check your .env file.")

# Optimized SQLAlchemy engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=75,          # koneksi utama ke DB
    max_overflow=100,       # koneksi tambahan saat load tinggi (total = 100)
    pool_timeout=60,       # waktu tunggu sebelum timeout (detik)
    pool_recycle=1800,     # recycle koneksi tiap 30 menit
    pool_pre_ping=True,    # ping koneksi sebelum digunakan
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency untuk FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
