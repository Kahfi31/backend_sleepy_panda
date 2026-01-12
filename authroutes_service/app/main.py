import logging
import os
import redis.asyncio as aioredis
from datetime import datetime, timedelta
from typing import List

# Framework & Utils
from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import extract
from sqlalchemy.orm import Session
from jose import jwt
from dotenv import load_dotenv

# Internal Modules
import models
import schemas
import utils
import database
from database import get_db
import httpx

# --- KONFIGURASI & SETUP ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)


# Configure logging
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()

# Database initialization
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
router = APIRouter()

PREDICT_SERVICE_URL = "http://predictroutes_service:8001"

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "2&aSeI[]ILhEP-I"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Redis Global Variable
redis = None

@app.on_event("startup")
async def startup_event():
    global redis
    # Database initialization
    models.Base.metadata.create_all(bind=database.engine)
    # Pastikan Redis berjalan di localhost atau sesuaikan URL-nya
    try:
        redis = await aioredis.from_url("redis://redis:6379",decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

# --- UTILITY FUNCTIONS ---

def normalize_work_title(work_title: str) -> str:
    """Membersihkan string pekerjaan untuk pencocokan ID."""
    return ''.join(e for e in work_title.lower().strip() if e.isalnum() or e.isspace()).replace(" ", "")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- TAMBAHAN HELPER FUNCTION ---
async def push_to_daily_service(data: dict):
    """
    Fungsi bantuan untuk mengirim data ke Predict Service (Port 8001)
    agar masuk ke tabel 'daily'.
    """
    try:
        # Pastikan ada tanggal hari ini
        if "date" not in data:
            data["date"] = str(datetime.now().date())
            
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{PREDICT_SERVICE_URL}/sync_daily",
                json=data,
                timeout=5.0
            )
    except Exception as e:
        # Kita log error saja, jangan sampai user gagal save cuma karena service 8001 mati
        logger.error(f"Gagal sinkron ke Predict Service: {e}")

# ==========================================
# 1. AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/register/")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = utils.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role}
    )

    return {"access_token": access_token, "token_type": "bearer", "role": db_user.role}

@app.post("/login/")
async def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email tidak terdaftar")
    
    if not utils.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password salah")
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "role": "user"}

@app.post("/logout/")
async def logout(token: str = Depends(oauth2_scheme)):
    return {"msg": "Logout successful"}

# ==========================================
# 2. USER PROFILE & HEALTH DATA
# ==========================================

