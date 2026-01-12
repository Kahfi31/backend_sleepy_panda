from passlib.context import CryptContext
import logging
import sqlite3
from sqlalchemy.exc import OperationalError, SQLAlchemyError, DBAPIError

# Konfigurasi Logger
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 1. Fungsi Password (Tetap Sama) ---
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# --- 2. Logika Fallback (BARU) ---
def fallback_or_mysql(action_mysql, action_sqlite):
    """
    Mencoba menjalankan fungsi MySQL.
    Jika terjadi error koneksi (OperationalError), otomatis jalankan fungsi SQLite.
    """
    try:
        # Coba jalankan aksi MySQL
        return action_mysql()
    
    except (OperationalError, DBAPIError) as e:
        # Menangkap error jika MySQL mati/unreachable
        logger.warning(f"MySQL Connection failed/timeout. Switching to SQLite. Error: {e}")
        return action_sqlite()
        
    except SQLAlchemyError as e:
        # Menangkap error SQLAlchemy lain yang berkaitan dengan DB
        logger.error(f"Database Error: {e}. Switching to SQLite.")
        return action_sqlite()
        
    except Exception as e:
        # Opsional: Jika ada error coding lain, log dan tetap coba SQLite agar tidak crash
        logger.error(f"Unexpected error: {e}. Attempting SQLite fallback.")
        return action_sqlite()

# --- 3. Autentikasi Offline (BARU) ---
def authenticate_local(email: str, password: str, db_name="/app/data/local_storage.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT hashed_password FROM users WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        return verify_password(password, row[0])

    except Exception as e:
        logger.error(f"Local auth failed: {e}")
        return False
