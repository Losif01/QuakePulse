from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from app.core.database import get_db
from app.db.models import Earthquake
from app.schemas.earthquake import EarthquakeResponse

router = APIRouter()

@router.get("/earthquakes", response_model=List[EarthquakeResponse])
def get_earthquakes(
    start_date: date = Query(..., description="Start date for historical data"),
    limit: int = Query(default=5000, le=10000), # Increased limit to handle 2 years of data safely
    db: Session = Depends(get_db)
):
    """Retrieve historical seismic records filtered by date."""

    # Convert date to a datetime object starting at midnight for accurate database comparison
    start_datetime = datetime.combine(start_date, datetime.min.time())

    return db.query(Earthquake).filter(
        Earthquake.time >= start_datetime
    ).order_by(Earthquake.time.desc()).limit(limit).all()
