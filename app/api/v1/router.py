from fastapi import APIRouter
from app.api.v1.endpoints import forecast, earthquakes

api_router = APIRouter()
api_router.include_router(forecast.router, tags=["Forecast"])
api_router.include_router(earthquakes.router, tags=["Earthquakes"])
