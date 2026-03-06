import pandas as pd
from pymongo import MongoClient
from config import *

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

df = pd.DataFrame(list(db["hybrid_fraud_scores"].find()))

df["time"] = pd.to_datetime(df["time"])
df = df.sort_values(["ticker", "time"])

trend_results = []

for ticker in df["ticker"].unique():
    temp = df[df["ticker"] == ticker].copy()

    # Moving average (3-period)
    temp["risk_ma3"] = temp["final_fraud_score"].rolling(3).mean()

    # Risk change rate
    temp["risk_change"] = temp["final_fraud_score"].diff()

    # Risk acceleration
    temp["risk_acceleration"] = temp["risk_change"].diff()

    # Escalation flag
    temp["escalation_flag"] = temp["risk_change"].apply(
        lambda x: 1 if x > 0.15 else 0
    )

    trend_results.append(temp)

df_trend = pd.concat(trend_results)

db["risk_trend_analysis"].delete_many({})
db["risk_trend_analysis"].insert_many(
    df_trend.to_dict("records")
)

print("Trend analysis stored.")