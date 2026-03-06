import os
import yfinance as yf
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_PATH = os.path.join(BASE_DIR, "data", "raw")

def load_data(tickers, start=None, end=None, refresh=False):
    """
    Load market data from CSV or yfinance.
    
    Args:
        tickers: Single ticker string or list of tickers
        start: Start date
        end: End date
        refresh: Force download from yfinance
        
    Returns:
        Single DataFrame if single ticker (string input), 
        Dict of DataFrames if multiple tickers (list input)
    """
    os.makedirs(DATA_PATH, exist_ok=True)

    # Track if single ticker
    single_ticker = isinstance(tickers, str)
    
    # Convert single ticker to list
    if single_ticker:
        tickers = [tickers]

    data_dict = {}

    for ticker in tickers:
        try:
            file_path = os.path.join(DATA_PATH, f"{ticker}.csv")

            if os.path.exists(file_path) and not refresh:
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            else:
                print(f"Downloading data for {ticker}...")
                df = yf.download(ticker, start=start, end=end, progress=False)

                if df is None or df.empty:
                    print(f"No data for {ticker}")
                    continue

                # Ensure we have Close column
                if isinstance(df, pd.DataFrame):
                    if 'Close' in df.columns:
                        df = df[["Close"]].dropna()
                    else:
                        # In case only single column returned
                        df = pd.DataFrame(df)
                
                # Create data directory if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                df.to_csv(file_path)

            if df is not None and not df.empty:
                data_dict[ticker] = df
        
        except Exception as e:
            print(f"Error loading data for {ticker}: {str(e)}")
            continue

    # Return single DataFrame if single ticker was requested
    if single_ticker:
        if tickers[0] in data_dict:
            return data_dict[tickers[0]]
        else:
            return pd.DataFrame()
    
    return data_dict if data_dict else None
