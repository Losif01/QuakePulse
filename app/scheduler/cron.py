from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.services.ingester import DataIngesterService

scheduler = AsyncIOScheduler()

def daily_data_pull_job():
    """Executed automatically every 24h at 00:00 UTC"""
    db = SessionLocal()
    try:
        new_records = DataIngesterService.fetch_and_store_latest(db, days_back=2)
        print(f"[CRON 00:00 UTC] Ingestion complete. {new_records} new events added.")
    finally:
        db.close()

def start_scheduler():
    # Run every day at 00:00 UTC
    scheduler.add_job(daily_data_pull_job, 'cron', hour=0, minute=0, timezone='UTC')
    scheduler.start()
