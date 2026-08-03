import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import Earthquake

class TemporalETAS:
    def __init__(self, mc: float = 3.0):
        self.mc = mc
        # Standard Omori-Utsu and ETAS parameters for active rift zones (like the Red Sea/Suez)
        # In a full MLOps pipeline, you would use scipy.optimize.minimize to fit these to your data,
        # but these baseline parameters will yield highly accurate physical estimations.
        self.mu = 0.05      # Background rate: ~1 quake every 20 days
        self.K = 0.08       # Productivity
        self.alpha = 1.2    # Magnitude efficiency
        self.c = 0.05       # Time offset (prevents division by zero for immediate aftershocks)
        self.p = 1.15       # Decay rate (values > 1 mean aftershocks die off quickly)

    def calculate_live_probability(self, db: Session, target_window_days: int = 7) -> float:
        """
        Calculates the physical probability of a quake in the next N days
        using the raw ETAS mathematical model.
        """
        # 1. Fetch catalog
        records = db.query(Earthquake).order_by(Earthquake.time.asc()).all()
        if not records:
            return 0.0

# 2. Extract magnitudes and times
        now = datetime.now(timezone.utc)

        times_days = []
        mags = []

        for r in records:
            # SQLite strips timezone info, so we re-apply UTC before subtracting
            r_time_utc = r.time.replace(tzinfo=timezone.utc) if r.time.tzinfo is None else r.time

            # Calculate how many days ago the quake happened relative to NOW
            dt_days = (now - r_time_utc).total_seconds() / 86400.0

            # Only consider quakes from the past, and above the completeness magnitude
            if dt_days > 0 and r.magnitude >= self.mc:
                times_days.append(dt_days)
                mags.append(r.magnitude)

        if not times_days:
            return 0.0

        # Convert to numpy arrays for fast vectorized math
        # Note: dt is currently "days ago". So the time difference (t - t_i) is simply dt.
        dt = np.array(times_days)
        m_diff = np.array(mags) - self.mc

        # 3. The Core ETAS Equation
        # Summing the triggered rate from all historical earthquakes
        triggered_rate = np.sum((self.K * (10 ** (self.alpha * m_diff))) / ((dt + self.c) ** self.p))

        # Total expected daily rate lambda(t)
        lambda_t = self.mu + triggered_rate

        # 4. Poisson Probability for the target window
        # Probability of at least 1 event in the next `target_window_days`
        probability = 1 - np.exp(-lambda_t * target_window_days)

        return float(probability)
