from aiohttp import request
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import config
import asyncio
import io
from datetime import datetime, timedelta

# --- Data Modules ---
from Scraper.GetMarketData import get_market_data
from Scraper.HOSE.GetHOSEMarketData import get_hose_market_data

# --- Feature Engineering ---
from FeatureEngineering.feature_engineering import create_market_features
from FeatureEngineering.hose_market_features import create_hose_market_features

# --- Anomaly Detection ---
from AnomalyDetection.IsolationForest import compute_risk_score
from AnomalyDetection.HoseMarketIsolationForest import compute_hose_market_anomaly

# --- Portfolio Optimization ---
from PortfolioOptimizer.Optimizer import optimize_portfolio_mean_variance_fraud

# --- Database ---
from Database.MongoDBManager import get_db_manager

# --- Fraud Detection ---
from FraudDetection.fraud_detection_csv import detect_fraud_csv
from FraudDetection.fraud_detection_pdf import detect_fraud_pdf, detect_comprehensive_fraud

# --- LSTM ---
from MarketPrediction.services.predict_service import predict

# Initialize database manager
db_manager = get_db_manager()

# Initialize FastAPI app
app = FastAPI(
    title="Python Finance API",
    description="API for stock scraping, fraud detection, anomaly detection, and portfolio optimization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Allow all origins as fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== MODELS =====================

class MarketDataRequest(BaseModel):
    ticker: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class MarketDataResponse(BaseModel):
    ticker: str
    data: Dict
    status: str

class AnomalyDetectionResponse(BaseModel):
    ticker: str
    anomaly_score: float
    anomalies: List[Dict]
    status: str

class PortfolioOptimizationRequest(BaseModel):
    tickers: List[str]
    risk_aversion: float = 0.6
    fraud_penalty: float = 0.8
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PortfolioOptimizationResponse(BaseModel):
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: Optional[float] = None
    status: str

class FraudDetectionResponse(BaseModel):
    fraud_risk: float
    fraud_indicators: Dict
    status: str

# ===================== HEALTH CHECK =====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "scraper": "available",
            "fraud_detection": "available",
            "anomaly_detection": "available",
            "portfolio_optimization": "available"
        }
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint for frontend"""
    return {
        "status": "ok",
        "message": "Python FastAPI backend is running",
        "version": "1.0.0"
    }

# ===================== SCRAPER ENDPOINTS =====================

@app.post("/api/scraper/market-data", response_model=MarketDataResponse)
async def fetch_market_data(request: MarketDataRequest):
    """
    Fetch market data for a given ticker
    """
    try:
        start_date = request.start_date or config.start_date
        end_date = request.end_date or config.end_date
        
        df = await run_in_threadpool(
            get_market_data,
            request.ticker,
            start_date,
            end_date
        )
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.ticker} between {start_date} and {end_date}. Try a different date range or stock.")
        
        # Convert index to dates
        dates = []
        if hasattr(df.index, 'strftime'):
            dates = df.index.strftime('%Y-%m-%d').tolist()
        elif hasattr(df.index, 'date'):
            dates = [d.strftime('%Y-%m-%d') for d in df.index]
        else:
            dates = [str(d)[:10] for d in df.index.tolist()]
        
        close_prices = df['Close'].tolist() if 'Close' in df.columns else []
        volumes = df['Volume'].tolist() if 'Volume' in df.columns else []
        
        return MarketDataResponse(
            ticker=request.ticker,
            data={
                "close": close_prices,
                "volume": volumes,
                "dates": dates
            },
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in fetch_market_data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scraper/hose-market")
async def fetch_hose_market():
    """
    Fetch HOSE market data
    """
    try:
        df = get_hose_market_data()
        if df is None or df.empty:
            print("Warning: No HOSE data returned. Attempting to fetch...")
            # Try again or return cached data
            return {
                "data": [],
                "count": 0,
                "status": "no_data",
                "message": "No HOSE market data available at this moment. Please try again later."
            }
        
        return {
            "data": df.to_dict('records'),
            "count": len(df),
            "status": "success"
        }
    except Exception as e:
        print(f"Error in hose-market endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching HOSE data: {str(e)}")

@app.get("/api/scraper/company-news")
async def fetch_hose_news_default(days: int = 30):
    """
    Fetch latest HOSE market news (general market news)
    """
    try:
        from Scraper.HOSE.GetHOSENews import get_company_news
        
        news_data = get_company_news(ticker=None, days=days)
        
        if not news_data:
            raise HTTPException(status_code=404, detail="No news available")
        
        return {
            "ticker": "HOSE_MARKET",
            "data": news_data,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

@app.get("/api/scraper/company-news/{ticker}")
async def fetch_company_news(ticker: str, days: int = 30):
    """
    Fetch company news and news sentiment analysis for a specific ticker
    """
    try:
        from Scraper.HOSE.GetHOSENews import get_company_news
        
        news_data = get_company_news(ticker, days=days)
        
        if not news_data:
            raise HTTPException(status_code=404, detail=f"No news found for {ticker}")
        
        return {
            "ticker": ticker,
            "data": news_data,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

# ===================== ANOMALY DETECTION ENDPOINTS =====================

@app.post("/api/anomaly/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(request: MarketDataRequest):
    """
    Detect anomalies in market data for a ticker
    """
    try:
        # Validate ticker
        if not request.ticker or not isinstance(request.ticker, str):
            raise HTTPException(status_code=400, detail="Invalid ticker format")
        
        start_date = request.start_date or config.start_date
        end_date = request.end_date or config.end_date
        
        # Get market data
        df = await run_in_threadpool(
            get_market_data,
            request.ticker,
            start_date,
            end_date
        )
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {request.ticker}")
        
        # Ensure minimum data points
        if len(df) < 20:
            raise HTTPException(status_code=400, detail="Insufficient data for anomaly detection (minimum 20 data points required)")
        
        # Create features
        try:
            features = create_market_features(df)
        except Exception as e:
            # If feature creation fails, use simplified approach
            features = pd.DataFrame({
                'return': df['close'].pct_change() if 'close' in df.columns else [0] * len(df)
            }).fillna(0)
        
        if features is None or features.empty or len(features) < 10:
            raise HTTPException(status_code=400, detail="Unable to extract sufficient features from data")
        
        # Compute anomaly score
        feature_values = features.values if isinstance(features, pd.DataFrame) else features
        anomaly_score = compute_risk_score(feature_values)
        
        # Find anomalous points
        anomalies = []
        if isinstance(anomaly_score, (np.ndarray, list)):
            threshold = np.percentile(anomaly_score, 95)
            anomaly_indices = np.where(np.array(anomaly_score) > threshold)[0]
            anomalies = [{"date": str(df.index[i] if hasattr(df, 'index') else i), 
                        "score": float(anomaly_score[i])} 
                        for i in anomaly_indices[-10:] if i < len(df)]  # Last 10 anomalies
        
        result = {
            "ticker": request.ticker.upper(),
            "anomaly_score": float(np.mean(anomaly_score)) if isinstance(anomaly_score, np.ndarray) else float(anomaly_score),
            "anomalies": anomalies,
            "status": "success"
        }
        
        # Save to MongoDB
        db_manager.save_anomaly_detection_result(request.ticker.upper(), result)
        
        return AnomalyDetectionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in anomaly detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)[:100]}")

@app.get("/api/anomaly/hose-market")
async def detect_hose_anomalies():
    """
    Detect anomalies in HOSE market data
    """
    try:
        df = get_hose_market_data()
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No HOSE data available")
        
        features = create_hose_market_features(df)
        anomalies_df = compute_hose_market_anomaly(features)
        
        merged = df.merge(anomalies_df, left_index=True, right_index=True, how='left')
        
        return {
            "anomalies": merged.to_dict('records')[:50],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===================== PORTFOLIO OPTIMIZATION ENDPOINTS =====================

@app.post("/api/portfolio/optimize", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(request: PortfolioOptimizationRequest):
    """
    Optimize portfolio weights based on fraud scores and risk for multiple assets
    """
    try:
        # Validate input
        if not request.tickers or len(request.tickers) < 2:
            raise HTTPException(status_code=400, detail="At least 2 tickers required for optimization")
        
        # Fetch data for all tickers
        market_data = {}
        returns_data = {}
        fraud_scores = {}
        valid_tickers = []
        
        print(f"Fetching data for {len(request.tickers)} tickers...")
        
        for ticker in request.tickers:
            try:
                ticker_upper = ticker.upper().strip()
                
                # Try MongoDB first
                try:
                    db = db_manager.get_db()
                    ticker_data = db['mixed_ticker_data'].find_one({'symbol': ticker_upper})
                    if ticker_data and 'daily_data' in ticker_data:
                        daily_list = ticker_data['daily_data']
                        if daily_list and len(daily_list) > 0:
                            df = pd.DataFrame(daily_list)
                            df['Close'] = pd.to_numeric(df.get('close', df.get('Close', 0)), errors='coerce')
                            df['Volume'] = pd.to_numeric(df.get('volume', df.get('Volume', 0)), errors='coerce')
                            print(f"Loaded {ticker_upper} from MongoDB ({len(df)} records)")
                        else:
                            df = None
                    else:
                        df = None
                except Exception as db_err:
                    print(f"MongoDB lookup failed for {ticker_upper}: {str(db_err)}")
                    df = None
                
                # Fallback to API if MongoDB doesn't have data
                if df is None or df.empty:
                    try:
                        df = await asyncio.wait_for(
                            run_in_threadpool(
                                get_market_data,
                                ticker_upper,
                                request.start_date or config.start_date,
                                request.end_date or config.end_date
                            ),
                            timeout=10.0
                        )
                        print(f"Fetched {ticker_upper} from API ({len(df) if df is not None else 0} records)")
                    except asyncio.TimeoutError:
                        print(f"Timeout fetching {ticker_upper}")
                        df = None
                    except Exception as api_err:
                        print(f"API fetch failed for {ticker_upper}: {str(api_err)}")
                        df = None
                
                if df is None or df.empty:
                    print(f"No data for ticker {ticker_upper}")
                    continue
                
                market_data[ticker_upper] = df
                valid_tickers.append(ticker_upper)
                
                # Get returns from the data
                if 'return' in df.columns:
                    returns_data[ticker_upper] = df['return'].dropna().values
                elif 'Close' in df.columns:
                    returns_data[ticker_upper] = df['Close'].pct_change().dropna().values
                else:
                    print(f"No Close price data for {ticker_upper}")
                    if ticker_upper in valid_tickers:
                        valid_tickers.remove(ticker_upper)
                    continue
                
                # Create features for fraud scoring
                try:
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        features = create_market_features(df)
                    else:
                        features = pd.DataFrame({'return': returns_data[ticker_upper]})
                except Exception as feat_err:
                    print(f"Feature creation failed for {ticker_upper}: {str(feat_err)}")
                    features = pd.DataFrame({'return': returns_data[ticker_upper]})
                
                # Get fraud score
                try:
                    fraud_scores[ticker_upper] = compute_risk_score(features.values if isinstance(features, pd.DataFrame) else features)
                except Exception as risk_err:
                    print(f"Risk score calculation failed for {ticker_upper}: {str(risk_err)}")
                    fraud_scores[ticker_upper] = 0.5  # Default to neutral risk
            
            except Exception as e:
                print(f"Error processing ticker {ticker}: {str(e)}")
                continue
        
        if len(valid_tickers) < 2:
            raise HTTPException(status_code=400, detail=f"Insufficient valid tickers. Got data for: {valid_tickers}. Need at least 2.")
        
        # Align returns to same length for covariance calculation
        min_len = min(len(r) for r in returns_data.values())
        if min_len < 2:
            raise HTTPException(status_code=400, detail=f"Insufficient return data. Min length: {min_len}, need at least 2.")
        aligned_returns = {}
        for ticker, returns in returns_data.items():
            aligned_returns[ticker] = returns[-min_len:] if len(returns) > min_len else returns
        
        # Create returns array for covariance
        returns_array = np.array([aligned_returns[t] for t in valid_tickers])
        
        # Calculate expected returns and covariance with error handling
        try:
            expected_returns = np.nanmean(returns_array, axis=1)
            expected_returns = np.nan_to_num(expected_returns, nan=0.001)  # Default 0.1% if NaN
            
            # Ensure sufficient data for covariance
            if returns_array.shape[1] > 1:
                cov_matrix = np.cov(returns_array)
            else:
                cov_matrix = np.eye(len(valid_tickers)) * 0.01
            
            # Handle 1D cov_matrix (single asset case, though we require 2+)
            if cov_matrix.ndim == 1:
                cov_matrix = np.diag(cov_matrix)
            
            # Clean NaN values
            if np.isnan(cov_matrix).any():
                cov_matrix = np.eye(len(valid_tickers)) * 0.01
        except Exception as e:
            print(f"Covariance calculation error: {str(e)}")
            expected_returns = np.ones(len(valid_tickers)) * 0.001
            cov_matrix = np.eye(len(valid_tickers)) * 0.01
        
        fraud_scores_array = np.array([fraud_scores.get(t, 0.5) for t in valid_tickers])
        
        # Optimize with fallback
        try:
            optimal_weights = optimize_portfolio_mean_variance_fraud(
                expected_returns=expected_returns,
                cov_matrix=cov_matrix,
                fraud_scores=fraud_scores_array,
                alpha=request.risk_aversion,
                beta=request.fraud_penalty
            )
        except Exception as e:
            print(f"Optimization error: {str(e)}")
            # Simple equal-weight fallback
            optimal_weights = np.ones(len(valid_tickers)) / len(valid_tickers)
        
        # Normalize weights to sum to 1
        optimal_weights = optimal_weights / np.sum(optimal_weights)
        
        # Calculate metrics
        portfolio_return = np.dot(optimal_weights, expected_returns)
        portfolio_variance = np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights))
        portfolio_volatility = np.sqrt(abs(portfolio_variance))  # abs to handle negative variance
        
        # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0.0001 else 0
        
        result = {
            "weights": {ticker: float(weight) for ticker, weight in zip(valid_tickers, optimal_weights)},
            "expected_return": float(portfolio_return),
            "volatility": float(portfolio_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "status": "success"
        }
        
        # Save to MongoDB
        try:
            db_manager.save_portfolio_optimization_result(valid_tickers, result)
        except Exception as db_err:
            print(f"Could not save to MongoDB: {str(db_err)}")
        
        return PortfolioOptimizationResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in portfolio optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)[:100]}")

# ===================== FRAUD DETECTION ENDPOINTS =====================

@app.post("/api/fraud/csv", response_model=FraudDetectionResponse)
async def detect_fraud_from_csv(file: UploadFile = File(...)):
    """
    Detect fraud from CSV file
    """
    try:
        # Read file
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        
        # Detect fraud
        fraud_result = detect_fraud_csv(df)
        
        return FraudDetectionResponse(
            fraud_risk=float(fraud_result.get('fraud_probability', 0)),
            fraud_indicators=fraud_result.get('indicators', {}),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fraud/pdf")
async def detect_fraud_from_pdf(file: UploadFile = File(...)):
    """
    Detect fraud from PDF file (financial statements)
    """
    try:
        # Save uploaded file temporarily
        contents = await file.read()
        
        # Detect fraud
        fraud_result = detect_fraud_pdf(contents)
        
        return {
            "fraud_risk": float(fraud_result.get('fraud_probability', 0)),
            "fraud_indicators": fraud_result.get('indicators', {}),
            "extracted_text": fraud_result.get('extracted_text', ''),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fraud/detect")
async def detect_fraud(file: UploadFile = File(...)):
    """
    Detect fraud from CSV or PDF file
    """
    try:
        contents = await file.read()
        filename = file.filename.lower() if file.filename else ""
        
        if filename.endswith('.csv'):
            # Process CSV
            df = pd.read_csv(io.BytesIO(contents))
            fraud_result = detect_fraud_csv(df)
            
            result = {
                "fraud_risk": float(fraud_result.get('fraud_probability', 0)),
                "fraud_indicators": fraud_result.get('indicators', {}),
                "file_type": "csv",
                "status": "success"
            }
        elif filename.endswith('.pdf'):
            # Process PDF
            fraud_result = detect_fraud_pdf(contents)
            
            result = {
                "fraud_risk": float(fraud_result.get('fraud_probability', 0)),
                "fraud_indicators": fraud_result.get('indicators', {}),
                "extracted_text": fraud_result.get('extracted_text', '')[:500],
                "file_type": "pdf",
                "status": "success"
            }
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or PDF")
        
        # Save to MongoDB
        db_manager.save_fraud_detection_result(result)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in fraud detection: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/fraud/comprehensive")
async def detect_fraud_comprehensive(file: UploadFile = File(...), ticker: str = None):
    """
    Comprehensive fraud detection combining PDF analysis + news sentiment
    Uses Fraud Triangle & Fraud Diamond frameworks
    
    Args:
        file: PDF financial document
        ticker: Stock symbol (optional, for news sentiment analysis)
        
    Returns:
        Comprehensive fraud risk with all four diamond elements
    """
    try:
        from Scraper.HOSE.GetHOSENews import get_company_news
        
        contents = await file.read()
        
        # Get news data if ticker provided
        news_data = None
        if ticker:
            try:
                news_data = get_company_news(ticker, days=30)
            except Exception as e:
                print(f"Warning: Could not fetch news for {ticker}: {str(e)}")
        
        # Comprehensive fraud analysis
        fraud_result = detect_comprehensive_fraud(contents, ticker=ticker, news_data=news_data)
        
        # Prepare response
        response = {
            "ticker": ticker,
            "combined_fraud_risk": float(fraud_result['combined_fraud_risk']),
            "overall_risk_level": fraud_result['overall_risk_level'],
            "pdf_fraud_risk": float(fraud_result['risk_components']['pdf_risk']),
            "news_fraud_risk": float(fraud_result['risk_components']['news_risk']),
            "fraud_diamond_score": {
                "pressure": float(fraud_result['fraud_indicators_summary']['pressure']),
                "opportunity": float(fraud_result['fraud_indicators_summary']['opportunity']),
                "rationalization": float(fraud_result['fraud_indicators_summary']['rationalization']),
                "capability": float(fraud_result['fraud_indicators_summary']['capability'])
            },
            "pdf_analysis": {
                "fraud_probability": float(fraud_result['pdf_fraud_analysis']['fraud_probability']),
                "fraud_diamond_probability": float(fraud_result['pdf_fraud_analysis'].get('fraud_diamond_probability', 0)),
                "risk_factors": fraud_result['pdf_fraud_analysis'].get('risk_factors', {})
            },
            "news_analysis": fraud_result['news_fraud_analysis'],
            "analysis_status": fraud_result['status'],
            "status": "success"
        }
        
        # Save to MongoDB
        db_manager.save_fraud_detection_result(response)
        
        return response
        
    except Exception as e:
        print(f"Error in comprehensive fraud detection: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ===================== MARKET PREDICTION ENDPOINTS =====================

@app.get("/api/prediction/forecast/{ticker}")
async def predict_market(ticker: str, days: int = 5):
    """
    Predict market movement for a ticker
    """
    try:
        df = await run_in_threadpool(
            get_market_data,
            ticker,
            config.start_date,
            config.end_date
        )
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        predictions = predict(df, days)
        result = {
            "ticker": ticker.upper(),
            "predictions": predictions,
            "confidence": 0.0
            }
        
        # Save to MongoDB
        db_manager.save_market_prediction_result(ticker.upper(), days, result)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in market prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== DATA MANAGEMENT ENDPOINTS =====================

@app.post("/api/data/save-results")
async def save_analysis_results(data: Dict):
    """
    Save analysis results to MongoDB
    """
    try:
        db_manager.save_fraud_detection_result(data)
        return {
            "status": "saved",
            "message": "Results saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===================== MONGODB MANAGEMENT ENDPOINTS =====================

@app.get("/api/stock/{symbol}")
def get_stock(symbol: str, limit: int = 100):
    """
    Get stock data from ticker_db by symbol
    """
    data = db_manager.get_stock_from_ticker_db(symbol, limit)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
    
    return {
        "symbol": symbol.upper(),
        "count": len(data),
        "data": data,
        "status": "success"
    }

@app.get("/api/stock/{symbol}/range")
def get_stock_range(symbol: str, start: str, end: str):
    """
    Get stock data from ticker_db within date range
    """
    data = db_manager.get_stock_range_from_ticker_db(symbol, start, end)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol} in the specified range")
    
    return {
        "symbol": symbol.upper(),
        "range": {"start": start, "end": end},
        "count": len(data),
        "data": data,
        "status": "success"
    }

@app.get("/api/data/available-tickers")
async def get_available_tickers():
    """
    Get list of available tickers from ticker_db
    """
    tickers = db_manager.get_available_tickers_from_ticker_db()
    
    return {
        "tickers": tickers,
        "count": len(tickers),
        "status": "success"
    }

@app.get("/api/db/status")
async def get_database_status():
    """
    Check MongoDB connection status
    """
    return {
        "mongodb_connected": db_manager.is_connected,
        "database_name": db_manager.db_name,
        "collection_name": "mixed_ticker_data",
        "status": "connected" if db_manager.is_connected else "disconnected"
    }

@app.get("/api/db/fraud-detection-history")
async def get_fraud_detection_history(limit: int = 10):
    """
    Get recent fraud detection results
    """
    if not db_manager.is_connected:
        return {"results": [], "message": "Database not connected"}
    
    results = db_manager.get_recent_results("fraud_detection_results", limit)
    return {"count": len(results), "results": results, "status": "success"}

@app.get("/api/db/anomaly-detection-history")
async def get_anomaly_detection_history(limit: int = 10):
    """
    Get recent anomaly detection results
    """
    if not db_manager.is_connected:
        return {"results": [], "message": "Database not connected"}
    
    results = db_manager.get_recent_results("anomaly_detection_results", limit)
    return {"count": len(results), "results": results, "status": "success"}

@app.get("/api/db/portfolio-optimization-history")
async def get_portfolio_optimization_history(limit: int = 10):
    """
    Get recent portfolio optimization results
    """
    if not db_manager.is_connected:
        return {"results": [], "message": "Database not connected"}
    
    results = db_manager.get_recent_results("portfolio_optimization_results", limit)
    return {"count": len(results), "results": results, "status": "success"}

@app.get("/api/db/market-prediction-history")
async def get_market_prediction_history(limit: int = 10):
    """
    Get recent market prediction results
    """
    if not db_manager.is_connected:
        return {"results": [], "message": "Database not connected"}
    
    results = db_manager.get_recent_results("market_prediction_results", limit)
    return {"count": len(results), "results": results, "status": "success"}

@app.get("/api/db/trend-analysis-history")
async def get_trend_analysis_history(limit: int = 10):
    """
    Get recent trend analysis results
    """
    if not db_manager.is_connected:
        return {"results": [], "message": "Database not connected"}
    
    results = db_manager.get_recent_results("trend_analysis_results", limit)
    return {"count": len(results), "results": results, "status": "success"}

# ===================== STARTUP/SHUTDOWN EVENTS =====================

@app.on_event("startup")
async def startup_event():
    """
    Initialize database connection on startup
    """
    if not db_manager.is_connected:
        db_manager.connect()
        print(f"Database connection established: {db_manager.db_name}")
        db_manager.create_indexes()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Close database connection on shutdown
    """
    db_manager.disconnect()
    print("Database connection closed")

# ===================== ERROR HANDLERS =====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
