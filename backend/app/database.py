"""
Database configuration and session management.

Creates the SQLAlchemy engine and session factory used to
interact with the database. Provides a shared base class
for models and a database session dependency for FastAPI
routes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit = False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
