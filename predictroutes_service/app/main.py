import logging
import os
import joblib
import numpy as np
import httpx
from datetime import datetime, timedelta, date

# Framework & Database
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from dotenv import load_dotenv

# Internal Modules
import models
import schemas
import database
from database import get_db

# --- CONFIGURATION & SETUP ---

# Path & Environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Logging
logger = logging.getLogger(__name__)

# --- ML MODEL PATHS ---
ML_DIR = os.path.join(BASE_DIR, 'ml_model')

MODEL_PATH = os.path.join(ML_DIR, 'xgb_model_Test.pkl')
SCALER_PATH = os.path.join(ML_DIR, 'minmax_scaler_split.pkl')
OCCUPATION_ENCODER_PATH = os.path.join(ML_DIR, 'Occupation_label_encoder.pkl')
BMI_CATEGORY_ENCODER_PATH = os.path.join(ML_DIR, 'BMI Category_label_encoder.pkl')
GENDER_ENCODER_PATH = os.path.join(ML_DIR, 'Gender_label_encoder.pkl') # NEW

# Auth Service URL
AUTH_SERVICE_URL = "http://authroutes_service:8000"

# Global Variables for Models
model = None
scaler = None
occupation_encoder = None
bmi_encoder = None
gender_encoder = None # NEW

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STARTUP EVENT (LOAD MODELS) ---

@app.on_event("startup")
async def startup_event():
    global model, scaler, occupation_encoder, bmi_encoder, gender_encoder
    logger.info(f"Server starting up from {BASE_DIR}...")
    
    # Helper function to check and load
    def load_pickle(path, name):
        if os.path.exists(path):
            try:
                obj = joblib.load(path)
                logger.info(f"{name} loaded successfully.")
                return obj
            except Exception as e:
                logger.error(f"Failed to load {name}: {e}")
                return None
        else:
            logger.error(f"{name} file not found at {path}")
            return None

    # Load All Models
    model = load_pickle(MODEL_PATH, "XGBoost Model")
    scaler = load_pickle(SCALER_PATH, "Scaler")
    occupation_encoder = load_pickle(OCCUPATION_ENCODER_PATH, "Occupation Encoder")
    bmi_encoder = load_pickle(BMI_CATEGORY_ENCODER_PATH, "BMI Encoder")
    gender_encoder = load_pickle(GENDER_ENCODER_PATH, "Gender Encoder") # NEW

    if not model or not scaler:
        logger.critical("CRITICAL: Model or Scaler failed to load. Prediction will not work.")

# --- HELPER FUNCTIONS ---

