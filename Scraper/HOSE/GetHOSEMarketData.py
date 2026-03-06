import requests
import pandas as pd
import numpy as np

def get_hose_market_data():
	"""
	Fetch HOSE market data and filter to essential columns
	Includes real-time price percentage changes
	"""
	url = "https://api.hsx.vn/l/api/v1/securities/load-securities-matching/1"

	headers = {
		"accept": "application/json, text/plain, */*",
		"referer": "https://rtboard.hsx.vn/",
		"user-agent": "Mozilla/5.0"
	}

	try:
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
			"lowest": "low"
			})
		
		df = df[["symbol","company","price","change","pct_change","volume","open","high","low"]]
		
		# Clean data - convert to proper types
		if 'price' in df.columns:
			df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
		if 'change' in df.columns:
			df['change'] = pd.to_numeric(df['change'], errors='coerce').fillna(0)
		if 'pct_change' in df.columns:
			df['pct_change'] = pd.to_numeric(df['pct_change'], errors='coerce').fillna(0)
		if 'volume' in df.columns:
			df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
		
		# If all change/percentChange fields are 0, try to fetch from alternative source
		if (df.get('change', pd.Series()).sum() == 0 and df.get('pct_change', pd.Series()).sum() == 0):
			# Try to get change data from price open/close
			if 'open' in df.columns and 'price' in df.columns:
				df['open'] = pd.to_numeric(df['open'], errors='coerce')
				# Calculate percentage change from previous close (open is today's open)
				df['change'] = np.where(
					df['open'] > 0,
					((df['price'] - df['open']) / df['open'] * 100),
					0
				).round(2)
		
		# Ensure change column exists
		if 'change' not in df.columns:
			df['change'] = 0
		
		return df

	except Exception as e:
		print(f"Error fetching HOSE data: {str(e)}")
		return pd.DataFrame()
