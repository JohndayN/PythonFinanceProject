from vnstock import Vnstock, Listing
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time

def get_all_symbols() -> List[str]:
    try:
        listing = Listing()
        df = listing.all_symbols()
        return df["symbol"].tolist()
    except Exception as e:
        print(f"Error fetching all symbols: {str(e)}")
        return []

def get_market_data(ticker: str, 
                    start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    try:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Normalize ticker
        ticker = ticker.upper().strip()
        
        # Try Vietnamese stock first (VNX)
        vietnam_stocks = ['VCB', 'VIC', 'VNM', 'HPG', 'FPT', 'MWG', 'TCB', 'BID', 'GAS', 'MSN', 'IMP']
        if ticker in vietnam_stocks:
            try:
                stock = Vnstock().stock(symbol=ticker, source="VCI")
                df = stock.quote.history(start=start_date, end=end_date, interval="1D")
                
                if df is not None and not df.empty:
                    # Standardize column names (case-insensitive)
                    df.columns = [col.lower() for col in df.columns]
                    
                    # Ensure we have close price
                    if 'close' not in df.columns:
                        for col in df.columns:
                            if 'close' in col.lower():
                                df['close'] = df[col]
                                break
                    
                    # Ensure we have volume
                    if 'volume' not in df.columns:
                        for col in df.columns:
                            if 'volume' in col.lower():
                                df['volume'] = df[col]
                                break
                    
                    # Reset index to make date proper DatetimeIndex
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)
                    
                    # Create result DataFrame with only needed columns
                    result_df = pd.DataFrame()
                    result_df.index = df.index
                    
                    if 'close' in df.columns:
                        result_df['Close'] = pd.to_numeric(df['close'], errors='coerce')
                    else:
                        result_df['Close'] = pd.to_numeric(df.iloc[:, 0], errors='coerce')
                    
                    if 'volume' in df.columns:
                        result_df['Volume'] = pd.to_numeric(df['volume'], errors='coerce')
                    else:
                        result_df['Volume'] = 0
                    
                    # Add symbol
                    result_df['symbol'] = ticker
                    
                    # Calculate returns
                    result_df['return'] = result_df['Close'].pct_change()
                    result_df['log_return'] = np.log(result_df['Close'] / result_df['Close'].shift(1))
                    
                    # Remove NaN rows
                    result_df = result_df.dropna()
                    
                    if not result_df.empty:
                        return result_df
            except Exception as e:
                print(f"Skipping {ticker} — {str(e)}")
        
        # Fallback to yfinance for international stocks or if VNX failed
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df is not None and not df.empty:
                if isinstance(df, pd.DataFrame):
                    result = pd.DataFrame()
                    result.index = df.index
                    result['Close'] = df['Close']
                    result['Volume'] = df['Volume']
                    result['symbol'] = ticker
                    
                    # Calculate returns
                    result['return'] = result['Close'].pct_change()
                    result['log_return'] = np.log(result['Close'] / result['Close'].shift(1))
                    
                    result = result.dropna()
                    return result if not result.empty else None
                else:
                    return None
        except Exception as e:
            print(f"Skipping {ticker} — {str(e)}")
        
        return None
        
    except Exception as e:
        print(f"Skipping {ticker} — {str(e)}")
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
