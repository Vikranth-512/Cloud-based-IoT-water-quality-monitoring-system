from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import List, Optional
import logging

from database import get_db
from models import Reading

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", status_code=200)
async def ingest_telemetry(reading_data: dict, db: Session = Depends(get_db)):
    """
    Ingest water quality telemetry data
    Expected payload:
    {
        "device_id": "unit_001",
        "timestamp": "ISO_8601_UTC",
        "temperature": 30.44,
        "ec": 1.125,
        "tds": 562.5,
        "wqi": 93,
        "irrigation_index": "Moderate"
    }
    """
    try:
        # Validate required fields
        required_fields = ["device_id", "timestamp", "temperature", "ec", "tds", "wqi", "irrigation_index"]
        for field in required_fields:
            if field not in reading_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(reading_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601 format.")
        
        # Validate numeric ranges
        if not (-50 <= reading_data["temperature"] <= 100):
            raise HTTPException(status_code=400, detail="Temperature must be between -50 and 100°C")
        
        if not (0 <= reading_data["ec"] <= 10):
            raise HTTPException(status_code=400, detail="EC must be between 0 and 10 mS/cm")
        
        if not (0 <= reading_data["wqi"] <= 100):
            raise HTTPException(status_code=400, detail="WQI must be between 0 and 100")
        
        ph = reading_data.get("ph")
        if ph is not None and not (0 <= ph <= 14):
            raise HTTPException(status_code=400, detail="pH must be between 0 and 14")
        
        # Create database record
        reading = Reading(
            device_id=reading_data["device_id"],
            timestamp=timestamp,
            temperature=reading_data["temperature"],
            ec=reading_data["ec"],
            tds=reading_data["tds"],
            wqi=reading_data["wqi"],
            irrigation_index=reading_data["irrigation_index"],
            ph=ph
        )
        
        db.add(reading)
        db.commit()
        db.refresh(reading)
        
        logger.info(f"Ingested reading from device {reading_data['device_id']} at {timestamp}")
        
        return {"status": "success", "id": reading.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting telemetry: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/latest")
async def get_latest_reading(db: Session = Depends(get_db)):
    """Get the most recent water quality reading"""
    try:
        latest = db.query(Reading).order_by(desc(Reading.timestamp)).first()
        
        if not latest:
            raise HTTPException(status_code=404, detail="No readings found")
        
        return latest.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest reading: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/history")
async def get_history(
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get historical water quality readings"""
    try:
        query = db.query(Reading)
        
        if device_id:
            query = query.filter(Reading.device_id == device_id)
        
        readings = query.order_by(desc(Reading.timestamp)).limit(limit).all()
        
        return [reading.to_dict() for reading in readings]
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get aggregated metrics from all readings"""
    try:
        metrics = db.query(
            func.avg(Reading.temperature).label('avg_temperature'),
            func.avg(Reading.ec).label('avg_ec'),
            func.avg(Reading.wqi).label('avg_wqi'),
            func.avg(Reading.ph).label('avg_ph'),
            func.count(Reading.id).label('total_records')
        ).first()
        
        if not metrics or metrics.total_records == 0:
            return {
                "avg_temperature": 0,
                "avg_ec": 0,
                "avg_wqi": 0,
                "avg_ph": None,
                "total_records": 0
            }
        
        return {
            "avg_temperature": round(float(metrics.avg_temperature), 2),
            "avg_ec": round(float(metrics.avg_ec), 3),
            "avg_wqi": round(float(metrics.avg_wqi), 2),
            "avg_ph": round(float(metrics.avg_ph), 2) if metrics.avg_ph is not None else None,
            "total_records": int(metrics.total_records)
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/devices")
async def get_devices(db: Session = Depends(get_db)):
    """Get list of unique device IDs"""
    try:
        devices = db.query(Reading.device_id).distinct().all()
        return [device[0] for device in devices]
        
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
