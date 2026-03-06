"""
API Diagnostic Script
Tests all major endpoints and identifies issues
Run with: python test_api_endpoints.py
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_result(test_name, success, message=""):
    status = f"{Colors.GREEN}PASS{Colors.END}" if success else f"{Colors.RED}FAIL{Colors.END}"
    print(f"[{status}] {test_name}")
    if message:
        print(f"      {message}")

def test_api_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_result("API Health Check", True, f"Status: {data.get('status')}")
            return True
        else:
            print_result("API Health Check", False, f"Status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result("API Health Check", False, "Cannot connect to API on port 8000")
        return False
    except Exception as e:
        print_result("API Health Check", False, f"Error: {str(e)}")
        return False

def test_database_status():
    """Test MongoDB connection"""
    try:
        response = requests.get(f"{BASE_URL}/api/db/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            is_connected = data.get('mongodb_connected', False)
            print_result(
                "MongoDB Connection", 
                is_connected,
                f"Status: {'Connected' if is_connected else 'Disconnected'}"
            )
            return is_connected
        else:
            print_result("MongoDB Connection", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result("MongoDB Connection", False, f"Error: {str(e)}")
        return False

def test_available_tickers():
    """Get available tickers"""
    try:
        response = requests.get(f"{BASE_URL}/api/data/available-tickers", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tickers = data.get('tickers', [])
            print_result(
                "Available Tickers",
                len(tickers) > 0,
                f"Found {len(tickers)} tickers: {', '.join(tickers[:3])}..."
            )
            return tickers
        else:
            print_result("Available Tickers", False, f"Status code: {response.status_code}")
            return []
    except Exception as e:
        print_result("Available Tickers", False, f"Error: {str(e)}")
        return []

def test_anomaly_detection():
    """Test anomaly detection endpoint"""
    try:
        payload = {"ticker": "FPT"}
        response = requests.post(
            f"{BASE_URL}/api/anomaly/detect",
            json=payload,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            score = data.get('anomaly_score', 0)
            print_result(
                "Anomaly Detection",
                True,
                f"Ticker: FPT, Score: {score:.3f}, Status: {data.get('status')}"
            )
            return True
        elif response.status_code == 404:
            print_result("Anomaly Detection", False, "No data found for FPT (vnstock API may be down)")
            return False
        else:
            print_result("Anomaly Detection", False, f"Status code: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_result("Anomaly Detection", False, "Request timeout (API may be slow or processing)")
        return False
    except Exception as e:
        print_result("Anomaly Detection", False, f"Error: {str(e)[:100]}")
        return False

def test_portfolio_optimization():
    """Test portfolio optimization endpoint"""
    try:
        payload = {
            "tickers": ["FPT", "HPG", "VNM"],
            "risk_aversion": 0.6,
            "fraud_penalty": 0.8
        }
        response = requests.post(
            f"{BASE_URL}/api/portfolio/optimize",
            json=payload,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            weights = data.get('optimal_weights', {})
            ret = data.get('expected_return', 0)
            risk = data.get('portfolio_risk', 0)
            print_result(
                "Portfolio Optimization",
                True,
                f"Return: {ret:.4f}, Risk: {risk:.4f}, Tickers: 3"
            )
            return True
        elif response.status_code == 400:
            print_result("Portfolio Optimization", False, "Data validation error (missing market data)")
            return False
        else:
            print_result("Portfolio Optimization", False, f"Status code: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_result("Portfolio Optimization", False, "Request timeout")
        return False
    except Exception as e:
        print_result("Portfolio Optimization", False, f"Error: {str(e)[:100]}")
        return False

def test_market_prediction():
    """Test market prediction endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/prediction/forecast/FPT?days=30",
            timeout=5,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            print_result(
                "Market Prediction",
                True,
                f"Ticker: FPT, Status: {status} (LSTM training in progress)"
            )
            return True
        elif response.status_code == 404:
            print_result("Market Prediction", False, "No data found for FPT")
            return False
        else:
            print_result("Market Prediction", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result("Market Prediction", False, f"Error: {str(e)}")
        return False

def test_fraud_detection_history():
    """Test fraud detection history retrieval"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/db/fraud-detection-history?limit=5",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            message = f"Found {count} saved fraud analyses"
            print_result("Fraud Detection History", count >= 0, message)
            return True
        else:
            print_result("Fraud Detection History", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result("Fraud Detection History", False, f"Error: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BLUE}=== Python Finance API Diagnostic Test ==={Colors.END}")
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Test basic connectivity
    print(f"{Colors.YELLOW}[1] BASIC CONNECTIVITY{Colors.END}")
    api_running = test_api_health()
    results.append(("API Health", api_running))
    
    if not api_running:
        print(f"\n{Colors.RED}API is not running! Cannot proceed with testing.{Colors.END}")
        print("Start the API with: python run.py")
        return
    
    # Test database
    print(f"\n{Colors.YELLOW}[2] DATABASE{Colors.END}")
    db_ok = test_database_status()
    results.append(("MongoDB", db_ok))
    
    # Test data
    print(f"\n{Colors.YELLOW}[3] DATA ACCESS{Colors.END}")
    tickers = test_available_tickers()
    results.append(("Tickers Available", len(tickers) > 0))
    
    # Test endpoints
    print(f"\n{Colors.YELLOW}[4] ANALYSIS ENDPOINTS{Colors.END}")
    print("(This may take 10-20 seconds if vnstock API is slow...)\n")
    
    anomaly_ok = test_anomaly_detection()
    results.append(("Anomaly Detection", anomaly_ok))
    
    portfolio_ok = test_portfolio_optimization()
    results.append(("Portfolio Optimization", portfolio_ok))
    
    prediction_ok = test_market_prediction()
    results.append(("Market Prediction", prediction_ok))
    
    # Test data persistence
    print(f"\n{Colors.YELLOW}[5] DATA PERSISTENCE{Colors.END}")
    history_ok = test_fraud_detection_history()
    results.append(("Result Storage", history_ok))
    
    # Summary
    print(f"\n{Colors.BLUE}=== TEST SUMMARY ==={Colors.END}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  [{status}] {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}All systems operational!{Colors.END}\n")
    elif passed >= total * 0.7:
        print(f"{Colors.YELLOW}Mostly working. Some features may be unavailable.{Colors.END}")
        print(f"Check data sources (vnstock API) and MongoDB connection.\n")
    else:
        print(f"{Colors.RED}Multiple issues detected. See troubleshooting guide.{Colors.END}")
        print(f"File: API_TROUBLESHOOTING.md\n")

if __name__ == "__main__":
    main()
