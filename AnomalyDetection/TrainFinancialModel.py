import pandas as pd
import joblib
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import *
from FeatureEngineering.financial_features import create_financial_features

# Connect Mongo
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["financial_statements"]

all_data = []

print("Loading financial data...")

for ticker in TICKERS:
    data = list(collection.find({"ticker": ticker}))
    df = pd.DataFrame(data)

    if df.empty:
        continue

    df = create_financial_features(df)
    df["ticker"] = ticker

    all_data.append(df)

df_all = pd.concat(all_data, ignore_index=True)

print("Total financial rows:", len(df_all))

FEATURES = [
    "roa",
    "roe",
    "debt_to_assets",
    "revenue_growth",
    "accrual_ratio",
    "cf_to_income",
    "beneish_m_score"
]

X = df_all[FEATURES]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = IsolationForest(
    n_estimators=300,
    contamination=0.10,
    random_state=42,
    n_jobs=-1
)

print("Training financial model...")
model.fit(X_scaled)

joblib.dump({
    "model": model,
    "scaler": scaler
}, "saved_models/financial_isolation_forest.pkl")

print("Financial model saved.")

df_all["anomaly_score"] = model.decision_function(X_scaled)
df_all["anomaly_label"] = model.predict(X_scaled)

df_all["financial_risk_score"] = 1 - (
    (df_all["anomaly_score"] - df_all["anomaly_score"].min()) /
    (df_all["anomaly_score"].max() - df_all["anomaly_score"].min())
)

db["financial_anomaly_scores"].delete_many({})
db["financial_anomaly_scores"].insert_many(
    df_all[["ticker", "year", "financial_risk_score", "anomaly_label"]]
    .to_dict("records")
)

print("Financial risk scores stored.")

def compute_beneish(df):

    df = df.sort_values("year")

    df["DSRI"] = (
        (df["receivables"] / df["revenue"]) /
        (df["receivables"].shift(1) / df["revenue"].shift(1))
    )

    df["GMI"] = (
        (df["gross_profit"].shift(1) / df["revenue"].shift(1)) /
        (df["gross_profit"] / df["revenue"])
    )

    df["AQI"] = (
        (1 - (df["current_assets"] + df["ppe"]) / df["total_assets"]) /
        (1 - (df["current_assets"].shift(1) + df["ppe"].shift(1)) / df["total_assets"].shift(1))
    )

    df["SGI"] = df["revenue"] / df["revenue"].shift(1)

    df["DEPI"] = (
        (df["depreciation"].shift(1) / 
            (df["depreciation"].shift(1) + df["ppe"].shift(1))) /
        (df["depreciation"] /
            (df["depreciation"] + df["ppe"]))
    )

    df["SGAI"] = (
        (df["sga"] / df["revenue"]) /
        (df["sga"].shift(1) / df["revenue"].shift(1))
    )

    df["LVGI"] = (
        (df["total_liabilities"] / df["total_assets"]) /
        (df["total_liabilities"].shift(1) / df["total_assets"].shift(1))
    )

    df["TATA"] = (
        (df["net_income"] - df["operating_cash_flow"]) /
        df["total_assets"]
    )

    df["beneish_m_score"] = (
        -4.84
        + 0.92 * df["DSRI"]
        + 0.528 * df["GMI"]
        + 0.404 * df["AQI"]
        + 0.892 * df["SGI"]
        + 0.115 * df["DEPI"]
        - 0.172 * df["SGAI"]
        + 4.679 * df["TATA"]
        - 0.327 * df["LVGI"]
    )

    return df

df = create_financial_features(df)
df = compute_beneish(df)

df["final_financial_risk"] = (
    0.7 * df["financial_risk_score"] +
    0.3 * df["beneish_risk_score"]
)