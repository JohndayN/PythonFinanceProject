import pandas as pd
import joblib
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import *
from FeatureEngineering.feature_engineering import create_features


# Connect MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

all_data = []

print("Loading data from MongoDB...")

for ticker in TICKERS:
    data = list(collection.find({"ticker": ticker}))
    df = pd.DataFrame(data)

    if df.empty:
        continue

    df = create_features(df)
    df["ticker"] = ticker

    all_data.append(df)

# Combine 7 tickers
df_all = pd.concat(all_data, ignore_index=True)

print("Total rows after feature engineering:", len(df_all))


# Select features
FEATURES = [
    "return",
    "volatility_20",
    "volume_change",
    "high_low_spread"
]

X = df_all[FEATURES]

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Isolation Forest
model = IsolationForest(
    n_estimators=300,
    contamination=0.05,
    random_state=42,
    n_jobs=-1
)

print("Training model...")
model.fit(X_scaled)

# Save model + scaler
joblib.dump({
    "model": model,
    "scaler": scaler
}, MODEL_PATH)

print("Model saved.")


# Compute anomaly score
df_all["anomaly_score"] = model.decision_function(X_scaled)
df_all["anomaly_label"] = model.predict(X_scaled)  # -1 anomaly

# Convert to risk score (0–1)
df_all["risk_score"] = 1 - (
    (df_all["anomaly_score"] - df_all["anomaly_score"].min()) /
    (df_all["anomaly_score"].max() - df_all["anomaly_score"].min())
)

# Save results to MongoDB
fraud_collection = db["anomaly_scores"]

fraud_collection.delete_many({})  # optional clean

fraud_collection.insert_many(
    df_all[["ticker", "time", "risk_score", "anomaly_label"]].to_dict("records")
)

print("Anomaly scores stored in MongoDB.")