import numpy as np
from sklearn.preprocessing import StandardScaler

def scale_split(df, seq_length=30):
    train_ratio = 0.8
    train_size = int(len(df) * train_ratio)

    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_df)
    test_scaled = scaler.transform(test_df)

    def create_sequences(data):
        X, y = [], []
        for i in range(len(data) - seq_length - 1):
            X.append(data[i:i+seq_length])
            y.append(data[i+seq_length])
        return np.array(X), np.array(y)

    X_train, y_train = create_sequences(train_scaled)
    X_test, y_test = create_sequences(test_scaled)

    return X_train, y_train, X_test, y_test, scaler
