import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(df):
    model = IsolationForest(
        n_estimators=100,
        contamination=0.08,
        random_state=42
    )

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    df["anomaly"] = model.fit_predict(df[["amount"]])
    df["anomaly"] = df["anomaly"].map({1: 0, -1: 1})

    return df
