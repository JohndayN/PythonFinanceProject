import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
import os

from MarketPrediction.models.lstm import LSTMModel
from MarketPrediction.services.feature_service import create_features
from MarketPrediction.services.data_service import load_data
from MarketPrediction.services.feature_service import scale_split


def train_model(ticker):

    print(f"Training model for {ticker}")

    df = load_data(ticker)

    df = create_features(df)

    X_train, y_train, X_test, y_test, scaler = scale_split(df)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = LSTMModel(input_size=5).to(device)

    criterion = nn.MSELoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    X_train = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train = torch.tensor(y_train, dtype=torch.float32).to(device)

    epochs = 30

    for epoch in range(epochs):

        model.train()

        optimizer.zero_grad()

        outputs = model(X_train)

        loss = criterion(outputs.squeeze(), y_train)

        loss.backward()

        optimizer.step()

        if epoch % 5 == 0:
            print(f"Epoch {epoch} Loss {loss.item():.4f}")

    os.makedirs("MarketPrediction/models/artifacts", exist_ok=True)

    torch.save(
        model.state_dict(),
        f"MarketPrediction/models/artifacts/{ticker}_model.pth"
    )

    joblib.dump(
        scaler,
        f"MarketPrediction/models/artifacts/{ticker}_scaler.pkl"
    )

    print("Model saved.")


if __name__ == "__main__":

    tickers = ["FPT", "VNM", "VCB"]

    for t in tickers:
        train_model(t)