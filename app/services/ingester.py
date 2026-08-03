import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from app.core.config import settings
from app.db.models import Earthquake

class DataIngesterService:
    @staticmethod
    def fetch_and_store_latest(db: Session, days_back: int = 1) -> int:
        url = "https://www.seismicportal.eu/fdsnws/event/1/query"
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        params = {
            "format": "json",
            "starttime": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "minmagnitude": settings.MIN_MAGNITUDE,
            "minlatitude": settings.LAT_MIN,
            "maxlatitude": settings.LAT_MAX,
            "minlongitude": settings.LON_MIN,
            "maxlongitude": settings.LON_MAX,
            "limit": 20000
        }

        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return 0

        data = response.json()
        features = data.get('features', [])
        inserted_count = 0

        for feature in features:
            props = feature['properties']
            geom = feature['geometry']['coordinates']

            # Parse UTC ISO string
            quake_time = pd.to_datetime(props['time'], utc=True).to_pydatetime()

            # Prevent duplicate inserts using SQLAlchemy ORM filter
            exists = db.query(Earthquake).filter(
                Earthquake.time == quake_time,
                Earthquake.latitude == geom[1],
                Earthquake.longitude == geom[0]
            ).first()

            if not exists:
                record = Earthquake(
                    time=quake_time,
                    magnitude=float(props['mag']),
                    latitude=geom[1],
                    longitude=geom[0],
                    depth=geom[2],
                    place=props.get('flynn_region', 'Gulf of Suez')
                )
                db.add(record)
                inserted_count += 1

        db.commit()
        return inserted_count
