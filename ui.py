import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
# Page configuration
st.set_page_config(
    page_title="QuakePulse | Gulf of Suez Dashboard",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1")

# Styling custom CSS
st.markdown("""
    <style>
    .metric-box {
        background-color: #1e222d;
        border-radius: 8px;
        padding: 20px;
        border: 1px solid #2e3440;
    }
    </style>
""", unsafe_allow_html=True)

# App Title & Subtitle
st.title("QuakePulse: Seismic Forecast & Analytics")
st.caption("Real-time seismic data ingestion & XGBoost probabilistic forecasting for the Gulf of Suez")

# Sidebar Controls
st.sidebar.header("System Status & Controls")

# API Health Check
try:
    health_check = requests.get(f"{API_BASE_URL}/forecast", timeout=3)
    if health_check.status_code == 200:
        st.sidebar.success("Backend API: Online 🟢")
    else:
        st.sidebar.error(f"Backend API: Issue ({health_check.status_code}) 🔴")
except Exception:
    st.sidebar.error("Backend API: Offline 🔴\n(Ensure FastAPI is running on port 8000)")

# --- NEW DATE PICKER ---
today = date.today()
two_years_ago = today - timedelta(days=730)
start_date = st.sidebar.date_input("Historical Data Start Date", value=two_years_ago, max_value=today)

refresh_btn = st.sidebar.button("🔄 Refresh Data")

# Data Fetching Helpers
@st.cache_data(ttl=60)
def fetch_forecast():
    try:
        res = requests.get(f"{API_BASE_URL}/forecast", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None
    return None

# --- UPDATED FETCH FUNCTION ---
@st.cache_data(ttl=60)
def fetch_earthquakes(start_date_str: str):
    try:
        res = requests.get(f"{API_BASE_URL}/earthquakes?start_date={start_date_str}", timeout=5)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()

if refresh_btn:
    st.cache_data.clear()

# Load Data (passing the ISO formatted date string)
forecast_data = fetch_forecast()
df_quakes = fetch_earthquakes(start_date.isoformat())

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

    # XGBoost Risk Badge
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
            delta="Omori-Utsu Decay",
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

    # Dynamic Context Explainer
    st.markdown("---")

    # Trigger the explanation if ETAS is extremely high and diverges from XGBoost
    if etas_prob > 90 and xgb_prob < 50:
        with st.expander("Model Insights: Why is ETAS at 100% while XGBoost is lower?", expanded=True):
            st.markdown(f"""
            **Don't panic! A 100% ETAS probability does not mean a massive earthquake is imminent.**

            These two models look at the fault line using entirely different methods:

            * **ETAS (The Physics):** ETAS calculates the rigid laws of physics (*Omori-Utsu Law*). Because a large energy release just occurred, the math dictates it is **100% certain** the fault will produce minor aftershocks as it settles. However, ETAS predicts *occurrence*, not magnitude (*Gutenberg-Richter Law*). It is virtually guaranteeing a tremor ≥ M3.0, but statistically, it is overwhelmingly likely to be a harmless 3.1 or 3.2.
            * **XGBoost (The Machine Learning):** The XGBoost model doesn't calculate rigid physics; it looks for historical patterns. It reviewed 36 years of Gulf of Suez data and concluded that while minor aftershocks are guaranteed, the probability of them coalescing into a notable, separate event (≥ M{target_mag}) in the next 7 days is only **~{xgb_prob:.0f}%**.

            **The Verdict:** The fault is behaving exactly as expected after a moderate quake. Minor, imperceptible aftershocks are occurring, but the overall risk of a dangerous secondary event remains moderate.
            """)
    else:
        with st.expander(" Understanding the Dual-Model System"):
            st.markdown("""
            * **XGBoost ML:** Evaluates the historical probability of an event based on 36 years of tectonic energy patterns.
            * **ETAS Physics:** Calculates the deterministic Omori-Utsu physical decay rate of the fault line.
            """)

else:
    st.warning("Unable to reach `/api/v1/forecast`. Please start the FastAPI backend server.")

st.divider()

# ---------------------------------------------------------
# SECTION 2: MAP & MAGNITUDE DISTRIBUTION
# ---------------------------------------------------------
if not df_quakes.empty:
    df_quakes['time'] = pd.to_datetime(df_quakes['time'], format = "mixed", utc= True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader(" Recent Epicenters Map")
        fig_map = px.scatter_mapbox(
            df_quakes,
            lat="latitude",
            lon="longitude",
            size="magnitude",
            color="magnitude",
            color_continuous_scale="Reds",
            size_max=15,
            zoom=6.5,
            center={"lat": 28.75, "lon": 33.5},
            hover_name="place",
            hover_data={"time": True, "magnitude": True, "depth": True, "latitude": False, "longitude": False},
            mapbox_style="carto-darkmatter",
            title="Spatial Distribution of Recent Events"
        )
        fig_map.update_layout(margin={"r":0, "t":30, "l":0, "b":0})
        st.plotly_chart(fig_map, use_container_width=True)

    with col_right:
        st.subheader("Magnitude Timeline")
        fig_time = px.scatter(
            df_quakes,
            x="time",
            y="magnitude",
            size="magnitude",
            color="depth",
            color_continuous_scale="Viridis",
            labels={"time": "Date", "magnitude": "Magnitude (M)", "depth": "Depth (km)"},
            title="Event Sequence & Depth Profiles"
        )
        fig_time.update_layout(margin={"r":0, "t":30, "l":0, "b":0})
        st.plotly_chart(fig_time, use_container_width=True)

    # ---------------------------------------------------------
    # SECTION 3: RECENT CATALOG DATA TABLE
    # ---------------------------------------------------------
    st.subheader("Ingested Catalog Records")
    st.dataframe(
        df_quakes[['time', 'magnitude', 'depth', 'latitude', 'longitude', 'place']],
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No earthquake data available to map. Run `seed_db.py` or fetch recent events via the API.")
