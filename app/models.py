try:
    # Import SQLAlchemy components. Surround with try/except to provide a clearer
    # error message if the installed SQLAlchemy version is incompatible with
    # the running Python interpreter (common with very new Python versions).
    from sqlalchemy import Column, Integer, String, Float, DateTime
    # Use the modern import path for declarative_base
    from sqlalchemy.orm import declarative_base
except Exception as e:
    raise RuntimeError(
        "Failed to import SQLAlchemy. This often happens when the installed "
        "SQLAlchemy version is incompatible with your Python version.\n"
        "Suggested fixes:\n"
        "  - Downgrade Python to 3.11 or 3.12, or\n"
        "  - Upgrade SQLAlchemy to a version that supports your Python release, e.g.:\n"
        "      pip install -U 'sqlalchemy>=2.1'\n"
        "Then re-run the application. Original error: " + str(e)
    ) from e
from datetime import datetime

Base = declarative_base()

class Reading(Base):
    __tablename__ = "readings"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    ec = Column(Float, nullable=False)
    tds = Column(Float, nullable=False)
    wqi = Column(Float, nullable=False)
    irrigation_index = Column(String(20), nullable=False)
    ph = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "temperature": self.temperature,
            "ec": self.ec,
            "tds": self.tds,
            "wqi": self.wqi,
            "irrigation_index": self.irrigation_index,
            "ph": self.ph,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def calculate_tds(cls, ec: float) -> float:
        """Calculate TDS from EC reading"""
        return ec * 500
    
    @classmethod
    def calculate_wqi(cls, temperature: float, ec: float) -> float:
        """Calculate Water Quality Index (placeholder algorithm)"""
        # Simple WQI calculation based on temperature and EC
        # This is a placeholder - implement proper WQI algorithm as needed
        temp_score = max(0, 100 - abs(temperature - 25) * 2)  # Optimal temp ~25°C
        ec_score = max(0, 100 - ec * 20)  # Lower EC is better
        
        wqi = (temp_score + ec_score) / 2
        return round(wqi, 2)
    
    @classmethod
    def calculate_irrigation_index(cls, ec: float) -> str:
        """Calculate irrigation sustainability index"""
        if ec < 0.7:
            return "Excellent"
        elif ec <= 3.0:
            return "Moderate"
        else:
            return "Unsuitable"
