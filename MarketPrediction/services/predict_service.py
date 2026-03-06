import torch
import joblib
import numpy as np
import pandas as pd
import os
from typing import List, Union, Optional

def predict(ticker_data, days: int = 5) -> List[float]:
    try:
        # Handle both DataFrame and string ticker inputs
        if isinstance(ticker_data, str):
            from MarketPrediction.services.data_service import load_data
            df = load_data(ticker_data)
        else:
            df = ticker_data
        
        if df is None or df.empty:
            # Return simple trend continuation as fallback
            return generate_simple_forecast(df, days) if df is not None else [0.0] * days
        
        # Get the last close price
        if 'Close' in df.columns:
            last_price = df['Close'].iloc[-1]
        elif 'close' in df.columns:
            last_price = df['close'].iloc[-1]
        else:
            last_price = df.iloc[-1, 0]  # Use first numeric column
        
        # Try to load trained model if available
        try:
            if isinstance(ticker_data, str):
                model_path = f"MarketPrediction/models/artifacts/{ticker_data}_model.pth"
                if os.path.exists(model_path):
                    from MarketPrediction.models.lstm import LSTMModel
                    from MarketPrediction.services.feature_service import scale_split
                    
                    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    _, _, X_test, _, scaler = scale_split(df)
                    
                    model = LSTMModel().to(device)
                    model.load_state_dict(torch.load(model_path, map_location=device))
                    model.eval()
                    
                    X_test = torch.tensor(X_test, dtype=torch.float32).to(device)
                    with torch.no_grad():
                        preds = model(X_test).cpu().numpy()
                    
                    preds_inv = scaler.inverse_transform(preds)
                    predictions = preds_inv.flatten().tolist()[-days:] if len(preds_inv) > 0 else [last_price] * days
                    return predictions
        except Exception as e:
            print(f"Model loading failed for {ticker_data}: {str(e)}")
        
        # Fallback: Use simple trend continuation
        return generate_simple_forecast(df, days)
    
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        # Return constant prediction as last resort
        if isinstance(ticker_data, str) or (isinstance(ticker_data, pd.DataFrame) and not ticker_data.empty):
            try:
                if isinstance(ticker_data, str):
                    from MarketPrediction.services.data_service import load_data
                    df = load_data(ticker_data)
                else:
                    df = ticker_data
                
                if df is not None and not df.empty:
                    if 'Close' in df.columns:
                        last_price = float(df['Close'].iloc[-1])
                    elif 'close' in df.columns:
                        last_price = float(df['close'].iloc[-1])
                    else:
                        last_price = float(df.iloc[-1, 0])
                    return [last_price] * days
            except:
                pass
        return [0.0] * days


def generate_simple_forecast(df: pd.DataFrame, days: int) -> List[float]:
    try:
        if df is None or df.empty:
            return [0.0] * days
        
        # Get close prices
        if 'Close' in df.columns:
            prices = df['Close'].values
        elif 'close' in df.columns:
            prices = df['close'].values
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
