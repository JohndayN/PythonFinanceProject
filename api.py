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
from fastapi.responses import JSONResponse

# --- Data Modules ---
from Scraper.GetMarketData import get_market_data, get_all_symbols
from Scraper.HOSE.Liveboard import get_market_data as get_hose_market_data

# --- Feature Engineering ---
from FeatureEngineering.feature_engineering import create_market_features
from FeatureEngineering.hose_market_features import create_hose_market_features

# --- Anomaly Detection ---
from AnomalyDetection.IsolationForest import compute_risk_score
from AnomalyDetection.HoseMarketIsolationForest import compute_hose_market_anomaly

# --- Portfolio Optimization ---
from PortfolioOptimizer.Optimizer import *

# --- Database ---
from Database.MongoDBManager import get_db_manager
from Database.utils import df_to_mongo_docs

# --- Fraud Detection ---
from FraudDetection.fraud_detection_csv import detect_fraud_csv
from FraudDetection.fraud_detection_pdf import detect_fraud_pdf, detect_comprehensive_fraud

# --- LSTM ---
from MarketPrediction.services.predict_service import predict

# === REMOVE DUPE ===
def remove_duplicate_prices(prices):
    """Remove duplicate price entries by date"""
    seen = set()
    unique = []

    for p in prices:
        d = str(p.get("date"))
        if d not in seen:
            unique.append(p)
            seen.add(d)

    return unique

# Initialize database manager
db_manager = get_db_manager()

# Initialize FastAPI app
app = FastAPI(
    title="Python Finance API",
    description="API for stock scraping, fraud detection, anomaly detection, and portfolio optimization",
    version="1.0.0"
)

market_cache = {}
CACHE_TTL = 60   # seconds
MAX_CACHE_ITEMS = 200

#Handle error
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
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
        "http://localhost:3003",
        "http://localhost:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== MODELS =====================

class MarketDataRequest(BaseModel):
    ticker: str
    source: Optional[str] = "VCI"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class MarketDataResponse(BaseModel):
    ticker: str
    data: Dict
    status: str

class AnomalyDetectionResponse(BaseModel):
    ticker: str
    source: Optional[str] = "VCI"
    anomaly_score: float
    anomalies: List[Dict]
    status: str

class PortfolioOptimizationRequest(BaseModel):
    tickers: List[str]
    source: Optional[str] = "VCI"
    risk_aversion: float = 0.6
    fraud_penalty: float = 0.8
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ConfidenceBand(BaseModel):
    lower: float
    upper: float
    
class FrontierBand(BaseModel):
    risk: float
    lower: float
    upper: float
class PortfolioOptimizationResponse(BaseModel):
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: Optional[float] = None
    efficient_frontier: Optional[List[Dict]] = None
    confidence_band: Optional[ConfidenceBand] = None
    frontier_confidence_band: Optional[List[FrontierBand]] = None
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

# ===================== SOURCE =====================

def normalize_source(source: Optional[str]) -> str:
    """Normalize and validate data source"""
    if not source:
        return config.source

    source = source.upper()

    if source not in ["VCI", "KBS"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid source. Allowed sources: VCI, KBS"
        )

    return source


async def get_cached_market_data(ticker, start_date, end_date, source):
    """Fetch market data with caching and fallback"""

    cache_key = f"{ticker}_{source}_{start_date}_{end_date}"
    now = datetime.now()

    # ================= CACHE HIT =================
    if cache_key in market_cache:
        cached = market_cache[cache_key]

        if (now - cached["time"]).seconds < CACHE_TTL:
            print(f"Cache hit: {ticker}")
            return cached["data"]

    # ================= FETCH DATA =================
    try:
        df = await run_in_threadpool(
            get_market_data,
            ticker,
            start_date,
            end_date,
            source
        )

    except Exception as e:

        print(f"{source} failed for {ticker}, trying fallback")

        # fallback source
        fallback = "KBS" if source == "VCI" else "VCI"

        df = await run_in_threadpool(
            get_market_data,
            ticker,
            start_date,
            end_date,
            fallback
        )

    # ================= SAVE CACHE =================
    market_cache[cache_key] = {
        "data": df,
        "time": now
    }
    
    # prevent memory explosion
    if len(market_cache) > MAX_CACHE_ITEMS:
        oldest = list(market_cache.keys())[:50]
        for k in oldest:
            market_cache.pop(k, None)
        return df

