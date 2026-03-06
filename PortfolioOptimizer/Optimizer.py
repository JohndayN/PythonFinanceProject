import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds
from typing import Dict, Tuple, List, Optional
import warnings

warnings.filterwarnings('ignore')

def optimize_portfolio(expected_returns: np.ndarray,
                        cov_matrix: np.ndarray,
                        fraud_scores: np.ndarray,
                        lambda_penalty: float = 0.5) -> np.ndarray:
    num_assets = len(expected_returns)

    def objective(weights):
        # Portfolio volatility
        portfolio_vol = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )

        # Fraud risk penalty
        fraud_penalty = np.dot(weights, fraud_scores)

        return portfolio_vol + lambda_penalty * fraud_penalty

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    init_guess = num_assets * [1. / num_assets]

    try:
        result = minimize(objective,
                            init_guess,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints,
                            options={'maxiter': 1000})
        return result.x
    except Exception as e:
        print(f"Optimization error: {str(e)}")
        return init_guess

def optimize_portfolio_mean_variance_fraud(
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        fraud_scores: np.ndarray,
        alpha: float = 0.5,      # risk aversion
        beta: float = 0.5        # fraud penalty weight
) -> np.ndarray:
    num_assets = len(expected_returns)
    
    # Validate inputs
    if not isinstance(expected_returns, np.ndarray):
        expected_returns = np.array(expected_returns)
    if not isinstance(cov_matrix, np.ndarray):
        cov_matrix = np.array(cov_matrix)
    if not isinstance(fraud_scores, np.ndarray):
        fraud_scores = np.array(fraud_scores)
    
    # Handle NaN values
    expected_returns = np.nan_to_num(expected_returns, 0)
    fraud_scores = np.nan_to_num(fraud_scores, 0)
    cov_matrix = np.nan_to_num(cov_matrix, 0)

    def objective(weights):
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        fraud_penalty = np.dot(weights, fraud_scores)

        # Negative because we minimize (maximize negative)
        return -(portfolio_return - alpha * portfolio_variance - beta * fraud_penalty)

    constraints = ({
        'type': 'eq',
        'fun': lambda w: np.sum(w) - 1
    })

    bounds = tuple((0, 1) for _ in range(num_assets))
    init_guess = num_assets * [1. / num_assets]

    try:
        result = minimize(objective,
                            init_guess,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints,
                            options={'maxiter': 1000})
        return result.x
    except Exception as e:
        print(f"Optimization error: {str(e)}")
        return init_guess

def optimize_minimum_variance(cov_matrix: np.ndarray) -> np.ndarray:
    num_assets = len(cov_matrix)
    
    def objective(weights):
        return np.dot(weights.T, np.dot(cov_matrix, weights))
    
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    init_guess = num_assets * [1. / num_assets]
    
    try:
        result = minimize(objective,
                            init_guess,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints)
        return result.x
    except:
        return init_guess

def optimize_maximum_sharpe(expected_returns: np.ndarray,
                            cov_matrix: np.ndarray,
                            risk_free_rate: float = 0.02) -> np.ndarray:
    num_assets = len(expected_returns)
    
    def objective(weights):
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        if portfolio_vol == 0:
            return 0
        
        sharpe = (portfolio_return - risk_free_rate) / portfolio_vol
        return -sharpe  # Negative because we minimize
    
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    init_guess = num_assets * [1. / num_assets]
    
    try:
        result = minimize(objective,
                            init_guess,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints)
        return result.x
    except:
        return init_guess

def optimize_risk_parity(cov_matrix: np.ndarray) -> np.ndarray:
    num_assets = len(cov_matrix)
    
    def objective(weights):
        # Volatility of each asset in portfolio
        asset_volatilities = np.sqrt(np.diag(cov_matrix))
        
        # Risk contribution of each asset
        marginal_contrib_to_risk = np.dot(cov_matrix, weights) / np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        contributions = weights * marginal_contrib_to_risk
        
        # Target equal contribution
        target = 1.0 / num_assets
        
        # Sum squared deviations from target
        return np.sum((contributions - target) ** 2)
    
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    init_guess = np.ones(num_assets) / num_assets
    
    try:
        result = minimize(objective,
                        init_guess,
                        method='SLSQP',
                        bounds=bounds,
                        constraints=constraints)
        return result.x
    except:
        return init_guess

def calculate_portfolio_metrics(weights: np.ndarray,
                                expected_returns: np.ndarray,
                                cov_matrix: np.ndarray,
                                risk_free_rate: float = 0.02) -> Dict[str, float]:
    portfolio_return = np.dot(weights, expected_returns)
    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    portfolio_risk = np.sqrt(portfolio_variance)
    
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_risk if portfolio_risk > 0 else 0
    
    return {
        "expected_return": float(portfolio_return),
        "risk": float(portfolio_risk),
        "variance": float(portfolio_variance),
        "sharpe_ratio": float(sharpe_ratio)
    }

def backtesting_metrics(returns: np.ndarray,
                        weights: np.ndarray) -> Dict[str, float]:
    portfolio_returns = np.dot(returns, weights)
    
    cumulative_return = np.prod(1 + portfolio_returns) - 1
    annual_return = (1 + cumulative_return) ** (252 / len(portfolio_returns)) - 1
    annual_volatility = np.std(portfolio_returns) * np.sqrt(252)
    
    sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0
    
    max_drawdown = np.min(np.cumsum(portfolio_returns))
    
    return {
        "cumulative_return": float(cumulative_return),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_volatility),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(max_drawdown)
    }