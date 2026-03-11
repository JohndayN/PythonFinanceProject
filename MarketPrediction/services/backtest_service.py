import numpy as np
import torch
from MarketPrediction.services.predict_service import predict
from Database.MongoDBManager import get_db_manager
import config

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def backtest(ticker):
    model, scaler = predict(ticker)
    db = get_db_manager()
    df = db.get_stock_df(ticker)
    prices = df["Close"].values

    scaled = scaler.transform(df.values)

    profits = []

    for i in range(config.SEQ_LENGTH, len(prices)-1):
        seq = scaled[i-config.SEQ_LENGTH:i]
        X = torch.tensor(seq, dtype=torch.float32).unsqueeze(0).to(device)

        with torch.no_grad():
            pred = model(X).cpu().numpy()

        pred_price = scaler.inverse_transform(pred)[0][0]
        today_price = prices[i]
        next_price = prices[i+1]

        if pred_price > today_price:
            profits.append(next_price - today_price)
        else:
            profits.append(0)

    total_profit = np.sum(profits)
    return {
        "ticker": ticker,
        "total_profit": float(total_profit),
        "trades": len([p for p in profits if p != 0])
    }
