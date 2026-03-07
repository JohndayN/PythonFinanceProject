import requests
import pandas as pd
import numpy as np

def fetch_board(url):
    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "referer": "https://rtboard.hsx.vn/",
            "user-agent": "Mozilla/5.0"
            }   
        
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json().get("data", [])

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        df = df.rename(columns={
            "securitySymbol": "symbol",
            "name": "company",
            "accumulatedPrice": "price",
			"changePrice": "change",
			"changePriceRatio": "pct_change",
			"accumulatedVol": "volume",
			"openPrice": "open",
			"highest": "high",
			"lowest": "low",
        })

        df = df[["symbol","company","price","change","pct_change","volume","open","high","low"]]

        numeric_cols = ["price","change","pct_change","volume","open","high","low"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # fallback change calculation
        if df["change"].sum() == 0 and df["pct_change"].sum() == 0:
            df["change"] = np.where(
                df["open"] > 0,
                ((df["price"] - df["open"]) / df["open"] * 100),
                0
            ).round(2)

        return df

    except Exception as e:
        print(f"Error fetching HOSE data: {str(e)}")
        return pd.DataFrame()