import numpy as np
from sklearn.ensemble import IsolationForest


def detect_anomalies(series, contamination=0.01):
    data = np.asarray(series, dtype=float).reshape(-1, 1)
    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(data)
    return predictions
