"""
Test script for Market Scraper fixes
Run this to verify all endpoints work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Scraper.GetMarketData import get_market_data
from Scraper.HOSE.GetHOSEMarketData import get_hose_market_data

def test_single_stock():
	"""Test single stock data fetching"""
	print("=" * 60)
	print("TEST 1: Single Stock Data Fetching")
	print("=" * 60)
	
	tickers = ['VCB', 'GAS', 'HPG']
	
	for ticker in tickers:
		print(f"\nFetching {ticker}...")
		df = get_market_data(ticker, '2023-01-01', '2024-12-31')
		
		if df is None or df.empty:
			print(f"  ❌ FAILED: No data returned")
		else:
			print(f"  ✓ SUCCESS: Got {len(df)} data points")
			print(f"    Columns: {df.columns.tolist()}")
			print(f"    Date range: {df.index[0]} to {df.index[-1]}")
			print(f"    Latest close: {df['Close'].iloc[-1]:.2f}")

def test_hose_market():
	"""Test HOSE market data fetching"""
	print("\n" + "=" * 60)
	print("TEST 2: HOSE Market Data Fetching")
	print("=" * 60)
	
	print("\nFetching HOSE market data...")
	df = get_hose_market_data()
	
	if df is None or df.empty:
		print("  ❌ FAILED: No data returned")
	else:
		print(f"  ✓ SUCCESS: Got {len(df)} stocks")
		print(f"    Columns: {df.columns.tolist()}")
		
		# Check for null columns
		null_cols = df.columns[df.isnull().all()].tolist()
		if null_cols:
			print(f"    ⚠ WARNING: All-null columns: {null_cols}")
		else:
			print(f"    ✓ No all-null columns")
		
		print(f"\n    Sample data:")
		print(df.head(3).to_string())

def test_api_endpoints():
	"""Test API endpoints"""
	print("\n" + "=" * 60)
	print("TEST 3: API Endpoints")
	print("=" * 60)
	
	try:
		import requests
		
		# Test health endpoint
		print("\nTesting /api/health endpoint...")
		response = requests.get('http://localhost:8000/api/health', timeout=5)
		if response.status_code == 200:
			print(f"  ✓ SUCCESS: {response.json()}")
		else:
			print(f"  ❌ FAILED: Status {response.status_code}")
		
		# Test market data endpoint
		print("\nTesting /api/scraper/market-data endpoint...")
		payload = {
			"ticker": "VCB",
			"start_date": "2023-01-01",
			"end_date": "2024-12-31"
		}
		response = requests.post('http://localhost:8000/api/scraper/market-data', 
								json=payload, timeout=10)
		if response.status_code == 200:
			data = response.json()
			print(f"  ✓ SUCCESS: Got {len(data.get('data', {}).get('dates', []))} data points")
		else:
			print(f"  ❌ FAILED: Status {response.status_code}")
			print(f"    Message: {response.text}")
		
		# Test HOSE endpoint
		print("\nTesting /api/scraper/hose-market endpoint...")
		response = requests.get('http://localhost:8000/api/scraper/hose-market', timeout=10)
		if response.status_code == 200:
			data = response.json()
			print(f"  ✓ SUCCESS: Got {len(data.get('data', []))} stocks")
		else:
			print(f"  ❌ FAILED: Status {response.status_code}")
			print(f"    Message: {response.text}")
	
	except requests.exceptions.ConnectionError:
		print("  ⚠ WARNING: Cannot connect to API. Make sure it's running on port 8000")
	except Exception as e:
		print(f"  ❌ ERROR: {str(e)}")

if __name__ == "__main__":
	print("\n")
	print("╔" + "=" * 58 + "╗")
	print("║" + " " * 15 + "Market Scraper Test Suite" + " " * 19 + "║")
	print("╚" + "=" * 58 + "╝")
	
	test_single_stock()
	test_hose_market()
	test_api_endpoints()
	
	print("\n" + "=" * 60)
	print("Test Complete!")
	print("=" * 60 + "\n")
