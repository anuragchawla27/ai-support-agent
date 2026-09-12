"""
SQLAlchemy engine/session setup. Reads DATABASE_URL from config.py.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
