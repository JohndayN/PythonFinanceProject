import os
import torch
import joblib
from torch.utils.data import DataLoader, TensorDataset
from MarketPrediction.models.lstm import LSTMModel
from MarketPrediction.services.data_service import load_data
from MarketPrediction.services.feature_service import scale_split

def train_model(ticker, epochs=20, lr=0.001, batch_size=32):

    os.makedirs("artifacts", exist_ok=True)

    df = load_data(ticker)
    X_train, y_train, X_val, y_val, scaler = scale_split(df)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = LSTMModel().to(device)
    model.train()

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)

    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

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

        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss:.6f}")

    # Save artifacts
    torch.save(model.state_dict(), f"artifacts/{ticker}_model.pth")
    joblib.dump(scaler, f"artifacts/{ticker}_scaler.pkl")

    return {"status": "trained", "ticker": ticker}
