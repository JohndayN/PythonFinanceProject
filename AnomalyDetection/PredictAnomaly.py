import joblib
import numpy as np

model = joblib.load("saved_models/isolation_forest.pkl")

def final_risk_score(numeric_features, text_score):
    anomaly_score = model.decision_function([numeric_features])[0]

    # Normalize anomaly score
    anomaly_risk = 1 - anomaly_score

    # Weighted combination
    final_score = 0.7 * anomaly_risk + 0.3 * text_score

    return round(final_score, 4)