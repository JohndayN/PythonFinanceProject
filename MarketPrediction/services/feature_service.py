import numpy as np
from sklearn.preprocessing import StandardScaler
import pandas as pd


def create_features(df: pd.DataFrame):

    df = df.copy()

    # normalize column names
    df.columns = [c.lower() for c in df.columns]
    
    print("DF columns:", df.columns.tolist())

    ticker = df.attrs.get("ticker")

    if "date" in df.columns:
        df = df.sort_values("date")
    elif "time" in df.columns:
        df = df.sort_values("time")
    
    # ensure close column exists
    if "close" not in df.columns and "close" in df.columns:
        df["close"] = df["close"]

    if "close" not in df.columns:
        raise ValueError("Close column missing")

    if len(df) < 100:
        raise ValueError("Not enough data to create features")
    
    # lag features
    df["lag_1"] = df["close"].shift(1)
    df["lag_3"] = df["close"].shift(3)
    df["lag_5"] = df["close"].shift(5)

    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_10"] = df["close"].rolling(10).mean()

    df["momentum"] = df["close"] - df["close"].shift(5)

    df["volatility"] = df["close"].rolling(10).std()

    df["return"] = df["close"].pct_change()

    df["target"] = df["return"].shift(-1)

    df = df.dropna()

    df.attrs["ticker"] = ticker

    return df



def scale_split(df, seq_length=30):

    train_ratio = 0.8
    train_size = int(len(df) * train_ratio)

    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]
    
    feature_cols = [
        "lag_1",
        "lag_3",
        "lag_5",
        "ma_5",
        "ma_10",
        "ma_50",
        "momentum",
        "volatility",
        "volume_change"
    ]

    
    target_col = "target"

    X_train_raw = train_df[feature_cols].values
    y_train_raw = train_df[target_col].values

    X_test_raw = test_df[feature_cols].values
    y_test_raw = test_df[target_col].values

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    def create_sequences(X, y):

        X_seq = []
        y_seq = []

        for i in range(len(X) - seq_length):

            X_seq.append(X[i:i + seq_length])
            y_seq.append(y[i + seq_length])

        return np.array(X_seq), np.array(y_seq)

    X_train, y_train = create_sequences(X_train_scaled, y_train_raw)
    X_test, y_test = create_sequences(X_test_scaled, y_test_raw)

    return X_train, y_train, X_test, y_test, scaler