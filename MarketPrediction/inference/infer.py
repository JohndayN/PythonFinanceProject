import torch
import joblib
import numpy as np
from MarketPrediction.models.lstm import LSTMModel
from MarketPrediction.services.data_service import load_data
from MarketPrediction.services.train_service import train_model
import config
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# User input
ticker = input("Enter stock ticker(s) separated by comma: ").upper().split(",")
ticker = [t.strip() for t in ticker]

config.TICKERS = ticker

# Scaler and model
model = LSTMModel(
        hidden_dim=config.HIDDEN_DIM,
        num_layers=config.NUM_LAYERS
    ).to(device)

model.eval()
model, scaler = train_model(model, config.TICKERS, config.start_date, config.end_date, config.EPOCHS, config.LR)

# Load data
df = load_data(config.TICKERS, config.start_date, config.end_date)

if len(df) < config.SEQ_LENGTH:
    raise ValueError("Not enough data to create sequence")

scaled = scaler.transform(df.values)

last_seq = scaled[-config.SEQ_LENGTH:]
X = torch.tensor(last_seq, dtype=torch.float32).unsqueeze(0).to(device)

# Prediction
with torch.no_grad():
    pred = model(X).cpu().numpy()

# Reconstruct shape for inverse scaling
dummy = np.zeros((1, df.shape[1]))
dummy[0, -1] = pred[0][0]

pred_price = scaler.inverse_transform(dummy)[0, -1]

print(f"\nNext predicted close price: {pred_price:.2f}")