@app.get("/user-profile/{email}") 
async def get_user_profile(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/user-profile/update")
async def update_user_profile(user_data: schemas.UserProfile, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user fields if provided in user_data
    update_fields = ["name", "gender", "date_of_birth"]
    for field in update_fields:
        if getattr(user_data, field) is not None:
            setattr(user, field, getattr(user_data, field))

    db.commit()
    db.refresh(user)

    return {"message": "User profile updated successfully", "user": user}


@app.put("/save-name/")
async def save_name(request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    user.name = request.name
    db.commit()
    return {"message": "Name saved successfully", "user": user}

@app.put("/save-gender/")
async def save_gender(request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    if request.gender is not None:
        user.gender = int(request.gender)
    db.commit()
    return {"message": "Gender saved successfully", "user": user}

@app.put("/save-dob/")
async def save_dob(request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    if request.date_of_birth:
        user.date_of_birth = request.date_of_birth
        # Hitung Umur
        try:
            birth_date = datetime.strptime(request.date_of_birth, '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            user.age = age
        except ValueError:
            pass 
    db.commit()
    return {"message": "DOB saved", "user": user}

@app.put("/save-weight/")
async def save_weight(request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.weight = request.weight
    db.commit()
    return {"message": "Weight saved"}

@app.put("/save-height/")
async def save_height(request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.height = request.height
    db.commit()
    return {"message": "Height saved"}

@app.put("/save-blood-pressure/")
async def save_blood_pressure(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get('email')
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Update DB Lokal (User Profile)
    user.upper_pressure = data.get('upperPressure')
    user.lower_pressure = data.get('lowerPressure')
    db.commit()
    
    # 2. Kirim ke Predict Service (History Harian)
    await push_to_daily_service({
        "email": email,
        "upper_pressure": user.upper_pressure,
        "lower_pressure": user.lower_pressure
    })
    
    return {"message": "BP saved"}

@app.put("/save-daily-steps/")
async def save_daily_steps(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get('email')
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Update DB Lokal (User Profile)
    user.daily_steps = data.get('dailySteps')
    db.commit()
    
    # 2. Kirim ke Predict Service (History Harian)
    await push_to_daily_service({
        "email": email,
        "daily_steps": user.daily_steps
    })
    
    return {"message": "Steps saved"}

@app.put("/save-heart-rate/")
async def save_heart_rate(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get('email')
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Update DB Lokal (User Profile)
    user.heart_rate = data.get('heartRate')
    db.commit()

    # 2. Kirim ke Predict Service (History Harian)
    await push_to_daily_service({
        "email": email,
        "heart_rate": user.heart_rate
    })
    
    return {"message": "Heart rate saved"}

@app.put("/save-work/")
async def save_work(request: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")

    normalized_work = normalize_work_title(request.work)
    user.work = request.work

    # Mapping Work ID
    work_id_map = {
        'accountant': 0, 'doctor': 1, 'engineer': 2, 'lawyer': 3,
        'manager': 4, 'nurse': 5, 'salesrepresentative': 6, 'salesperson': 7,
        'scientist': 8, 'softwareengineer': 9, 'teacher': 10
    }
    
    work_id = work_id_map.get(normalized_work, 20) 
    user.work_id = work_id

    # Simpan ke tabel Work
    work_record = db.query(models.Work).filter(models.Work.email == user.email).first()
    if not work_record:
        work_record = models.Work(
            email=user.email, work_id=work_id, 
            quality_of_sleep=5.0, physical_activity_level=50.0, stress_level=5.0
        )
        db.add(work_record)
    else:
        work_record.work_id = work_id

    db.commit()
    return {"message": "Work saved", "user": user}

@app.post("/store-info")
async def store_user_info(user_info: schemas.UserInfo):
    if redis:
        user_data = user_info.dict()
        await redis.set(user_info.gender, str(user_data))
        return {"message": "Data stored successfully in Redis"}
    return {"message": "Redis not available"}

# --- FEEDBACK ---

@app.post("/submit-feedback/")
async def submit_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    new_fb = models.Feedback(
        email=feedback.email,
        feedback=feedback.feedback,
        created_at=datetime.now()
    )
    db.add(new_fb)
    db.commit()
    return {"message": "Feedback submitted"}

# ==========================================
# 4. ADMIN ENDPOINTS
# ==========================================

@app.get("/api/users/", response_model=List[schemas.UserListResponse]) 
def get_all_users(db: Session = Depends(get_db)):
    """Mengambil semua data user untuk Admin Panel."""
    users = db.query(models.User).all()
    return users

@app.get("/api/user/detail/{email}")
def get_user_detail(email: str, db: Session = Depends(get_db)):
    """Mengambil detail user (misal: untuk header dashboard)."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ==========================================
# 5. SYNC ENDPOINTS (OFFLINE SUPPORT)
# ==========================================
# Bagian ini TIDAK DIUBAH sesuai permintaan Anda.

@app.post("/sync_users")
def sync_users(data: schemas.SyncUserRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user:
        user = models.User(email=data.email, role="user", hashed_password="OFFLINE_CREATED")
        db.add(user)
    
    if data.name: user.name = data.name
    if data.gender is not None: user.gender = data.gender
    if data.work: user.work = data.work
    if data.date_of_birth: user.date_of_birth = data.date_of_birth
    if data.age: user.age = data.age
    if data.weight: user.weight = data.weight
    if data.height: user.height = data.height
    if data.upper_pressure: user.upper_pressure = data.upper_pressure
    if data.lower_pressure: user.lower_pressure = data.lower_pressure
    if data.daily_steps: user.daily_steps = data.daily_steps
    if data.heart_rate: user.heart_rate = data.heart_rate

    db.commit()
    return {"message": "User synced"}

@app.post("/sync_feedback")
async def sync_feedback(feedback: schemas.SyncFeedbackRequest, db: Session = Depends(get_db)):
    try:
        created = datetime.fromisoformat(feedback.created_at)
    except:
        created = datetime.now()
        
    new_fb = models.Feedback(
        email=feedback.email, 
        feedback=feedback.feedback, 
        created_at=created
    )
    db.add(new_fb)
    db.commit()
    return {"message": "Feedback synced"}

@app.post("/sync_work_data")
def sync_work_data(data: schemas.SyncWorkDataRequest, db: Session = Depends(get_db)):
    work = db.query(models.Work).filter(models.Work.email == data.email).first()
    if work:
        work.quality_of_sleep = data.quality_of_sleep
        work.physical_activity_level = data.physical_activity_level
        work.stress_level = data.stress_level
        work.work_id = data.work_id
    else:
        new_work = models.Work(
            email=data.email,
            quality_of_sleep=data.quality_of_sleep,
            physical_activity_level=data.physical_activity_level,
            stress_level=data.stress_level,
            work_id=data.work_id
        )
        db.add(new_work)
    db.commit()
    return {"message": "Work synced"}