import os
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Base
except Exception as e:
    raise RuntimeError(
        "Failed to import SQLAlchemy or project models. This is usually due to an "
        "incompatible SQLAlchemy version for your Python interpreter.\n"
        "Suggested fixes:\n"
        "  - Upgrade SQLAlchemy: pip install -U 'sqlalchemy>=2.1'\n"
        "  - Or use Python 3.11/3.12 if you are on a very new Python release.\n"
        "Original error: " + str(e)
    ) from e

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./water_quality.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