# ===================== SCRAPER ENDPOINTS =====================

@app.post("/api/scraper/market-data", response_model=MarketDataResponse)
async def fetch_market_data(request: MarketDataRequest):
    """
    Fetch market data for a given ticker and save to MongoDB
    """
    try:
        start_date = request.start_date or config.start_date
        end_date = request.end_date or config.end_date

        source = normalize_source(request.source)

        df = await get_cached_market_data(
            request.ticker,
            start_date,
            end_date,
            source
        )
        
        # ================= FIX TIME COLUMN =================
        if df.index.name == "time":
            df = df.reset_index()

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])

        df = df.reset_index(drop=True)

        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {request.ticker}"
            )

        ticker = request.ticker.upper()
        df["symbol"] = ticker

        # ================= SAVE TO MONGODB =================

        try:
            db = db_manager.db

            prices = df.apply(
                lambda r: {
                    "date": str(r.get("time")),
                    "open": float(r.get("open", 0)),
                    "high": float(r.get("high", 0)),
                    "low": float(r.get("low", 0)),
                    "close": float(r.get("close", 0)),
                    "volume": float(r.get("volume", 0)),
                    "return": float(r.get("return", 0)),
                    "log_return": float(r.get("log_return", 0))
                },
                axis=1
            ).tolist()

            # remove duplicates
            prices = remove_duplicate_prices(prices)

            # prevent huge Mongo documents
            prices = prices[-5000:]

            doc = {
                "symbol": ticker,
                "source": source,
                "updated_at": datetime.utcnow(),
                "prices": prices
            }

            db["mixed_ticker_data"].update_one(
                {"symbol": ticker},
                {
                    "$set": {
                        "source": source,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "prices": {
                            "$each": prices
                        }
                    }
                },
                upsert=True
            )

        except Exception as db_err:
            print("MongoDB save failed:", db_err)

        # ================= RETURN DATA TO FRONTEND =================

        date_col = None
        for col in ["time", "date", "datetime"]:
            if col in df.columns:
                date_col = col
                break

        if date_col:
            date = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d").tolist()
        else:
            date = df.index.astype(str).tolist()

        close_prices = df["close"].tolist() if "close" in df.columns else []
        volumes = df["volume"].tolist() if "volume" in df.columns else []

        return MarketDataResponse(
            ticker=ticker,
            data={
                "dates": date,
                "open": df["open"].tolist(),
                "high": df["high"].tolist(),
                "low": df["low"].tolist(),
                "close": df["close"].tolist(),
                "volume": df["volume"].tolist()
            },
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in fetch_market_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scraper/hose-market")
async def fetch_hose_market(board: str = "Auction"):
    try:
        df = await run_in_threadpool(get_hose_market_data, board)
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
            "board": board,
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

# ===================== GET ALL STOCK =====================

@app.get("/api/scraper/all-tickers")
async def fetch_all_ticker_data(source: str = "VCI"):
    """
    Fetch latest market data for all tickers
    """

    try:
        tickers = get_all_symbols()

        if not tickers:
            raise HTTPException(status_code=404, detail="No tickers found")

        results = []

        for ticker in tickers: 
            try:
                df = await run_in_threadpool(
                    get_market_data,
                    ticker,
                    config.start_date,
                    config.end_date,
                    source
                )

                if df is None or df.empty:
                    continue

                last = df.iloc[-1]

                results.append({
                    "ticker": ticker,
                    "close": float(last.get("close", 0)),
                    "volume": float(last.get("volume", 0)),
                    "return": float(last.get("return", 0))
                })
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Failed {ticker}: {e}")

        return {
            "count": len(results),
            "data": results,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ===================== GET ALL STOCK FROM MONGO =====================    

@app.get("/api/scraper/all-tickers-db")
async def get_all_tickers_from_db(source: str = "VCI"):

    try:

        db = db_manager.db

        docs = list(
            db["mixed_ticker_data"].find(
                {},
                {
                    "symbol": 1,
                    "company_name": 1,
                    "prices": {"$slice": -1},
                    "_id": 0
                }
            )
        )

        results = []

        for doc in docs:

            ticker = doc.get("symbol")
            company = doc.get("company_name")

            prices = doc.get("prices", [])

            if not prices:
                continue

            last = prices[-1]

            results.append({
                "ticker": ticker,
                "company_name": company,
                "close": float(last.get("close", 0)),
                "volume": float(last.get("volume", 0)),
                "return": float(last.get("return", 0))
            })

        return {
            "count": len(results),
            "data": results,
            "source": source,
            "status": "success"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/api/market/snapshot")
async def market_snapshot():

    db = db_manager.db

    cursor = db["mixed_ticker_data"].find(
        {},
        {
            "symbol":1,
            "company_name":1,
            "prices":{"$slice":-1},
            "_id":0
        }
    )

    docs = await run_in_threadpool(list, cursor)

    results = []

    for doc in docs:

        prices = doc.get("prices", [])

        if not prices:
            continue

        p = prices[-1]

        results.append({
            "symbol": doc["symbol"],
            "company_name": doc.get("company_name"),
            "close": p.get("close"),
            "volume": p.get("volume"),
            "return": p.get("return"),
            "date": p.get("date")
        })

    return {"data": results}

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
        
        source = normalize_source(request.source)

        df = await get_cached_market_data(
            request.ticker,
            start_date,
            end_date,
            source
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
            threshold = np.quantile(anomaly_score, 0.95)
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
    try:
        df = await run_in_threadpool(get_hose_market_data)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No HOSE auction data available")
        
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
async def process_ticker(ticker: str, request):
    ticker_upper = ticker.upper().strip()

    try:
        df = None

        # ================= MongoDB =================
        try:
            db = db_manager.db
            ticker_data = db['mixed_ticker_data'].find_one(
                {'symbol': ticker_upper},
                {"symbol":1, "company_name":1, "prices":1}
            )

            if ticker_data and 'prices' in ticker_data:
                daily_list = ticker_data['prices']

                if daily_list:
                    df = pd.DataFrame(daily_list)
                    df.columns = df.columns.str.lower()

                    df['close'] = pd.to_numeric(df.get('close'), errors='coerce')
                    df['volume'] = pd.to_numeric(df.get('volume'), errors='coerce')

                    print(f"Loaded {ticker_upper} from MongoDB")

        except Exception as mongo_err:
            print(f"MongoDB error: {mongo_err}")
            df = None

        # ================= API FALLBACK =================
        if df is None or df.empty:

            source = normalize_source(request.source)

            df = await asyncio.wait_for(
                get_cached_market_data(
                    ticker_upper,
                    request.start_date or config.start_date,
                    request.end_date or config.end_date,
                    source
                ),
                timeout=10
            )

            if df is not None:
                df.columns = df.columns.str.lower()

        if df is None or df.empty:
            return None

        # ================= RETURNS =================
        if 'return' in df.columns:
            returns = df['return'].dropna().values
        else:
            returns = df['close'].pct_change().dropna().values

        if len(returns) < 3:
            return None

        # ================= FEATURES =================
        try:
            features = create_market_features(df)
        except:
            features = pd.DataFrame({'return': returns})

        # ================= FRAUD SCORE =================
        try:
            score = compute_risk_score(features.values)

            if isinstance(score, (list, np.ndarray)):
                fraud_score = float(np.mean(score))
            else:
                fraud_score = float(score)

        except:
            fraud_score = 0.5

        fraud_score = np.clip(fraud_score, 0, 1)

        return {
            "ticker": ticker_upper,
            "df": df,
            "returns": returns,
            "fraud_score": fraud_score
        }

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None


@app.post("/api/portfolio/optimize", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(request: PortfolioOptimizationRequest):

    try:

        if not request.tickers:
            raise HTTPException(status_code=400, detail="At least 1 ticker required")

        print(f"Fetching {len(request.tickers)} tickers")

        # ================= FETCH DATA CONCURRENTLY =================
        tasks = [process_ticker(t, request) for t in request.tickers]

        results = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=20
        )

        market_data = {}
        returns_data = {}
        fraud_scores = {}
        valid_tickers = []

        for r in results:

            if r is None:
                continue

            ticker = r["ticker"]

            market_data[ticker] = r["df"]
            returns_data[ticker] = r["returns"]
            fraud_scores[ticker] = r["fraud_score"]

            valid_tickers.append(ticker)

        if len(valid_tickers) == 0:
            raise HTTPException(status_code=400, detail="No valid tickers found")

        # ================= ALIGN RETURNS =================
        min_len = min(len(r) for r in returns_data.values())

        if min_len < 3:
            raise HTTPException(status_code=400, detail="Insufficient return data")

        aligned_returns = {
            ticker: returns[-min_len:]
            for ticker, returns in returns_data.items()
        }

        returns_array = np.array([aligned_returns[t] for t in valid_tickers])

        # shape = (assets, time)

        # ================= EXPECTED RETURNS =================
        expected_returns = np.nanmean(returns_array, axis=1) * 252

        expected_returns = np.nan_to_num(
            expected_returns,
            nan=0.05,
            posinf=0.01,
            neginf=-0.01
        )

        # ================= COVARIANCE MATRIX =================

        if len(valid_tickers) == 1:

            var = np.var(returns_array[0]) * 252

            cov_matrix = np.array([[var if var > 0 else 1e-6]])

        else:

            cov_matrix = np.cov(returns_array) * 252

            if cov_matrix.ndim == 1:
                cov_matrix = np.diag(cov_matrix)

            if np.isnan(cov_matrix).any():
                cov_matrix = np.eye(len(valid_tickers)) * 0.01

        # ================= FRAUD ARRAY =================
        fraud_scores_array = np.array([
            fraud_scores.get(t, 0.5) for t in valid_tickers
        ])

        # ================= OPTIMIZATION =================
        try:

            if len(valid_tickers) == 1:

                optimal_weights = np.array([1.0])

            else:

                optimal_weights = optimize_portfolio_mean_variance_fraud(
                    expected_returns=expected_returns,
                    cov_matrix=cov_matrix,
                    fraud_scores=fraud_scores_array,
                    alpha=request.risk_aversion,
                    beta=request.fraud_penalty
                )

        except Exception as opt_err:

            print(f"Optimizer failure: {opt_err}")

            optimal_weights = np.ones(len(valid_tickers)) / len(valid_tickers)

        # normalize weights
        optimal_weights = optimal_weights / np.sum(optimal_weights)

        # ================= METRICS =================

        portfolio_return = float(np.dot(optimal_weights, expected_returns))

        portfolio_variance = float(
            np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights))
        )

        portfolio_volatility = float(np.sqrt(abs(portfolio_variance)))

        risk_free_rate = 0.02 / 252

        sharpe_ratio = (
            (portfolio_return - risk_free_rate) / portfolio_volatility
            if portfolio_volatility > 1e-6
            else 0
        
        )
        
        # ================= FRONTIER =================
        frontier = generate_efficient_frontier(
            expected_returns,
            cov_matrix,
            n_points=60
        )
        
        # ================= CONFIDENCE BAND =================
        lower, upper = compute_confidence_band(
            optimal_weights,
            expected_returns,
            cov_matrix
        )
        
        # ================= FRONTIER BAND =================
        frontier_band = compute_frontier_confidence_band(
            frontier,
            cov_matrix,
            expected_returns
        )

        result = {
            "weights": {
                t: float(w) for t, w in zip(valid_tickers, optimal_weights)
            },
            "expected_return": portfolio_return,
            "volatility": portfolio_volatility,
            "sharpe_ratio": float(sharpe_ratio),

            "efficient_frontier": frontier,
            "confidence_band": {
                "lower": lower,
                "upper": upper
            },
            
            "frontier_confidence_band": frontier_band,

            "status": "success"
        }

        
        # ================= SAVE RESULT =================
        try:
            db_manager.save_portfolio_optimization_result(valid_tickers, result)
        except Exception as db_err:
            print(f"Mongo save failed: {db_err}")

        return PortfolioOptimizationResponse(**result)

    except HTTPException:
        raise

    except Exception as e:

        print(f"Portfolio optimization error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


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
    try:
        df = await get_cached_market_data(
            ticker,
            config.start_date,
            config.end_date,
            config.source
        )

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        # Ensure datetime
        if "time" in df.columns:
            df["date"] = pd.to_datetime(df["time"])
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        else:
            df["date"] = df.index

        # Convert to JSON format for candlestick
        historical = df.tail(120)[["date","open","high","low","close"]].copy()
        historical["date"] = pd.to_datetime(historical["date"]).dt.strftime("%Y-%m-%d")

        predictions = predict(df, ticker, days)

        result = {
            "ticker": ticker.upper(),
            "historical": historical.to_dict("records"),
            "predictions": predictions["prediction"],
            "upper": predictions["upper"],
            "lower": predictions["lower"],
            "confidence": 0.0
        }

        db_manager.save_market_prediction_result(ticker.upper(), days, result)

        return result

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