async def fetch_user_profile(email: str):
    """
    Mengambil data user lengkap dari Auth Service via HTTP Request.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{AUTH_SERVICE_URL}/user-profile/{email}", timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                logger.warning(f"User {email} not found in Auth Service")
                return None
            else:
                logger.error(f"Auth Service Error: {resp.status_code}")
                return None
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth Service: {e}")
            return None

def calculate_bmi_category(height_cm, weight_kg):
    """
    Menghitung BMI dan mengembalikan kategori dalam bentuk INTEGER (0, 1, 2).
    """
    if not height_cm or not weight_kg:
        return 0 # Default Normal
    
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    # Logic Kategori BMI Standard (Sesuaikan dengan data training)
    # 0: Normal, 1: Obese, 2: Overweight
    if bmi < 25:
        return 0 
    elif 25 <= bmi < 30:
        return 2 
    else:
        return 1 

def prepare_features(user_data, sleep_duration, scaler):
    """
    Menyiapkan array input untuk model XGBoost.
    """
    # 1. Extract Semua Data Terlebih Dahulu (Agar Rapi)
    age = user_data.get('age', 30)
    raw_gender = user_data.get('gender', 0)
    occupation = user_data.get('work_id', 0)
    height = user_data.get('height', 170)
    weight = user_data.get('weight', 65)
    
    # Metrics Kesehatan
    quality_of_sleep = user_data.get('quality_of_sleep', 5)
    physical_activity = user_data.get('physical_activity_level', 50)
    stress_level = user_data.get('stress_level', 5)
    heart_rate = user_data.get('heart_rate', 70)
    daily_steps = user_data.get('daily_steps', 5000)
    systolic = user_data.get('upper_pressure', 120)
    diastolic = user_data.get('lower_pressure', 80)
    
    additional_feature = 0 

    # 2. Proses Encoding Gender
    # Jika gender berupa string (misal: "Male", "Female") dan encoder tersedia
    if gender_encoder and isinstance(raw_gender, str):
        try:
            gender = gender_encoder.transform([raw_gender])[0]
        except Exception:
            gender = 0 
    else:
        try:
            gender = int(raw_gender)
        except:
            gender = 0

    # 3. Hitung BMI Category
    bmi_cat = calculate_bmi_category(height, weight)

    # 4. Scaling (Fitur Numerik)
    # Urutan array ini HARUS SAMA dengan urutan saat training Scaler
    raw_numerical = [
        age,  # <-- Sekarang variabel age dipakai disini
        sleep_duration, 
        quality_of_sleep, 
        physical_activity,
        stress_level, 
        heart_rate, 
        daily_steps, 
        systolic, 
        diastolic, 
        additional_feature
    ]
    
    # Membuat array input untuk scaler
    input_to_scaler = np.zeros((1, 12)) 
    input_to_scaler[0, :10] = raw_numerical
    
    scaled = scaler.transform(input_to_scaler).flatten()

    # 5. Final Input Vector
    # Urutan array ini HARUS SAMA dengan urutan saat training Model XGBoost
    features = np.array([
        gender,         # 0
        scaled[0],      # Age (Menggunakan hasil scaling dari variabel age)
        occupation,     # 2
        scaled[1],      # Duration
        scaled[2],      # Quality
        scaled[3],      # Physical Activity
        scaled[4],      # Stress
        bmi_cat,        # 7
        scaled[5],      # Heart Rate
        scaled[6],      # Steps
        scaled[7],      # Systolic
        scaled[8]       # Diastolic
    ]).reshape(1, -1)
    
    return features

# ==========================================
# 1. PREDICTION ENDPOINTS (DAILY)
# ==========================================

@app.post("/predict")
async def predict(request: schemas.PredictRequest, db: Session = Depends(get_db)):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="ML Model not loaded properly.")

    email = request.email
    
    # A. Fetch Data Profil dari Auth Service
    user_data = await fetch_user_profile(email)
    if not user_data:
        raise HTTPException(status_code=404, detail="User profile not found via Auth Service.")

    # B. Fetch Data Tidur Terakhir dari DB Lokal
    sleep_record = db.query(models.SleepRecord)\
        .filter(models.SleepRecord.email == email)\
        .order_by(models.SleepRecord.sleep_time.desc())\
        .first()

    if not sleep_record:
        logger.warning(f"No sleep record found for {email}, using default duration.")
        sleep_duration = 0.0
    else:
        sleep_duration = sleep_record.duration

    try:
        # C. Prepare Features & Predict
        features = prepare_features(user_data, sleep_duration, scaler)
        
        prediction = model.predict(features)[0]
        prediction_int = int(prediction)
        
        # Mapping Result
        mapping = {0: 'Insomnia', 1: 'Normal', 2: 'Sleep Apnea'}
        result_str = mapping.get(prediction_int, 'Unknown')

        # D. Save Result
        today = date.today()
        daily_record = db.query(models.Daily).filter(
            models.Daily.email == email,
            models.Daily.date == today
        ).first()

        # Data snapshot untuk disimpan di history
        systolic = user_data.get('upper_pressure', 0)
        diastolic = user_data.get('lower_pressure', 0)
        daily_steps = user_data.get('daily_steps', 0)
        heart_rate = user_data.get('heart_rate', 0)

        if daily_record:
            daily_record.prediction_result = prediction_int
            daily_record.duration = sleep_duration
            daily_record.upper_pressure = systolic
            daily_record.lower_pressure = diastolic
            daily_record.daily_steps = daily_steps
            daily_record.heart_rate = heart_rate
        else:
            new_daily_record = models.Daily(
                email=email,
                date=today,
                upper_pressure=systolic,
                lower_pressure=diastolic,
                daily_steps=daily_steps,
                heart_rate=heart_rate,
                duration=sleep_duration,
                prediction_result=prediction_int
            )
            db.add(new_daily_record)
        
        db.commit()
        return {"prediction": result_str}

    except Exception as e:
        db.rollback()
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# ==========================================
# 2. WEEKLY & MONTHLY PREDICTION
# ==========================================

@app.post("/weekly_predict")
def weekly_predict(request: schemas.WeeklyPredictRequest, db: Session = Depends(get_db)):
    try:
        email = request.email
        today = date.today()
        seven_days_ago = today - timedelta(days=7)

        weekly_data = db.query(models.Daily).filter(
            models.Daily.email == email,
            models.Daily.date >= seven_days_ago,
            models.Daily.date <= today
        ).all()

        if not weekly_data:
            raise HTTPException(status_code=404, detail="Tidak ada data harian minggu ini.")

        counts = {0: 0, 1: 0, 2: 0} # 0: Insomnia, 1: Normal, 2: Apnea
        for r in weekly_data:
            if r.prediction_result in counts:
                counts[r.prediction_result] += 1

        if counts[1] > (counts[0] + counts[2]):
            result = 'Normal'
        elif counts[2] > counts[0]:
            result = 'Sleep Apnea'
        elif counts[0] > counts[2]:
            result = 'Insomnia'
        else:
            result = 'Sleep Apnea'

        return {"weekly_prediction": result}

    except Exception as e:
        logger.error(f"Weekly Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monthly_predict")
def monthly_predict(request: schemas.MonthlyPredictRequest, db: Session = Depends(get_db)):
    try:
        email = request.email
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        monthly_data = db.query(models.Daily).filter(
            models.Daily.email == email,
            models.Daily.date >= thirty_days_ago
        ).all()

        if not monthly_data:
            raise HTTPException(status_code=404, detail="Tidak ada data bulan ini.")

        counts = {0: 0, 1: 0, 2: 0}
        for r in monthly_data:
            if r.prediction_result in counts:
                counts[r.prediction_result] += 1

        if counts[1] > (counts[0] + counts[2]):
            result = 'Normal'
        elif counts[2] > counts[0]:
            result = 'Sleep Apnea'
        else:
            result = 'Insomnia'

        return {"monthly_prediction": result}

    except Exception as e:
        logger.error(f"Monthly Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. SAVE PREDICTION & SLEEP RECORD
# ==========================================

prediction_mapping = {0: "Insomnia", 1: "Normal", 2: "Sleep Apnea"}

@app.post("/save_prediction")
def save_prediction_manual(request: schemas.SavePredictionRequest, db: Session = Depends(get_db)):
    try:
        today = date.today()
        daily_record = db.query(models.Daily).filter(
            models.Daily.email == request.email,
            models.Daily.date == today
        ).first()

        if daily_record:
            daily_record.prediction_result = request.prediction_result
        else:
            new_record = models.Daily(
                email=request.email,
                date=today,
                prediction_result=request.prediction_result,
                duration=0.0
            )
            db.add(new_record)
        
        db.commit()
        return {"message": "Prediction saved manually"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-sleep-record/")
async def save_sleep_record(sleep_data: schemas.SleepData, db: Session = Depends(get_db)):
    sleep_time = sleep_data.sleep_time
    wake_time = sleep_data.wake_time
    
    if sleep_time >= wake_time:
        wake_time += timedelta(days=1)
    
    duration = (wake_time - sleep_time).total_seconds() / 3600

    existing = db.query(models.SleepRecord).filter(
        models.SleepRecord.email == sleep_data.email,
        extract('year', models.SleepRecord.sleep_time) == sleep_time.year,
        extract('month', models.SleepRecord.sleep_time) == sleep_time.month,
        extract('day', models.SleepRecord.sleep_time) == sleep_time.day
    ).first()

    if existing:
        existing.sleep_time = sleep_time
        existing.wake_time = wake_time
        existing.duration = duration
        db.commit()
        return {"message": "Record updated"}
    else:
        new_record = models.SleepRecord(
            email=sleep_data.email,
            sleep_time=sleep_time,
            wake_time=wake_time,
            duration=duration
        )
        db.add(new_record)
        db.commit()
        return {"message": "Record saved"}

@app.get("/get-sleep-records/{email}")
async def get_sleep_records(email: str, db: Session = Depends(get_db)):
    records = db.query(models.SleepRecord).filter(models.SleepRecord.email == email)\
        .order_by(models.SleepRecord.sleep_time.desc()).all()
    
    response_data = []
    seen_dates = set()
    for r in records:
        r_date = r.sleep_time.date()
        if r_date not in seen_dates:
            dur = r.wake_time - r.sleep_time
            response_data.append({
                "date": r.sleep_time.strftime('%d %B %Y'),
                "duration": f"{dur.seconds // 3600} jam {dur.seconds % 3600 // 60} menit",
                "time": f"{r.sleep_time.strftime('%H:%M')} - {r.wake_time.strftime('%H:%M')}"
            })
            seen_dates.add(r_date)
    return response_data

@app.get("/get-weekly-sleep-data/{email}")
async def get_weekly_sleep_data(email: str, start_date: str, end_date: str, db: Session = Depends(database.get_db)):
    # Convert string dates to datetime objects
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=2)

    # Retrieve sleep records for the user between the start and end date
    sleep_records = db.query(models.SleepRecord).filter(
        models.SleepRecord.email == email,
        models.SleepRecord.sleep_time >= start_date_obj,
        models.SleepRecord.wake_time <= end_date_obj
    ).order_by(models.SleepRecord.sleep_time.desc()).all()


    if not sleep_records:
        raise HTTPException(status_code=404, detail="No sleep records found for the week")

    # Filter to keep only the latest record per day
    latest_records_per_day = {}
    for record in sleep_records:
        record_date = record.sleep_time.date()
        # Only keep the latest record for each date
        if record_date not in latest_records_per_day:
            latest_records_per_day[record_date] = record

    # Initialize dictionaries to store sleep durations, start times, and wake times for each day
    daily_sleep_durations = {i: timedelta() for i in range(7)}  # {0: Monday, ..., 6: Sunday}
    daily_sleep_start_times = {i: [] for i in range(7)}  # Store sleep start times for each day
    daily_wake_times = {i: [] for i in range(7)}  # Store wake times for each day

    for record in latest_records_per_day.values():
        # Handle cross-midnight sleep records
        if record.wake_time < record.sleep_time:
            record.wake_time += timedelta(days=1)

        duration = record.wake_time - record.sleep_time

        # Calculate the day of the week for the sleep time (0=Monday, 6=Sunday)
        day_of_week = record.sleep_time.weekday()
        daily_sleep_durations[day_of_week] += duration

        # Store the sleep start time for the day
        daily_sleep_start_times[day_of_week].append(record.sleep_time.strftime("%H:%M"))
        
        # Store the wake time for the day
        daily_wake_times[day_of_week].append(record.wake_time.strftime("%H:%M"))

    # Convert timedelta to hours for each day
    daily_sleep_durations_hours = [round(daily_sleep_durations[i].total_seconds() / 3600, 2) for i in range(7)]

    # Calculate total duration as the sum of daily sleep durations
    total_duration = sum(daily_sleep_durations_hours)

    # Calculate averages
    avg_duration = total_duration / len(latest_records_per_day)
    avg_sleep_time = (sum((timedelta(hours=int(time[:2]), minutes=int(time[3:])) 
                          for times in daily_sleep_start_times.values() for time in times), timedelta()) 
                      / len(latest_records_per_day))
    avg_wake_time = (sum((timedelta(hours=int(time[:2]), minutes=int(time[3:])) 
                         for times in daily_wake_times.values() for time in times), timedelta()) 
                     / len(latest_records_per_day))

    return {
        "daily_sleep_durations": daily_sleep_durations_hours,
        "daily_sleep_start_times": daily_sleep_start_times,  # Field with sleep start times
        "daily_wake_times": daily_wake_times,  # New field with wake times
        "avg_duration": f"{int(avg_duration)} jam {int((avg_duration * 60) % 60)} menit",
        "avg_sleep_time": (datetime.min + avg_sleep_time).strftime("%H:%M"),
        "avg_wake_time": (datetime.min + avg_wake_time).strftime("%H:%M"),
        "total_duration": f"{int(total_duration)} jam {int((total_duration * 60) % 60)} menit"
    }

@app.get("/get-monthly-sleep-data/{email}")
async def get_monthly_sleep_data(email: str, month: str, year: int, db: Session = Depends(database.get_db)):
    # Calculate the start and end dates for the month
    start_date_obj = datetime(year, int(month), 1)
    next_month = start_date_obj.replace(day=28) + timedelta(days=4)  # This will always jump to the next month
    end_date_obj = next_month - timedelta(days=next_month.day)

    # Retrieve sleep records for the user between the start and end dates
    sleep_records = db.query(models.SleepRecord).filter(
        models.SleepRecord.email == email,
        models.SleepRecord.sleep_time >= start_date_obj,
        models.SleepRecord.wake_time < end_date_obj + timedelta(days=1)  # Include the entire end day
    ).order_by(models.SleepRecord.sleep_time.desc()).all()  # Sort by sleep_time descending

    if not sleep_records:
        raise HTTPException(status_code=404, detail="No sleep records found for the month")

    # Filter to keep only the latest record per day
    latest_records_per_day = {}
    for record in sleep_records:
        record_date = record.sleep_time.date()
        if record_date not in latest_records_per_day:
            latest_records_per_day[record_date] = record

    # Initialize dictionaries to store weekly and daily sleep durations, start times, and wake times
    weekly_sleep_durations = {i: timedelta() for i in range(4)}
    weekly_sleep_start_times = {i: [] for i in range(4)}
    weekly_wake_times = {i: [] for i in range(4)}

    # Initialize daily sleep duration list
    days_in_month = (end_date_obj - start_date_obj).days + 1
    daily_sleep_durations = [0.0] * days_in_month  # Initialize daily sleep durations with 0

    for record in latest_records_per_day.values():
        # Handle cross-midnight sleep records
        if record.wake_time < record.sleep_time:
            record.wake_time += timedelta(days=1)

        duration = record.wake_time - record.sleep_time

        # Calculate the day of the month for the sleep time
        day_of_month = (record.sleep_time - start_date_obj).days
        daily_sleep_durations[day_of_month] = round(duration.total_seconds() / 3600, 2)  # Convert to hours

        # Calculate the week of the month for the sleep time
        week_of_month = day_of_month // 7
        if week_of_month > 3:
            week_of_month = 3

        weekly_sleep_durations[week_of_month] += duration
        weekly_sleep_start_times[week_of_month].append(record.sleep_time.strftime("%H:%M"))
        weekly_wake_times[week_of_month].append(record.wake_time.strftime("%H:%M"))

    weekly_sleep_durations_hours = [round(weekly_sleep_durations[i].total_seconds() / 3600, 2) for i in range(4)]
    total_duration = sum(weekly_sleep_durations_hours)

    avg_duration = total_duration / len(latest_records_per_day)

    # Adjust sleep times for proper average calculation
    sleep_times_in_minutes = []
    for times in weekly_sleep_start_times.values():
        for time in times:
            hours, minutes = map(int, time.split(':'))
            if hours < 12:
                hours += 24  # Adjust early morning times past midnight to make calculations accurate
            sleep_times_in_minutes.append(hours * 60 + minutes)

    avg_sleep_minutes = sum(sleep_times_in_minutes) / len(sleep_times_in_minutes)
    avg_sleep_hours = int(avg_sleep_minutes // 60)
    avg_sleep_minutes = int(avg_sleep_minutes % 60)

    wake_times_in_minutes = []
    for times in weekly_wake_times.values():
        for time in times:
            hours, minutes = map(int, time.split(':'))
            wake_times_in_minutes.append(hours * 60 + minutes)

    avg_wake_minutes = sum(wake_times_in_minutes) / len(wake_times_in_minutes)
    avg_wake_hours = int(avg_wake_minutes // 60)
    avg_wake_minutes = int(avg_wake_minutes % 60)

    return {
        "weekly_sleep_durations": weekly_sleep_durations_hours,
        "weekly_sleep_start_times": weekly_sleep_start_times,
        "weekly_wake_times": weekly_wake_times,
        "daily_sleep_durations": daily_sleep_durations,  # Send daily data to the frontend
        "avg_duration": f"{int(avg_duration)} jam {int((avg_duration * 60) % 60)} menit",
        "avg_sleep_time": f"{avg_sleep_hours:02d}:{avg_sleep_minutes:02d}",
        "avg_wake_time": f"{avg_wake_hours:02d}:{avg_wake_minutes:02d}",
        "total_duration": f"{int(total_duration)} jam {int((total_duration * 60) % 60)} menit"
    }

# ==========================================
# 4. SYNC ENDPOINTS (DATA TRANSFER)
# ==========================================

@app.post("/sync_daily")
def sync_daily(data: schemas.SyncDailyRequest, db: Session = Depends(get_db)):
    try:
        date_str = str(data.date)
        if "T" in date_str:
            record_date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
        else:
            try:
                record_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                record_date = date.today()

        daily_record = db.query(models.Daily).filter(
            models.Daily.email == data.email,
            models.Daily.date == record_date
        ).first()

        if daily_record:
            if data.prediction_result is not None: daily_record.prediction_result = data.prediction_result
            if data.daily_steps: daily_record.daily_steps = data.daily_steps
            if data.duration: daily_record.duration = data.duration
            if data.upper_pressure: daily_record.upper_pressure = data.upper_pressure
            if data.lower_pressure: daily_record.lower_pressure = data.lower_pressure
            if data.heart_rate: daily_record.heart_rate = data.heart_rate
        else:
            new_daily = models.Daily(
                email=data.email,
                date=record_date,
                upper_pressure=data.upper_pressure,
                lower_pressure=data.lower_pressure,
                daily_steps=data.daily_steps,
                heart_rate=data.heart_rate,
                duration=data.duration,
                prediction_result=data.prediction_result
            )
            db.add(new_daily)

        db.commit()
        return {"message": "Daily data synced"}
    except Exception as e:
        db.rollback()
        logger.error(f"Sync Daily Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync_weekly_predictions")
def sync_weekly(data: schemas.SyncPredictionRequest, db: Session = Depends(get_db)):
    try:
        created_at = datetime.fromisoformat(str(data.created_at).replace("Z", ""))
    except:
        created_at = datetime.now()

    new_record = models.WeeklyPrediction(
        email=data.email,
        prediction_result=data.prediction_result,
        created_at=created_at
    )
    db.add(new_record)
    try:
        db.commit()
        return {"message": "Weekly prediction synced"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync_monthly_predictions")
def sync_monthly(data: schemas.SyncPredictionRequest, db: Session = Depends(get_db)):
    try:
        created_at = datetime.fromisoformat(str(data.created_at).replace("Z", ""))
    except:
        created_at = datetime.now()

    new_record = models.MonthlyPrediction(
        email=data.email,
        prediction_result=data.prediction_result,
        prediction_date=created_at
    )
    db.add(new_record)
    try:
        db.commit()
        return {"message": "Monthly prediction synced"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))