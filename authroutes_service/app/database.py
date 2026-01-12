import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check your .env file.")

# Optimized SQLAlchemy engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=75,           
    max_overflow=100,       
    pool_timeout=10,        # <--- UBAH: Kurangi ini (misal 10 detik) supaya antrian pool gak kelamaan nunggu
    pool_recycle=1800,      
    pool_pre_ping=True,     
    
    # ---------------------------------------------------------
    # TAMBAHKAN BAGIAN INI (PENTING UNTUK FALLBACK):
    # ---------------------------------------------------------
    connect_args={
        "connect_timeout": 3  # Jika 3 detik gak connect ke MySQL, anggap error (biar langsung switch ke SQLite)
    }
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
