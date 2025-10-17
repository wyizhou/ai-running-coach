from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")) or ".", exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_light_migrations():
    """Ensure new columns exist for SQLite when tables already created."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    try:
        with engine.connect() as conn:
            # Check user_profiles.other_info
            res = conn.exec_driver_sql("PRAGMA table_info(user_profiles);")
            cols = [r[1] for r in res]
            if "other_info" not in cols:
                conn.exec_driver_sql("ALTER TABLE user_profiles ADD COLUMN other_info TEXT;")
    except Exception:
        # Best-effort; ignore
        pass
