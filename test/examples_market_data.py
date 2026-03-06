"""
Example script: Using improved GetMarketData with portfolio optimization
Demonstrates all the new features added to the platform
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Scraper.GetMarketData import (
	get_market_data, 
	get_all_symbols,
	get_bulk_market_data,
	build_vn_market,
	get_market_correlation_matrix
)
from PortfolioOptimizer.Optimizer import optimize_portfolio_mean_variance_fraud
import pandas as pd
import numpy as np

def example_1_single_stock_with_returns():
	"""Example 1: Fetch single stock with return calculations"""
	print("\n" + "="*60)
	print("EXAMPLE 1: Single Stock with Return Calculations")
	print("="*60)
	
	df = get_market_data("VCB", "2023-06-01", "2024-12-31")
	
	if df is not None:
		print(f"\nFetched {len(df)} data points")
		print(f"Columns: {df.columns.tolist()}")
		print(f"\nFirst 5 rows:")
		print(df.head())
		print(f"\nLast row:")
		print(df.tail(1))
		
		# Calculate statistics
		total_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
		avg_return = df['return'].mean() * 100
		volatility = df['return'].std() * 100
		
		print(f"\nStatistics:")
		print(f"  Total Return: {total_return:.2f}%")
		print(f"  Average Daily Return: {avg_return:.2f}%")
		print(f"  Daily Volatility: {volatility:.2f}%")
	else:
		print("Failed to fetch data")

def example_2_multiple_stocks():
	"""Example 2: Fetch multiple stocks efficiently"""
	print("\n" + "="*60)
	print("EXAMPLE 2: Multiple Stocks")
	print("="*60)
	
	tickers = ["VCB", "GAS", "HPG", "VNM", "FPT"]
	market_data = get_bulk_market_data(tickers, "2023-06-01", "2024-12-31")
	
	print(f"\nSuccessfully fetched data for {len(market_data)} stocks:")
	
	for ticker, df in market_data.items():
		if df is not None:
			total_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
			volatility = df['return'].std() * 100
			sharpe = df['return'].mean() / volatility if volatility > 0 else 0
			
			print(f"\n  {ticker}:")
			print(f"    Data Points: {len(df)}")
			print(f"    Total Return: {total_return:.2f}%")
			print(f"    Volatility: {volatility:.2f}%")
			print(f"    Sharpe Ratio: {sharpe:.4f}")

def example_3_correlation_matrix():
	"""Example 3: Calculate correlation matrix for portfolio"""
	print("\n" + "="*60)
	print("EXAMPLE 3: Correlation Matrix for Portfolio")
	print("="*60)
	
	tickers = ["VCB", "GAS", "HPG", "VNM"]
	correlation = get_market_correlation_matrix(tickers, "2023-06-01", "2024-12-31")
	
	if correlation is not None:
		print(f"\nCorrelation Matrix:")
		print(correlation.round(3))
		
		# Find highest and lowest correlations
		print(f"\nInsights:")
		# Set diagonal to NaN to exclude self-correlation
		corr_no_diag = correlation.copy()
		np.fill_diagonal(corr_no_diag.values, np.nan)
		
		max_corr = corr_no_diag.abs().max().max()
		min_corr = corr_no_diag.abs().min().min()
		
		print(f"  Highest Correlation: {max_corr:.3f}")
		print(f"  Lowest Correlation: {min_corr:.3f}")
		print(f"  Average |Correlation|: {corr_no_diag.abs().values.mean():.3f}")
	else:
		print("Failed to calculate correlation matrix")

def example_4_portfolio_optimization():
	"""Example 4: Optimize portfolio with multiple assets"""
	print("\n" + "="*60)
	print("EXAMPLE 4: Portfolio Optimization")
	print("="*60)
	
	tickers = ["VCB", "GAS", "HPG", "VNM"]
	print(f"\nOptimizing portfolio for {len(tickers)} stocks...")
	
	market_data = get_bulk_market_data(tickers, "2023-01-01", "2024-12-31")
	
	if len(market_data) < 2:
		print("Insufficient data for optimization")
		return
	
	# Align returns
	returns_dict = {}
	for ticker, df in market_data.items():
		if 'return' in df.columns:
			returns_dict[ticker] = df['return'].values
	
	valid_tickers = list(returns_dict.keys())
	
	# Calculate alignment length
	min_len = min(len(r) for r in returns_dict.values())
	aligned_returns = {}
	for ticker, returns in returns_dict.items():
		aligned_returns[ticker] = returns[-min_len:]
	
	# Create returns array
	returns_array = np.array([aligned_returns[t] for t in valid_tickers])
	
	# Calculate expected returns and covariance
	expected_returns = np.nanmean(returns_array, axis=1)
	cov_matrix = np.cov(returns_array)
	
	# Simple equal fraud scores
	fraud_scores = np.ones(len(valid_tickers)) * 0.3
	
	# Optimize
	weights = optimize_portfolio_mean_variance_fraud(
		expected_returns=expected_returns,
		cov_matrix=cov_matrix,
		fraud_scores=fraud_scores,
		alpha=0.5,
		beta=0.5
	)
	
	print(f"\nOptimal Portfolio Weights:")
	for ticker, weight in zip(valid_tickers, weights):
		print(f"  {ticker}: {weight*100:.2f}%")
	
	# Calculate portfolio metrics
	portfolio_return = np.dot(weights, expected_returns)
	portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
	portfolio_risk = np.sqrt(portfolio_variance)
	
	print(f"\nPortfolio Metrics:")
	print(f"  Expected Return: {portfolio_return*100:.2f}%")
	print(f"  Risk (Volatility): {portfolio_risk*100:.2f}%")
	print(f"  Sharpe Ratio: {portfolio_return/portfolio_risk:.4f}")

def example_5_import_csv_to_db():
	"""Example 5: Import vn_full_market.csv into MongoDB"""
	print("\n" + "="*60)
	print("EXAMPLE 5: Import CSV to Database (Optional)")
	print("="*60)
	
	import os
	csv_file = "vn_full_market.csv"
	
	if not os.path.exists(csv_file):
		print(f"\n{csv_file} not found")
		print("Run build_vn_market() first to create the CSV")
		print("\nExample:")
		print("  from Scraper.GetMarketData import build_vn_market")
		print("  df = build_vn_market()")
		print("  print(f'Built market with {len(df)} records')")
		return
	
	print(f"\nLoading {csv_file}...")
	df = pd.read_csv(csv_file)
	print(f"Loaded {len(df)} records with columns: {df.columns.tolist()}")
	
	try:
		from Database.MongoDBManager import get_db_manager
		from datetime import datetime
		
		db_manager = get_db_manager()
		
		# Add metadata
		df['source'] = 'historical_snapshot'
		df['import_date'] = datetime.now()
		
		# Convert to records
		records = df.to_dict('records')
		
		# Insert into MongoDB
		result = db_manager.db['vn_market_history'].insert_many(records)
		
		print(f"\n✓ Successfully imported {len(result.inserted_ids)} records to MongoDB")
		print(f"  Collection: 'vn_market_history'")
		print(f"  Columns: {df.columns.tolist()}")
		
		# Create index for faster queries
		db_manager.db['vn_market_history'].create_index([('symbol', 1), ('date', 1)])
		print(f"  Index created on (symbol, date)")
		
	except Exception as e:
		print(f"\n✗ Error importing to database: {str(e)}")
		print("Make sure MongoDB is running and database is configured")

def main():
	"""Run all examples"""
	print("\n")
	print("╔" + "="*58 + "╗")
	print("║" + " "*15 + "GetMarketData Examples" + " "*23 + "║")
	print("╚" + "="*58 + "╝")
	
	try:
		example_1_single_stock_with_returns()
	except Exception as e:
		print(f"ERROR in Example 1: {str(e)}")
	
	try:
		example_2_multiple_stocks()
	except Exception as e:
		print(f"ERROR in Example 2: {str(e)}")
	
	try:
		example_3_correlation_matrix()
	except Exception as e:
		print(f"ERROR in Example 3: {str(e)}")
	
	try:
		example_4_portfolio_optimization()
	except Exception as e:
		print(f"ERROR in Example 4: {str(e)}")
	
	try:
		example_5_import_csv_to_db()
	except Exception as e:
		print(f"ERROR in Example 5: {str(e)}")
	
	print("\n" + "="*60)
	print("Examples Complete!")
	print("="*60 + "\n")

if __name__ == "__main__":
	main()
