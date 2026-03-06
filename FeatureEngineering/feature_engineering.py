import pandas as pd
import numpy as np

def create_market_features(df):
    try:
        # Handle empty dataframe
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Standardize column names
        df.columns = [col.lower() for col in df.columns]
        
        # Get close price (required)
        if 'close' not in df.columns:
            return pd.DataFrame()
        
        # Calculate return
        df['return'] = df['close'].pct_change()
        
        # Calculate volatility (rolling standard deviation of returns)
        df['volatility'] = df['return'].rolling(window=20).std()
        
        # Financial features (optional - handle missing columns)
        if 'revenue' in df.columns:
            df['revenue_growth'] = df['revenue'].pct_change()
        else:
            df['revenue_growth'] = 0
        
        if 'revenue' in df.columns and 'net_profit' in df.columns:
            df['profit_margin'] = df['net_profit'] / df['revenue'].replace(0, np.nan)
        else:
            df['profit_margin'] = 0
        
        if 'total_debt' in df.columns and 'total_assets' in df.columns:
            df['debt_ratio'] = df['total_debt'] / df['total_assets'].replace(0, np.nan)
        else:
            df['debt_ratio'] = 0
        
        # Replace infinite values with NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN values with 0 or forward fill
        df = df.fillna(0)
        
        # Keep only numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        return df[numeric_cols]
    
    except Exception as e:
        print(f"Error creating market features: {str(e)}")
        return pd.DataFrame()