from vnstock import Vnstock, Listing
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time
import sys
import config
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def normalize_columns(df):
    df.columns = [c.lower() for c in df.columns]

    return df

def normalize_date(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    except:
        return date_str

def get_all_symbols() -> List[str]:
    try:
        listing = Listing()
        df = listing.all_symbols()
        return df["symbol"].tolist()
    except Exception as e:
        print(f"Error fetching all symbols: {str(e)}")
        return []

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

    # ---- Try VNSTOCK first ----
    try:

        print(f"Fetching {ticker} from VNStock ({source})")

        stock = Vnstock().stock(symbol=ticker, source=source)

        df = stock.quote.history(
            start=start_date,
            end=end_date,
            interval="1d"
        )

        if df is None or df.empty:
            print(f"No data returned for {ticker} with VNStock {source}")
            return None

        df = normalize_columns(df)

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df = df.set_index("time")

        df = df.sort_index()

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

            result = pd.DataFrame()
            result.index = df.index

            result["close"] = df["close"]
            result["volume"] = df["volume"]
            result["symbol"] = ticker

            result["return"] = result["close"].pct_change()
            result["log_return"] = np.log(result["close"] / result["close"].shift(1))

            result = result.dropna(subset=["return"])

            return result

        print(f"No data returned for {ticker} with YahooFinance")

    except Exception as e:
        print(f"Yahoo failed {ticker}: {e}")

    return None

def get_bulk_market_data(tickers: List[str], 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    results = {}
    for ticker in tickers:
        print(f"Fetching {ticker}...")
        df = get_market_data(ticker, start_date, end_date)
        if df is not None:
            results[ticker] = df
    return results

def build_vn_market(start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    symbols = get_all_symbols()
    all_data = []
    
    print(f"Building Vietnamese market data for {len(symbols)} stocks...")
    
    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] Processing {symbol}")
        
        df = get_market_data(symbol, start_date, end_date)
        
        if df is not None:
            all_data.append(df)
        
        # Rate limiting to avoid API overload
        time.sleep(3)
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        return result
    return None

def get_market_correlation_matrix(tickers: List[str],
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    market_data = get_bulk_market_data(tickers, start_date, end_date)
    
    if not market_data or len(market_data) < 2:
        print("Insufficient valid tickers for correlation matrix")
        return None
    
    # Extract returns for each ticker
    returns_dict = {}
    for ticker, df in market_data.items():
        if 'return' in df.columns:
            returns_dict[ticker] = df['return']
    
    if not returns_dict:
        return None
    
    # Create DataFrame with all returns
    returns_df = pd.DataFrame(returns_dict)
    
    # Calculate correlation
    correlation = returns_df.corr()
    
    return correlation

#Not used yet, but could be useful for future analysis
def build_returns_matrix(data):

    pivot = data.pivot_table(
        index=data.index,
        columns="symbol",
        values="return"
    )

    return pivot

# Legacy function name for compatibility
def fetch_market_data(*args, **kwargs):
    """Alias for get_market_data"""
    return get_market_data(*args, **kwargs)

if __name__ == "__main__":
    # Test
    df = get_market_data("VCB", "2023-01-01", "2024-12-31")
    if df is not None:
        print(f"Successfully fetched data shape: {df.shape}")
        print(df.head())
    else:
        print("Failed to fetch data")
