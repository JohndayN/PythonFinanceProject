from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd

def compute_hose_market_anomaly(df_features):
    try:
        if df_features is None or df_features.empty:
            return pd.DataFrame()
        
        df = df_features.copy()
        
        # Standardize column names
        df.columns = [col.lower() for col in df.columns]
        
        # Check for required columns
        if 'price_change_pct' not in df.columns:
            df['price_change_pct'] = 0
        if 'log_volume' not in df.columns:
            df['log_volume'] = 0
        
        # Convert to float and fill NaN
        df['price_change_pct'] = pd.to_numeric(df['price_change_pct'], errors='coerce').fillna(0)
        df['log_volume'] = pd.to_numeric(df['log_volume'], errors='coerce').fillna(0)
        
        # Prepare feature matrix
        X = df[["price_change_pct", "log_volume"]].values
        
        # Check for valid data
        if X.shape[0] < 2:
            df['hose_market_anomaly_score'] = 0
            return df
        
        try:
            model = IsolationForest(
                n_estimators=100,
                contamination=min(0.05, 1.0 / max(X.shape[0], 2)),  # Avoid invalid contamination
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X)
            scores = -model.score_samples(X)
            df['hose_market_anomaly_score'] = scores
        
        except Exception as e:
            print(f"IsolationForest error: {str(e)}")
            df['hose_market_anomaly_score'] = 0
        
        # Return with symbol if available
        if 'securitysymbol' in df.columns:
            return df[['securitysymbol', 'hose_market_anomaly_score']]
        elif 'symbol' in df.columns:
            return df[['symbol', 'hose_market_anomaly_score']]
        else:
            return df[['hose_market_anomaly_score']]
    
    except Exception as e:
        print(f"Error in compute_hose_market_anomaly: {str(e)}")
        return pd.DataFrame()