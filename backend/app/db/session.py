from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models.db_models import Base
from app.utils.logger import logger

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully using URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e

def get_db():
    """Dependency for yielding database sessions per request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
