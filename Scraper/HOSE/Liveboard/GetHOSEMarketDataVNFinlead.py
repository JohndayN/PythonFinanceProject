import requests
import pandas as pd
import numpy as np

"""
            "securitySymbol": "ACB",
            "securityName": null,
            "priorClosePrice": "23550",
            "ceiling": "25150",
            "floor": "21950",
            "best3Bid": "23200",
            "best3BidVolume": "360800",
            "best2Bid": "23250",
            "best2BidVolume": "182100",
            "best1Bid": "23300",
            "best1BidVolume": "89400",
            "accumulatedPrice": "23300",
            "accumulatedVol": "200000",
            "changePrice": "-250",
            "changePriceRatio": "-1.061571",
            "best1Offer": "23350",
            "best1OfferVolume": "54500",
            "best2Offer": "23400",
            "best2OfferVolume": "202400",
            "best3Offer": "23450",
            "best3OfferVolume": "31200",
            "openPrice": "23500",
            "highest": "23600",
            "lowest": "23200",
            "totalShare": "11699100",
            "totalValue": "273531125000",
            "foreignRoomBuy": "914800",
            "foreignRoomSell": "1457300",
            "currentRoom": "147946735",
            "totalRoom": "1540996979",
            "iNav": "",
            "iIndex": "",
            "warning_status": "",
            "id": 2784,
            "name": "Ngân hàng Thương mại Cổ phần Á Châu",
            "code": "ACB"
        """


def get_hose_market_liveboard(board_id = 3):
	url = "https://api.hsx.vn/l/api/v1/securities/load-securities-hoseindex-forboard/3"

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
