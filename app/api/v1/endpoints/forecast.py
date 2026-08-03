from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.schemas.earthquake import ForecastResponse
from app.services.ml_engine import MLEngine
from app.services.etas_engine import TemporalETAS

router = APIRouter()

@router.get("/forecast", response_model=ForecastResponse)
def get_live_forecast(db: Session = Depends(get_db)):
    """Runs model inference on demand against the latest database records

    using both XGBoost (Feature-Engineered) and Temporal ETAS (Physics-Based).
    """
    # 1. XGBoost Inference
    ml_engine = MLEngine()
    xgb_prob = ml_engine.predict_live(db)

    # 2. Raw Temporal ETAS Inference
    etas_engine = TemporalETAS(mc=3.0)
    etas_prob = etas_engine.calculate_live_probability(db, target_window_days=7)

    return ForecastResponse(
        region="Gulf of Suez, Egypt",
        target_magnitude=3.5,
        time_window_days=7,
        probability_percentage=round(xgb_prob * 100, 2),
        etas_probability_percentage=round(etas_prob * 100, 2),
        calculated_at=datetime.now(timezone.utc)
    )
