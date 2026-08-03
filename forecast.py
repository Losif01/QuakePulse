import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_auc_score, classification_report

# 1. Load the clean catalog
print("Loading catalog...")
df = pd.read_csv("emsc_catalog_egypt.csv")
df['time'] = pd.to_datetime(df['time'], utc=True, format = "mixed")
df = df.sort_values('time').reset_index(drop=True)

# 2. Calculate Relative Seismic Energy
# Using the standard Gutenberg-Richter energy relation approximation
df['energy'] = 10 ** (1.5 * df['mag'])

# 3. Resample to Daily Grids
# We create a continuous daily timeline from 1990 to 2026
df.set_index('time', inplace=True)
daily = df.resample('D').agg(
    quake_count=('mag', 'count'),
    max_mag=('mag', 'max'),
    total_energy=('energy', 'sum')
).fillna(0)

# 4. Feature Engineering (Simulating ETAS parameters)
print("Engineering rolling features...")
# Short-term momentum (7 days)
daily['energy_7d'] = daily['total_energy'].rolling(window=7, min_periods=1).sum()
daily['count_7d'] = daily['quake_count'].rolling(window=7, min_periods=1).sum()

# Long-term background rate (30 days)
daily['energy_30d'] = daily['total_energy'].rolling(window=30, min_periods=1).sum()
daily['count_30d'] = daily['quake_count'].rolling(window=30, min_periods=1).sum()

# 5. Define the Target Variable
# Will a quake >= M3.5 happen in the next 7 days?
target_mag = 3.5
# Look ahead 7 days, get the max magnitude, check if it meets the threshold
daily['future_max_mag'] = daily['max_mag'].shift(-7).rolling(window=7, min_periods=1).max()
daily['target'] = (daily['future_max_mag'] >= target_mag).astype(int)

# Drop rows at the very end where we can't look 7 days into the future
ml_data = daily.dropna().copy()

print(f"Dataset ready: {len(ml_data)} daily records.")
print(f"Positive forecast targets (>M{target_mag} in next 7 days): {ml_data['target'].sum()}")

# 6. Train/Test Split
# Time-series split (Train on 1990-2020, Test on 2020-2026)
features = ['energy_7d', 'count_7d', 'energy_30d', 'count_30d']
X = ml_data[features]
y = ml_data['target']

split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# 7. Train the XGBoost Model
print("\nTraining XGBoost Forecaster...")
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.05,
    objective='binary:logistic', # We want probabilities, not just 0 or 1
    eval_metric='auc',
    random_state=42
)

model.fit(X_train, y_train)

# 8. Evaluate
preds_proba = model.predict_proba(X_test)[:, 1]
roc_auc = roc_auc_score(y_test, preds_proba)
print(f"Model ROC-AUC Score: {roc_auc:.4f} (1.0 is perfect, 0.5 is random guessing)")

# 9. Live Forecast for Today
latest_features = X.tail(1)
live_prob = model.predict_proba(latest_features)[0][1]

print("\n" + "="*40)
print(f"🌍 LIVE FORECAST: GULF OF SUEZ")
print(f"Probability of an event >= M{target_mag} in the next 7 days:")
print(f"-> {live_prob * 100:.2f}%")
print("="*40)
