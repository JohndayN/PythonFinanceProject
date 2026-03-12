import torch
import torch.nn as nn
import joblib
import os

from MarketPrediction.models.lstm import LSTMModel
from MarketPrediction.services.feature_service import create_features, scale_split
from Database.MongoDBManager import get_db_manager

ARTIFACT_DIR = "MarketPrediction/models/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)


def train_model(ticker):

    print(f"\nTraining model for {ticker}")

    db = get_db_manager()
    df = db.get_stock_df(ticker, limit=800)

    if df is None or df.empty:
        raise ValueError(f"No data found for {ticker}")

    df.columns = [c.lower() for c in df.columns]

    print("Columns from MongoDB:", df.columns.tolist())
    print(df.head())

    # Feature engineering
    df = create_features(df)

    print("Columns after feature creation:", df.columns.tolist())

    if len(df) < 100:
        raise ValueError(f"Not enough data to train {ticker}")

    # Split data
    X_train, y_train, X_test, y_test, scaler = scale_split(df)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    input_size = X_train.shape[2]

    model = LSTMModel(input_size=input_size).to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    X_train = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train = torch.tensor(y_train, dtype=torch.float32).to(device)

    X_test = torch.tensor(X_test, dtype=torch.float32).to(device)
    y_test = torch.tensor(y_test, dtype=torch.float32).to(device)

    epochs = 30
    batch_size = 32

    for epoch in range(epochs):

        model.train()

        for i in range(0, len(X_train), batch_size):

            xb = X_train[i:i+batch_size]
            yb = y_train[i:i+batch_size]

            outputs = model(xb)

            loss = criterion(outputs.squeeze(), yb)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if epoch % 5 == 0:
            print(f"Epoch {epoch} Loss {loss.item():.6f}")

    # Evaluate
    model.eval()

    with torch.no_grad():
        test_pred = model(X_test)
        test_loss = criterion(test_pred.squeeze(), y_test)

    print(f"Final Test Loss: {test_loss.item():.6f}")

    # Save model
    model_path = os.path.join(ARTIFACT_DIR, f"{ticker}_model.pth")
    scaler_path = os.path.join(ARTIFACT_DIR, f"{ticker}_scaler.pkl")

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)

    print("Model saved:", model_path)


if __name__ == "__main__":

    tickers = ["FPT", "VNM", "VCB"]

    for t in tickers:
        train_model(t)
