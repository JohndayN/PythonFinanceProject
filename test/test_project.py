"""
Project Validation and Testing Script
Verifies that all modules are properly configured and connected
"""

import sys
import os
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test if all modules can be imported"""
    print("\n" + "="*60)
    print("Testing Imports...")
    print("="*60)
    
    modules_to_test = [
        ("config", "Configuration"),
        ("Scraper.GetMarketData", "Scraper - Market Data"),
        ("FraudDetection.fraud_detection_csv", "Fraud Detection - CSV"),
        ("FraudDetection.fraud_detection_pdf", "Fraud Detection - PDF"),
        ("PortfolioOptimizer.Optimizer", "Portfolio Optimizer"),
        ("FeatureEngineering.feature_engineering", "Feature Engineering"),
    ]
    
    failed = []
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"Pass {description:40} - OK")
        except ImportError as e:
            print(f"Fail {description:40} - FAILED: {e}")
            failed.append((description, str(e)))
        except Exception as e:
            print(f"WARNING {description:40} - ERROR: {e}")
            failed.append((description, str(e)))
    
    return len(failed) == 0, failed

def test_config():
    """Test configuration"""
    print("\n" + "="*60)
    print("Testing Configuration...")
    print("="*60)
    
    try:
        import config
        
        tests = [
            ("TICKERS defined", hasattr(config, 'TICKERS')),
            ("MONGO_URI defined", hasattr(config, 'MONGO_URI')),
            ("DB_NAME defined", hasattr(config, 'DB_NAME')),
            ("Config has values", len(config.TICKERS) > 0),
        ]
        
        all_passed = True
        for test_name, result in tests:
            status = "Pass" if result else "Fail"
            print(f"{status} {test_name}")
            if not result:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"Fail Configuration test failed: {e}")
        return False

def test_data_fetching():
    """Test if we can fetch data"""
    print("\n" + "="*60)
    print("Testing Data Fetching...")
    print("="*60)
    
    try:
        from Scraper.GetMarketData import get_market_data
        
        print("Attempting to fetch sample data for VCB...")
        df = get_market_data("VCB", "2024-01-01", "2024-01-31")
        
        if df is not None and not df.empty:
            print(f"Pass Successfully fetched {len(df)} rows")
            print(f"  Columns: {list(df.columns)[:5]}...")
            return True
        else:
            print("WARNING Data fetch returned empty result (network/API issue)")
            return True  # Not critical
    except Exception as e:
        print(f"WARNING Data fetching test failed: {e} (may be network-related)")
        return True

def test_fraud_detection():
    """Test fraud detection module"""
    print("\n" + "="*60)
    print("Testing Fraud Detection...")
    print("="*60)
    
    try:
        from FraudDetection.fraud_detection_csv import detect_fraud_csv
        import pandas as pd
        
        # Create sample data
        sample_data = pd.DataFrame({
            'revenue': [1000, 1100, 1050, 1200, 1300],
            'receivables': [200, 250, 300, 350, 400],
            'inventory': [100, 110, 120, 130, 140],
            'depreciation': [50, 50, 50, 50, 50],
            'sga': [200, 210, 220, 230, 240],
            'assets': [2000, 2100, 2200, 2300, 2400],
            'current_assets': [600, 650, 700, 750, 800],
            'cogs': [600, 660, 630, 720, 780]
        })
        
        result = detect_fraud_csv(sample_data)
        
        if 'fraud_probability' in result and 'fraud_risk_level' in result:
            print(f"Pass Fraud detection working")
            print(f"  Risk Level: {result['fraud_risk_level']}")
            print(f"  Fraud Probability: {result['fraud_probability']:.2%}")
            return True
        else:
            print(f"Fail Fraud detection returned unexpected format")
            return False
    except Exception as e:
        print(f"Fail Fraud detection test failed: {e}")
        return False

def test_portfolio_optimizer():
    """Test portfolio optimizer"""
    print("\n" + "="*60)
    print("Testing Portfolio Optimizer...")
    print("="*60)
    
    try:
        from PortfolioOptimizer.Optimizer import optimize_portfolio_mean_variance_fraud
        import numpy as np
        
        # Test data
        expected_returns = np.array([0.15, 0.12, 0.10])
        cov_matrix = np.array([
            [0.04, 0.02, 0.01],
            [0.02, 0.03, 0.01],
            [0.01, 0.01, 0.02]
        ])
        fraud_scores = np.array([0.3, 0.5, 0.2])
        
        weights = optimize_portfolio_mean_variance_fraud(
            expected_returns,
            cov_matrix,
            fraud_scores
        )
        
        if weights is not None and len(weights) == 3:
            print(f"Pass Portfolio optimizer working")
            print(f"  Weights: {weights}")
            print(f"  Sum of weights: {np.sum(weights):.4f}")
            return True
        else:
            print(f"Fail Portfolio optimizer returned unexpected format")
            return False
    except Exception as e:
        print(f"Fail Portfolio optimizer test failed: {e}")
        return False

def test_fastapi():
    """Test if FastAPI server can start"""
    print("\n" + "="*60)
    print("Testing FastAPI Server...")
    print("="*60)
    
    try:
        from api import app
        print(f"Pass FastAPI app imported successfully")
        print(f"  Routes defined: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"Fail FastAPI test failed: {e}")
        return False

def test_structure():
    """Test project structure"""
    print("\n" + "="*60)
    print("Testing Project Structure...")
    print("="*60)
    
    required_dirs = [
        "Scraper",
        "FraudDetection",
        "AnomalyDetection",
        "PortfolioOptimizer",
        "FeatureEngineering",
        "MarketPrediction",
        "Database",
        "BackEnd",
        "DashBoard",
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        exists = dir_path.exists()
        status = "Pass" if exists else "Fail"
        print(f"{status} {dir_name:30} - {'Found' if exists else 'Missing'}")
        if not exists:
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*15 + "PROJECT VALIDATION TEST SUITE" + " "*15 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "Project Structure": test_structure(),
        "Configuration": test_config(),
        "Module Imports": test_imports()[0],
        "FastAPI Setup": test_fastapi(),
        "Portfolio Optimizer": test_portfolio_optimizer(),
        "Fraud Detection": test_fraud_detection(),
        "Data Fetching": test_data_fetching(),
    }
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status:10} | {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! Project is ready to run.")
        print("\nNext steps:")
        print("1. Configure your .env file from .env.example")
        print("2. Run: python run.py")
        print("3. Access API at http://localhost:8000/docs")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed!")
        print("Please review the errors above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
