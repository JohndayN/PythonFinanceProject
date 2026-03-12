import torch
import joblib
import numpy as np
import pandas as pd
import os

from Database.MongoDBManager import get_db_manager
from MarketPrediction.models.train_price_model import train_model
from MarketPrediction.services.feature_service import create_features
from MarketPrediction.models.lstm import LSTMModel

MODEL_CACHE = {}
SCALER_CACHE = {}
TRAINING_LOCK = set()

ARTIFACT_DIR = "MarketPrediction/models/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)


def predict(df: pd.DataFrame, ticker: str, days: int = 5):

    try:

        if df is None or df.empty:
            raise ValueError("Dataframe empty")

        df.columns = [c.lower() for c in df.columns]

        # ----------------------------
        # FEATURE SET
        # ----------------------------

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

        df = create_features(df)

        seq_length = 30

        if len(df) < seq_length:
            return generate_simple_forecast(df, days)

        # ----------------------------
        # LAST PRICE
        # ----------------------------

        if "close" in df.columns:
            last_price = float(df["close"].iloc[-1])
        else:
            last_price = float(df.iloc[-1, 0])

        # ----------------------------
        # MODEL PATH
        # ----------------------------

        model_path = os.path.join(ARTIFACT_DIR, f"{ticker}_model.pth")
        scaler_path = os.path.join(ARTIFACT_DIR, f"{ticker}_scaler.pkl")

        # ----------------------------
        # TRAIN MODEL IF MISSING
        # ----------------------------

        if not os.path.exists(model_path):

            if ticker not in TRAINING_LOCK:

                TRAINING_LOCK.add(ticker)

                try:
                    print(f"No model for {ticker}. Training...")
                    train_model(ticker)
                finally:
                    TRAINING_LOCK.remove(ticker)

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):

            print("Training failed, using fallback forecast.")

            return generate_simple_forecast(df, days)

        # ----------------------------
        # LOAD MODEL FROM CACHE
        # ----------------------------

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if ticker not in MODEL_CACHE:

            scaler = joblib.load(scaler_path)

            model = LSTMModel(input_size=len(feature_cols)).to(device)

            model.load_state_dict(torch.load(model_path, map_location=device))

            model.eval()

            MODEL_CACHE[ticker] = model
            SCALER_CACHE[ticker] = scaler

        model = MODEL_CACHE[ticker]
        scaler = SCALER_CACHE[ticker]

        # ----------------------------
        # FEATURE CHECK
        # ----------------------------

        missing = [c for c in feature_cols if c not in df.columns]

        if missing:
            raise ValueError(f"Missing features: {missing}")

        features = df[feature_cols].values

        scaled = scaler.transform(features)

        last_seq = scaled[-seq_length:]

        last_seq = torch.tensor(last_seq, dtype=torch.float32).unsqueeze(0).to(device)

        predictions = []
        upper_band = []
        lower_band = []

        current_price = last_price

        returns = df["close"].pct_change().dropna()

        volatility = returns.std()

        if np.isnan(volatility):
            volatility = 0.01

        seq_np = last_seq.cpu().numpy()[0]

        # ----------------------------
        # ROLLING FORECAST
        # ----------------------------

        for _ in range(days):

            with torch.no_grad():
                pred = model(last_seq)

            pred_return = float(pred.cpu().numpy()[0][0])

            current_price = current_price * (1 + pred_return)

            predictions.append(float(current_price))

            band = current_price * volatility * 2

            upper_band.append(current_price + band)
            lower_band.append(current_price - band)

            new_row = seq_np[-1].copy()

            # update lag features
            new_row[0] = current_price   # lag_1
            new_row[1] = seq_np[-1][0]   # lag_3 shift
            new_row[2] = seq_np[-1][1]   # lag_5 shift

            seq_np = np.vstack((seq_np[1:], new_row))

            last_seq = torch.tensor(seq_np, dtype=torch.float32).unsqueeze(0).to(device)

        # ----------------------------
        # SAVE RESULT
        # ----------------------------

        manager = get_db_manager()

        manager.save_market_prediction_result(
            ticker=ticker,
            days=days,
            result={
                "predictions": predictions,
                "confidence": float(1 - volatility),
                "status": "completed",
                "model": "LSTM"
            }
        )

        return {
            "prediction": predictions,
            "upper": upper_band,
            "lower": lower_band
        }

    except Exception as e:

        print(f"Prediction error: {str(e)}")

        return generate_simple_forecast(df, days)


# ---------------------------------
# SIMPLE FORECAST FALLBACK
# ---------------------------------

def generate_simple_forecast(df: pd.DataFrame, days: int):

    try:

        if df is None or df.empty:
            return {
                "prediction": [0.0] * days,
                "upper": [0.0] * days,
                "lower": [0.0] * days
            }

        if "close" in df.columns:
            prices = df["close"].values
        else:
            prices = df.iloc[:, 0].values

        returns = np.diff(prices) / prices[:-1]

        avg_return = np.mean(returns) if len(returns) > 0 else 0.0

        last_price = float(prices[-1])

        forecast = []
        current_price = last_price

        for _ in range(days):

            current_price = current_price * (1 + avg_return)

            forecast.append(float(current_price))

        return {
            "prediction": forecast,
            "upper": forecast,
            "lower": forecast
        }

    except Exception as e:

        print(f"Forecast error: {str(e)}")

        return {
            "prediction": [0.0] * days,
            "upper": [0.0] * days,
            "lower": [0.0] * days
        }
