from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.router import api_router
from app.scheduler.cron import start_scheduler, scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if missing and start 00:00 cron job
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # Shutdown: Cleanly stop scheduler
    scheduler.shutdown()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")
