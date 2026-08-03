import xgboost as xgb
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import Earthquake

class MLEngine:
    _instance = None
    model: xgb.XGBClassifier | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLEngine, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        self.model = xgb.XGBClassifier()
        # Assumes model.json exists in settings.MODEL_PATH
        try:
            self.model.load_model(settings.MODEL_PATH)
        except Exception:
            self.model = None

    def predict_live(self, db: Session) -> float:
        if not self.model:
            return 0.0

        # Query recent earthquakes to calculate rolling features
        records = db.query(Earthquake).order_by(Earthquake.time.desc()).limit(500).all()
        if not records:
            return 0.0

        df = pd.DataFrame([{
            'time': r.time,
            'mag': r.magnitude,
            'energy': 10 ** (1.5 * r.magnitude)
        } for r in records])

        df['time'] = pd.to_datetime(df['time'], utc=True)
        df.set_index('time', inplace=True)

        daily = df.resample('D').agg(
            quake_count=('mag', 'count'),
            total_energy=('energy', 'sum')
        ).fillna(0)

        # Feature extraction matching training pipeline
        energy_7d = daily['total_energy'].rolling(window=7, min_periods=1).sum().iloc[-1]
        count_7d = daily['quake_count'].rolling(window=7, min_periods=1).sum().iloc[-1]
        energy_30d = daily['total_energy'].rolling(window=30, min_periods=1).sum().iloc[-1]
        count_30d = daily['quake_count'].rolling(window=30, min_periods=1).sum().iloc[-1]

        features = pd.DataFrame([{
            'energy_7d': energy_7d,
            'count_7d': count_7d,
            'energy_30d': energy_30d,
            'count_30d': count_30d
        }])

        prob = self.model.predict_proba(features)[0][1]
        return float(prob)
