from pydantic import BaseModel
from datetime import datetime

class EarthquakeResponse(BaseModel):
    id: int
    time: datetime
    magnitude: float
    latitude: float
    longitude: float
    depth: float
    place: str | None = None

    class Config:
        from_attributes = True

class ForecastResponse(BaseModel):
    region: str
    target_magnitude: float
    time_window_days: int
    probability_percentage: float        # XGBoost Model Probability
    etas_probability_percentage: float   # Physics-based Temporal ETAS Probability
    calculated_at: datetime
