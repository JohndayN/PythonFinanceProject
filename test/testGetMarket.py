from vnstock import Listing, Vnstock
import numpy as np
import time
import pandas as pd
from datetime import datetime, timedelta

def get_all_symbols():
    listing = Listing()
    df = listing.all_symbols()
    return df["symbol"].tolist()

def fetch_valid_stock(symbol, start, end):
    try:
        stock = Vnstock().stock(symbol=symbol)

        df = stock.quote.history(
            start=start,
            end=end,
            interval="1D"
        )

        # If no data returned
        if df is None or df.empty:
            print(f"Skipping {symbol} — empty data")
            return None

        df["symbol"] = symbol
        df["return"] = df["close"].pct_change()
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))

        return df

    except Exception as e:
        print(f"Skipping {symbol} — {e}")
        return None

def build_vn_market(start, end):
    symbols = get_all_symbols()
    all_data = []

    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] Processing {symbol}")

        df = fetch_valid_stock(symbol, start, end)

        if df is not None:
            all_data.append(df)

        time.sleep(3)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

start_date = "2020-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")
market_df = build_vn_market(start_date, end_date)

if market_df is not None:
    market_df.to_csv("vn_full_market.csv", index=False)