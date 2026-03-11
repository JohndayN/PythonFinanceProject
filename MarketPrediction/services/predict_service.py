import torch
import joblib
import numpy as np
import pandas as pd
import os
from typing import List, Dict
from Database.MongoDBManager import get_db_manager
from MarketPrediction.models.train_price_model import train_model

MODEL_CACHE = {}
SCALER_CACHE = {}

ARTIFACT_DIR = "MarketPrediction/models/artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def predict(ticker_data, ticker: str = None, days: int = 5) -> List[float]:
    try:
        if isinstance(ticker_data, str):
            ticker = ticker_data
            from MarketPrediction.services.data_service import load_data
            df = load_data(ticker_data)
        else:
            df = ticker_data
            ticker = df.attrs.get("ticker")
            
            if ticker is None:
                raise ValueError("Ticker missing from dataframe. Pass ticker explicitly.")  

        if df is None or df.empty:
            return [0.0] * days
        
        if len(df) < 100:
            print(f"Data for {ticker} not enough to predict. Changing to simple forecast")
            return generate_simple_forecast(df, days)

        # get last price
        if 'Close' in df.columns:
            last_price = float(df['Close'].iloc[-1])
        elif 'close' in df.columns:
            last_price = float(df['close'].iloc[-1])
        else:
            last_price = float(df.iloc[-1, 0])

        model_path = os.path.join(ARTIFACT_DIR, f"{ticker}_model.pth")
        scaler_path = os.path.join(ARTIFACT_DIR, f"{ticker}_scaler.pkl")

        if not os.path.exists(model_path):

            print(f"No model for {ticker}. Training...")

            train_model(ticker)

            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                print("Training failed, using fallback forecast.")
                return generate_simple_forecast(df, days)

        from MarketPrediction.models.lstm import LSTMModel

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if ticker not in MODEL_CACHE:

            scaler = joblib.load(scaler_path)

            model = LSTMModel().to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()

            MODEL_CACHE[ticker] = model
            SCALER_CACHE[ticker] = scaler

        model = MODEL_CACHE[ticker]
        scaler = SCALER_CACHE[ticker]

        seq_length = 30

        feature_cols = [
            "Close",
            "return",
            "ma_10",
            "ma_50",
            "volatility"
        ]
        
        missing = [c for c in feature_cols if c not in df.columns]

        if missing:
            from MarketPrediction.services.feature_service import create_features
            df = create_features(df)

        features = df.reindex(columns=feature_cols).values

        scaled = scaler.transform(features)

        last_seq = scaled[-seq_length:]

        last_seq = torch.tensor(last_seq, dtype=torch.float32).unsqueeze(0).to(device)

        predictions = []
        upper_band = []
        lower_band = []

        current_price = last_price

        returns = df["Close"].pct_change().dropna()

        volatility = returns.std()
        
        if np.isnan(volatility):
            volatility = 0.01
        
        seq_np = last_seq.cpu().numpy()[0]

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

            # update return feature
            new_row[0] = current_price
            new_row[1] = pred_return

            # scale row
            new_row = scaler.transform([new_row])[0]

            seq_np = np.vstack((seq_np[1:], new_row))

            last_seq = torch.tensor(seq_np, dtype=torch.float32).unsqueeze(0).to(device)
            
        manager = get_db_manager()

        manager.save_market_prediction_result(
            ticker=ticker,
            days=days,
            result={
                "predictions": predictions,
                "confidence": float(1 - volatility),
                "status": "completed",
                "model": "LSTM_Attention"
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

def generate_simple_forecast(df: pd.DataFrame, days: int) -> List[float]:
    try:
        if df is None or df.empty:
            return [0.0] * days
        
        # Get close prices
        if 'close' in df.columns:
            prices = df['close'].values
        elif 'Close' in df.columns:
            prices = df['Close'].values
        else:
            prices = df.iloc[:, 0].values
        
        # Calculate average daily return
        returns = np.diff(prices) / prices[:-1]
        avg_return = np.mean(returns) if len(returns) > 0 else 0.0
        
        # Generate forecast
        last_price = float(prices[-1])
        forecast = []
        current_price = last_price
        
        for _ in range(days):
            current_price = current_price * (1 + avg_return)
            forecast.append(float(current_price))
        
        return forecast
    
    except Exception as e:
        print(f"Forecast error: {str(e)}")
        return [0.0] * days
