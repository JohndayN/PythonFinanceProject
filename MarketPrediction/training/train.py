import pandas as pd
import numpy as np

def add_features(df):
    df = df.copy()

    df["return"] = df["Close"].pct_change()
    df["ma_10"] = df["Close"].rolling(10).mean()
    df["ma_50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["return"].rolling(20).std()

    df["target"] = (df["return"].shift(-1) > 0).astype(int)

    df = df.dropna()

    return df
