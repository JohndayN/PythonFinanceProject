import os
import torch
import joblib

from torch.utils.data import DataLoader, TensorDataset

from MarketPrediction.models.lstm import LSTMModel
from MarketPrediction.services.data_service import load_data
from MarketPrediction.services.feature_service import create_features, scale_split


ARTIFACT_DIR = "MarketPrediction/models/artifacts"


def train_model(ticker, epochs=20, lr=0.001, batch_size=32):

    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    df = load_data(ticker)

    if df is None or df.empty:
        raise ValueError(f"No data found for {ticker}")

    df = create_features(df)

    if len(df) < 100:
        raise ValueError("Not enough data to train")

    X_train, y_train, X_val, y_val, scaler = scale_split(df)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = LSTMModel().to(device)
    model.train()

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)

    X_val = torch.tensor(X_val, dtype=torch.float32)
    y_val = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)

    train_dataset = TensorDataset(X_train, y_train)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    criterion = torch.nn.MSELoss()

    for epoch in range(epochs):

        total_loss = 0

        for X_batch, y_batch in train_loader:

            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad()

            output = model(X_batch)

            loss = criterion(output, y_batch)

            loss.backward()

            optimizer.step()

            total_loss += loss.item()

        model.eval()

        with torch.no_grad():

            val_output = model(X_val.to(device))

            val_loss = criterion(val_output, y_val.to(device)).item()

        model.train()

        print(
            f"Epoch {epoch+1}/{epochs} | "
            f"Train Loss: {total_loss:.6f} | "
            f"Val Loss: {val_loss:.6f}"
        )

    model.eval()

    torch.save(
        model.state_dict(),
        f"{ARTIFACT_DIR}/{ticker}_model.pth"
    )

    joblib.dump(
        scaler,
        f"{ARTIFACT_DIR}/{ticker}_scaler.pkl"
    )

    return {
        "status": "trained",
        "ticker": ticker
    }