import numpy as np
import pandas as pd
import config

# --- Data ---
from Scraper.GetMarketData import get_market_data #There are but not done
from Scraper.HOSE.GetHOSENews import get_company_news #There are but not done

# --- Feature Engineering ---
from FeatureEngineering.feature_engineering import create_market_features
from FeatureEngineering.financial_features import create_financial_features

# --- Models ---
from AnomalyDetection.IsolationForest import compute_risk_score
from AnomalyDetection.TrainFinancialModel import compute_beneish
from AnomalyDetection.HybridModel import compute_hybrid_score

# --- OCR ---
from AnomalyDetection.OCRTextRisk import compute_text_risk

# --- Portfolio ---
from PortfolioOptimizer.Optimizer import optimize_portfolio_mean_variance_fraud

# --- Database ---
from Database.MongoClient import save_results

# --- HOSE ---
from Scraper.HOSE.GetHOSEMarketData import get_hose_market_data
from FeatureEngineering.hose_market_features import create_hose_market_features
from AnomalyDetection.HoseMarketIsolationForest import compute_hose_market_anomaly

# CONFIG

TICKERS = config.TICKERS
START_DATE = config.start_date
END_DATE = config.end_date

ALPHA = 0.6   # Risk aversion
BETA = 0.8    # Fraud penalty weight

#Load market data
print("Loading market data...")

market_data = {}
returns_data = {}

for ticker in TICKERS:
    df = get_market_data(ticker, START_DATE, END_DATE)
    market_data[ticker] = df
    returns_data[ticker] = create_market_features(df)['return']

returns_df = pd.DataFrame(returns_data).dropna()

expected_returns = returns_df[TICKERS].mean().values
cov_matrix = returns_df[TICKERS].cov().values

#Market Anomaly Detection(Isolation Forest)
print("Detecting market anomalies...")

market_anomaly_scores = {}

for ticker in TICKERS:
    X = returns_data[ticker].values.reshape(-1, 1)

    risk_series = compute_risk_score(X)

    # Take average risk per ticker
    market_anomaly_scores[ticker] = float(np.mean(risk_series))

#Beneish M-scores
print("Computing Beneish M-scores...")

beneish_scores = {}

for ticker in TICKERS:
    financial_df = get_company_news(ticker)

    financial_features = create_financial_features(financial_df)

    # Use latest year
    latest = financial_features.iloc[-1]

    beneish_score = compute_beneish(latest)

    beneish_scores[ticker] = float(beneish_score)

#OCR text risk scores
print("Computing OCR text risk scores...")

text_risk_scores = {}

for ticker in TICKERS:
    text_score = compute_text_risk(ticker)   # from annual reports
    text_risk_scores[ticker] = text_score
    
#HOSE Market Anomaly Scores
print("Fetching hose market data...")

hose_market_df = get_hose_market_data()
hose_market_features = create_hose_market_features(hose_market_df)
hose_market_anomaly = compute_hose_market_anomaly(hose_market_features)

hose_market_scores = dict(
    zip(
        hose_market_anomaly["securitySymbol"],
        hose_market_anomaly["hose_market_anomaly_score"]
    )
)

#Hybrid Fraud Score
print("Combining hybrid fraud scores...")

fraud_scores = []

for ticker in TICKERS:

    hybrid = compute_hybrid_score(
        market_anomaly_scores[ticker],
        beneish_scores[ticker],
        text_risk_scores[ticker],
        hose_market_scores.get(ticker, 0)
    )

    fraud_scores.append(hybrid)

fraud_scores = np.array(fraud_scores)


#Portfolio Optimization with Fraud Penalty
print("Optimizing portfolio...")

optimal_weights = optimize_portfolio_mean_variance_fraud(
    expected_returns,
    cov_matrix,
    fraud_scores,
    alpha=ALPHA,
    beta=BETA
)


#Save results to MongoDB
final_result = []

for i, ticker in enumerate(TICKERS):
    final_result.append({
        "ticker": ticker,
        "expected_return": float(expected_returns[i]),
        "fraud_score": float(fraud_scores[i]),
        "portfolio_weight": float(optimal_weights[i])
    })

save_results(final_result)

print("Pipeline completed successfully.")
print("Optimal Allocation:")
print(pd.DataFrame(final_result))