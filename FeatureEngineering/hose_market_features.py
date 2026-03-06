import numpy as np
import pandas as pd

def create_hose_market_features(df):
    try:
        if df is None or df.empty:
            return pd.DataFrame()
        
        df = df.copy()
        
        # Standardize column names to lowercase
        df.columns = [col.lower() for col in df.columns]
        
        # Handle price column variations
        if 'accumulatedprice' in df.columns:
            price_col = 'accumulatedprice'
        elif 'price' in df.columns:
            price_col = 'price'
        else:
            return pd.DataFrame()
        
        # Handle prior close price
        if 'priorcloseprice' in df.columns:
            prior_col = 'priorcloseprice'
        elif 'open' in df.columns:
            prior_col = 'open'
        else:
            prior_col = None
        
        # Handle volume/share column
        if 'totalshare' in df.columns:
            vol_col = 'totalshare'
        elif 'volume' in df.columns:
            vol_col = 'volume'
        else:
            vol_col = None
        
        # Convert to float
        df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
        if prior_col:
            df[prior_col] = pd.to_numeric(df[prior_col], errors='coerce')
        if vol_col:
            df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce')
        
        # Price change %
        if prior_col and prior_col in df.columns:
            df['price_change_pct'] = (
                (df[price_col] - df[prior_col]) / df[prior_col].replace(0, np.nan)
            ).fillna(0)
        else:
            df['price_change_pct'] = 0
        
        # Liquidity log scale
        if vol_col and vol_col in df.columns:
            df['log_volume'] = np.log1p(df[vol_col].fillna(0))
        else:
            df['log_volume'] = 0
        
        # Get symbol column if it exists
        if 'securitysymbol' in df.columns:
            symbol_col = 'securitysymbol'
        elif 'symbol' in df.columns:
            symbol_col = 'symbol'
        else:
            symbol_col = None
        
        # Build result dataframe
        result_cols = []
        if symbol_col and symbol_col in df.columns:
            result_cols.append(symbol_col)
        
        result_cols.extend(['price_change_pct', 'log_volume'])
        
        # Return only existing columns
        available_cols = [col for col in result_cols if col in df.columns]
        return df[available_cols] if available_cols else df[['price_change_pct', 'log_volume']]
    
    except Exception as e:
        print(f"Error creating HOSE market features: {str(e)}")
        return pd.DataFrame()