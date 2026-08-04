import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Earthquake
from app.services.ml_engine import MLEngine
from app.services.etas_engine import TemporalETAS

# ---------------------------------------------------------
# DIRECT DATABASE CONNECTION SETUP
# ---------------------------------------------------------
DB_PATH = os.path.abspath("data/Hezny.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------
# DIRECT DATA FETCHERS
# ---------------------------------------------------------
def get_live_forecast_data():
    db = SessionLocal()
    try:
        ml_engine = MLEngine()
        xgb_prob = ml_engine.predict_live(db)

        etas_engine = TemporalETAS(mc=3.0)
        etas_prob = etas_engine.calculate_live_probability(db, target_window_days=7)

        return {
            "region": "Gulf of Suez, Egypt",
            "target_magnitude": 3.5,
            "time_window_days": 7,
            "probability_percentage": round(xgb_prob * 100, 2),
            "etas_probability_percentage": round(etas_prob * 100, 2),
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()


def get_earthquake_records(start_date: date):
    db = SessionLocal()
    try:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        records = (
            db.query(Earthquake)
            .filter(Earthquake.time >= start_datetime)
            .order_by(Earthquake.time.desc())
            .all()
        )

        data = []
        for r in records:
            data.append({
                "id": r.id,
                "time": r.time,
                "magnitude": r.magnitude,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "depth": r.depth,
                "place": r.place
            })
        return data
    finally:
        db.close()


# ---------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="QuakePulse | Gulf of Suez Dashboard (Demo)",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title & Subtitle
st.title("🌋 QuakePulse: Seismic Forecast & Analytics")
st.caption("Real-time seismic data ingestion & probabilistic forecasting for the Gulf of Suez")

# ---------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.header("System Status & Controls")

# Blue status badge requested for cloud demo deployment
st.sidebar.info("Backend API: Status: Demo 🔵")

today = date.today()
two_years_ago = today - timedelta(days=730)
start_date = st.sidebar.date_input("Historical Data Start Date", value=two_years_ago, max_value=today)

refresh_btn = st.sidebar.button("🔄 Refresh Data")


# ---------------------------------------------------------
# CACHED DATA LOADERS
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_forecast():
    try:
        return get_live_forecast_data()
    except Exception as e:
        st.error(f"Error executing forecast inference: {e}")
        return None

@st.cache_data(ttl=60)
def fetch_earthquakes(selected_date: date):
    try:
        data = get_earthquake_records(selected_date)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error querying earthquake database: {e}")
        return pd.DataFrame()

if refresh_btn:
    st.cache_data.clear()

forecast_data = fetch_forecast()
df_quakes = fetch_earthquakes(start_date)


# ---------------------------------------------------------
# SECTION 1: LIVE FORECAST METRICS
# ---------------------------------------------------------
st.subheader("Live Seismic Hazard Forecast")

col1, col2, col3, col4 = st.columns(4)

if forecast_data:
    xgb_prob = forecast_data.get("probability_percentage", 0.0)
    etas_prob = forecast_data.get("etas_probability_percentage", 0.0)
    target_mag = forecast_data.get("target_magnitude", 3.5)
    region = forecast_data.get("region", "Gulf of Suez")
    calculated_at = forecast_data.get("calculated_at", "")

    if xgb_prob < 20:
        xgb_color = "🟢 Baseline"
    elif xgb_prob < 40:
        xgb_color = "🟡 Post-Swarm"
    else:
        xgb_color = "🔴 Elevated"

    with col1:
        st.metric(
            label=f"XGBoost ML (≥ M{target_mag})",
            value=f"{xgb_prob:.2f}%",
            delta=xgb_color
        )

    with col2:
        st.metric(
            label=f"ETAS Physics (≥ M{target_mag})",
            value=f"{etas_prob:.2f}%",
            delta="⚛️ Omori-Utsu Decay",
            delta_color="off"
        )

    with col3:
        st.metric(
            label="Monitored Region",
            value=region
        )

    with col4:
        st.metric(
            label="Last Inferred At (UTC)",
            value=calculated_at[:19].replace("T", " ") if calculated_at else "N/A"
        )

    st.markdown("---")

    if etas_prob > 90 and xgb_prob < 50:
        with st.expander("💡 Model Insights: Why is ETAS at 100% while XGBoost is lower?", expanded=True):
            st.markdown(f"""
            **Don't panic! A 100% ETAS probability does not mean a massive earthquake is imminent.**

            These two models look at the fault line using entirely different methods:

            * **ETAS (The Physics):** ETAS calculates the rigid laws of physics (*Omori-Utsu Law*). Because a large energy release just occurred, the math dictates it is **100% certain** the fault will produce minor aftershocks as it settles. However, ETAS predicts *occurrence*, not magnitude (*Gutenberg-Richter Law*). It is virtually guaranteeing a tremor ≥ M3.0, but statistically, it is overwhelmingly likely to be a harmless 3.1 or 3.2.
            * **XGBoost (The Machine Learning):** The XGBoost model doesn't calculate rigid physics; it looks for historical patterns. It reviewed 36 years of Gulf of Suez data and concluded that while minor aftershocks are guaranteed, the probability of them coalescing into a notable, separate event (≥ M{target_mag}) in the next 7 days is only **~{xgb_prob:.0f}%**.

            **The Verdict:** The fault is behaving exactly as expected after a moderate quake. Minor, imperceptible aftershocks are occurring, but the overall risk of a dangerous secondary event remains moderate.
            """)
    else:
        with st.expander("💡 Understanding the Dual-Model System"):
            st.markdown("""
            * **XGBoost ML:** Evaluates the historical probability of an event based on 36 years of tectonic energy patterns.
            * **ETAS Physics:** Calculates the deterministic Omori-Utsu physical decay rate of the fault line.
            """)

else:
    st.warning("No forecast data returned.")

st.divider()


# ---------------------------------------------------------
# SECTION 2: MAP & HISTORICAL ANALYTICS
# ---------------------------------------------------------
st.subheader("Regional Epicenter Map & Historical Activity")

if not df_quakes.empty:
    fig_map = px.scatter_mapbox(
        df_quakes,
        lat="latitude",
        lon="longitude",
        color="magnitude",
        size="magnitude",
        hover_name="place",
        hover_data={"magnitude": True, "depth": True, "time": True},
        color_continuous_scale="Reds",
        size_max=15,
        zoom=6.5,
        center={"lat": 28.0, "lon": 33.5},
        mapbox_style="open-street-map",
        title=f"Earthquake Epicenters since {start_date}"
    )
    fig_map.update_layout(margin={"r":0, "t":40, "l":0, "b":0})
    st.plotly_chart(fig_map, use_container_width=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Magnitude Distribution")
        fig_hist = px.histogram(
            df_quakes,
            x="magnitude",
            nbins=20,
            title="Frequency by Magnitude",
            labels={"magnitude": "Magnitude", "count": "Event Count"},
            color_discrete_sequence=["#FF4B4B"]
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_chart2:
        st.subheader("Event Timeline")
        fig_time = px.scatter(
            df_quakes,
            x="time",
            y="magnitude",
            color="depth",
            title="Seismic Events over Time",
            labels={"time": "Date/Time", "magnitude": "Magnitude", "depth": "Depth (km)"},
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("Raw Catalog Records")
    st.dataframe(df_quakes, use_container_width=True)

else:
    st.info(f"No earthquake records found starting from {start_date}.")
