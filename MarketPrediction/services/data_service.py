import os
import yfinance as yf
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_PATH = os.path.join(BASE_DIR, "data", "raw")

def load_data(tickers, start=None, end=None, refresh=False):

    os.makedirs(DATA_PATH, exist_ok=True)

    single_ticker = isinstance(tickers, str)

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

                # Flatten yfinance multi-index columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                if "Close" in df.columns:
                    df = df[["Close"]].dropna()

                df = df.sort_index()

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                df.to_csv(file_path)

            if df is not None and not df.empty:

                df = df.sort_index()

                # IMPORTANT for prediction service
                df.attrs["ticker"] = ticker

                data_dict[ticker] = df

        except Exception as e:

            print(f"Error loading data for {ticker}: {str(e)}")
            continue

    if single_ticker:
        return data_dict.get(tickers[0], pd.DataFrame())

    return data_dict if data_dict else None