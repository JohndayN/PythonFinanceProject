import numpy as np
from sklearn.preprocessing import StandardScaler

def split_data(df, train_ratio):
    train_size = int(len(df) * train_ratio)
    train_df = df[:train_size]
    test_df = df[train_size:]
    return train_df, test_df

def scale_data(train_df, test_df):
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_df)
    test_scaled = scaler.transform(test_df)
    return train_scaled, test_scaled, scaler

def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

def add_features(df):
    df = df.copy()

    df["return"] = df["Close"].pct_change()
    df["ma_10"] = df["Close"].rolling(10).mean()
    df["ma_50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["return"].rolling(20).std()

    df["target"] = (df["return"].shift(-1) > 0).astype(int)

    df = df.dropna()

    return df
