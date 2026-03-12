import numpy as np
from sklearn.preprocessing import StandardScaler

def split_data(df, train_ratio):
    train_size = int(len(df) * train_ratio)
    train_df = df[:train_size]
    test_df = df[train_size:]
    return train_df, test_df

def scale_data(train_df, test_df):

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

    scaler = StandardScaler()

    X_train = scaler.fit_transform(train_df[feature_cols])
    X_test = scaler.transform(test_df[feature_cols])

    y_train = train_df["target"].values
    y_test = test_df["target"].values

    return X_train, X_test, y_train, y_test, scaler

def create_sequences(X, y, seq_length):

    X_seq = []
    y_seq = []

    for i in range(len(X) - seq_length):

        X_seq.append(X[i:i + seq_length])
        y_seq.append(y[i + seq_length])

    return np.array(X_seq), np.array(y_seq)

def add_features(df):
    df = df.copy()

    df["return"] = df["Close"].pct_change()
    df["ma_10"] = df["Close"].rolling(10).mean()
    df["ma_50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["return"].rolling(20).std()

    df["target"] = df["return"].shift(-1)

    df = df.dropna()

    return df

def preprocess_pipeline(df, seq_length=30, train_ratio=0.8):

    df = add_features(df)

    train_df, test_df = split_data(df, train_ratio)

    X_train, X_test, y_train, y_test, scaler = scale_data(train_df, test_df)

    X_train, y_train = create_sequences(X_train, y_train, seq_length)
    X_test, y_test = create_sequences(X_test, y_test, seq_length)

    return X_train, y_train, X_test, y_test, scaler