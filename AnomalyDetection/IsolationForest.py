import numpy as np
from sklearn.ensemble import IsolationForest


def compute_risk_score(X, contamination=0.02):
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42
    )

    model.fit(X)

    scores = model.decision_function(X)

    # Convert anomaly → risk
    anomaly_strength = -scores

    # Normalize 0–1
    min_s = anomaly_strength.min()
    max_s = anomaly_strength.max()

    risk_score = (anomaly_strength - min_s) / (max_s - min_s + 1e-9)

    return risk_score