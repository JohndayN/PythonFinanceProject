from vnstock import Vnstock, Listing
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time
import sys
import config
from pymongo import MongoClient

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# -----------------------------
# MongoDB setup
# -----------------------------

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]

collection = db["mixed_ticker_data"]

indexes = collection.index_information()

if "symbol_1" not in indexes:
    collection.create_index([("symbol", 1)], unique=True)


# -----------------------------
# Utility functions
# -----------------------------

def normalize_columns(df):
    df.columns = [c.lower() for c in df.columns]
    return df


def normalize_date(date_str):

    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except:
            pass

    return date_str


# -----------------------------
# Listing data
# -----------------------------

def get_listing_data(source="VCI"):

    try:

        listing = Listing()

        df = listing.all_symbols(source=source)

        df = normalize_columns(df)

        return df[["symbol", "organ_name"]]

    except Exception as e:

        print(f"Error fetching listing data: {str(e)}")

        return pd.DataFrame()


def build_symbol_lookup(source="VCI"):

    listing_df = get_listing_data(source)

    lookup = {}

    for _, row in listing_df.iterrows():

        lookup[row["symbol"]] = row["organ_name"]

    return lookup


def get_all_symbols(source="VCI") -> List[str]:

    try:

        listing = Listing()

        df = listing.all_symbols(source=source)

        return df["symbol"].tolist()

    except Exception as e:

        print(f"Error fetching all symbols: {str(e)}")

        return []


# -----------------------------
# Market data
# -----------------------------

def get_market_data(ticker, start_date=None, end_date=None, source=None):

    ticker = ticker.upper().strip()

    if start_date is None:
        start_date = config.start_date

    if end_date is None:
        end_date = config.end_date

    if source is None:
        source = config.source

    source = source.upper()

    start_date = normalize_date(start_date)
    end_date = normalize_date(end_date)

    # ---- VNSTOCK ----

    try:

        print(f"Fetching {ticker} from VNStock ({source})")

        stock = Vnstock().stock(symbol=ticker, source=source)

        df = stock.quote.history(
            start=start_date,
            end=end_date,
            interval="1d"
        )

        if df is None or df.empty:
            print(f"No data returned for {ticker}")
            return None

        df = normalize_columns(df)

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])

        df = df.sort_values("time")

        df["symbol"] = ticker

        if "close" in df.columns:

            df["return"] = df["close"].pct_change()

            df["log_return"] = np.log(df["close"] / df["close"].shift(1))

        return df

    except Exception as e:

        print(f"VNStock failed {ticker} ({source}): {e}")

    # ---- Yahoo fallback ----

    try:

        yf_ticker = ticker + ".VN"

        print(f"Fallback to Yahoo Finance: {yf_ticker}")

        df = yf.download(
            yf_ticker,
            start=start_date,
            end=end_date,
            progress=False
        )

        if df is not None and not df.empty:

            df = normalize_columns(df)

            df["time"] = df.index

            df["symbol"] = ticker

            df["return"] = df["close"].pct_change()

            df["log_return"] = np.log(df["close"] / df["close"].shift(1))

            df = df.reset_index(drop=True)

            return df

    except Exception as e:

        print(f"Yahoo failed {ticker}: {e}")

    return None


# -----------------------------
# Mongo helpers
# -----------------------------

def build_price_list(df):

    prices = df.apply(
        lambda r: {
            "date": r["time"],
            "open": r.get("open"),
            "high": r.get("high"),
            "low": r.get("low"),
            "close": r.get("close"),
            "volume": r.get("volume"),
            "return": r.get("return"),
            "log_return": r.get("log_return")
        },
        axis=1
    ).tolist()

    return prices


def save_to_mongo(symbol, company_name, prices, source):

    doc = {
        "symbol": symbol,
        "company_name": company_name,
        "source": source,
        "updated_at": datetime.utcnow(),
        "prices": prices
    }

    collection.update_one(
        {"symbol": symbol},
        {"$set": doc},
        upsert=True
    )


# -----------------------------
# Build full VN market
# -----------------------------

def build_vn_market(start_date=None,
                    end_date=None,
                    source="VCI"):

    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    symbols = get_all_symbols(source)

    symbol_lookup = build_symbol_lookup(source)

    print(f"Building Vietnamese market data for {len(symbols)} stocks...")

    for i, symbol in enumerate(symbols):

        print(f"[{i+1}/{len(symbols)}] Processing {symbol}")

        df = get_market_data(symbol, start_date, end_date, source)

        if df is None:
            continue

        prices = build_price_list(df)

        company_name = symbol_lookup.get(symbol)

        save_to_mongo(symbol, company_name, prices, source)

        time.sleep(3)


# -----------------------------
# Correlation matrix
# -----------------------------

def get_market_correlation_matrix(tickers: List[str],
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None):

    results = {}

    for ticker in tickers:

        df = get_market_data(ticker, start_date, end_date)

        if df is not None:

            results[ticker] = df["return"]

    if len(results) < 2:

        print("Insufficient tickers")

        return None

    returns_df = pd.DataFrame(results)

    return returns_df.corr()


# -----------------------------
# Main test
# -----------------------------

if __name__ == "__main__":

    df = get_market_data("VCB", "2023-01-01", "2024-12-31")

    if df is not None:

        prices = build_price_list(df)
        
        print(prices)

        save_to_mongo(
            "VCB",
            "Ngân hàng TMCP Ngoại thương Việt Nam",
            prices,
            "VCI"
        )

        print("Saved test ticker")

    else:

        print("Failed to fetch data")