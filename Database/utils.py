import pandas as pd

def df_to_mongo_docs(df, ticker=None):

    df = df.copy()

    if "symbol" not in df.columns and ticker:
        df["symbol"] = ticker

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    elif "date" in df.columns:
        df["time"] = pd.to_datetime(df["date"])
    else:
        df["time"] = df.index

    grouped = df.groupby("symbol")

    docs = []

    for symbol, g in grouped:

        prices = g.sort_values("time").apply(
            lambda r: {
                "date": r["time"],
                "open": float(r.get("open", 0)),
                "high": float(r.get("high", 0)),
                "low": float(r.get("low", 0)),
                "close": float(r.get("close", 0)),
                "volume": float(r.get("volume", 0)),
                "return": float(r.get("return", 0)),
                "log_return": float(r.get("log_return", 0))
            },
            axis=1
        ).tolist()

        docs.append({
            "symbol": symbol,
            "daily_data": prices
        })

    return docs
