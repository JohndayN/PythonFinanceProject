import numpy as np
from scipy.optimize import minimize
from typing import Dict
import warnings

warnings.filterwarnings("ignore")

MIN_WEIGHT = 0.05
MAX_WEIGHT = 0.6

def _prepare_array(x):
    """Ensure numpy float array and remove NaNs"""
    arr = np.asarray(x, dtype=float)
    return np.nan_to_num(arr)


def optimize_portfolio(expected_returns,
                        cov_matrix,
                        fraud_scores,
                        lambda_penalty: float = 0.5):

    expected_returns = _prepare_array(expected_returns)
    cov_matrix = _prepare_array(cov_matrix)
    fraud_scores = _prepare_array(fraud_scores)

    num_assets = len(expected_returns)

    def objective(weights):
        portfolio_vol = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )

        fraud_penalty = np.dot(weights, fraud_scores)

        return float(portfolio_vol + lambda_penalty * fraud_penalty)

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    min_w = min(MIN_WEIGHT, 1.0 / num_assets)
    max_w = min(MAX_WEIGHT, 1.0)
    bounds = tuple((min_w, max_w) for _ in range(num_assets))
    init_guess = np.ones(num_assets) / num_assets

    try:
        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000}
        )

        if result.success:
            return result.x
        else:
            print("Optimization failed:", result.message)
            return init_guess

    except Exception as e:
        print("Optimization error:", str(e))
        return init_guess


def optimize_portfolio_mean_variance_fraud(
        expected_returns,
        cov_matrix,
        fraud_scores,
        alpha: float = 0.5,
        beta: float = 0.5
):

    expected_returns = _prepare_array(expected_returns)
    cov_matrix = _prepare_array(cov_matrix)
    fraud_scores = _prepare_array(fraud_scores)

    num_assets = len(expected_returns)

    def objective(weights):

        portfolio_return = np.dot(weights, expected_returns)

        portfolio_variance = np.dot(
            weights.T,
            np.dot(cov_matrix, weights)
        )

        fraud_penalty = np.dot(weights, fraud_scores)

        value = -(portfolio_return
                  - alpha * portfolio_variance
                  - beta * fraud_penalty)

        return float(value)

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})

    min_w = min(MIN_WEIGHT, 1.0 / num_assets)
    max_w = min(MAX_WEIGHT, 1.0)
    bounds = tuple((min_w, max_w) for _ in range(num_assets))
    init_guess = np.ones(num_assets) / num_assets

    try:
        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000}
        )

        if result.success:
            return result.x
        else:
            print("Optimization failed:", result.message)
            return init_guess

    except Exception as e:
        print("Optimization error:", str(e))
        return init_guess


def optimize_minimum_variance(cov_matrix):

    cov_matrix = _prepare_array(cov_matrix)

    num_assets = len(cov_matrix)

    def objective(weights):
        value = np.dot(weights.T, np.dot(cov_matrix, weights))
        return float(value)

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})

    min_w = min(MIN_WEIGHT, 1.0 / num_assets)
    max_w = min(MAX_WEIGHT, 1.0)
    bounds = tuple((min_w, max_w) for _ in range(num_assets))
    init_guess = np.ones(num_assets) / num_assets

    try:
        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            return result.x
        else:
            return init_guess

    except Exception:
        return init_guess


def optimize_maximum_sharpe(expected_returns,
                            cov_matrix,
                            risk_free_rate: float = 0.02):

    expected_returns = _prepare_array(expected_returns)
    cov_matrix = _prepare_array(cov_matrix)

    num_assets = len(expected_returns)

    def objective(weights):

        portfolio_return = np.dot(weights, expected_returns)

        portfolio_vol = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )

        if portfolio_vol <= 1e-8:
            return 0.0

        sharpe = (portfolio_return - risk_free_rate) / portfolio_vol

        return float(-sharpe)

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})

    min_w = min(MIN_WEIGHT, 1.0 / num_assets)
    max_w = min(MAX_WEIGHT, 1.0)
    bounds = tuple((min_w, max_w) for _ in range(num_assets))
    init_guess = np.ones(num_assets) / num_assets

    try:
        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            return result.x
        else:
            return init_guess

    except Exception:
        return init_guess


def optimize_risk_parity(cov_matrix):

    cov_matrix = _prepare_array(cov_matrix)

    num_assets = len(cov_matrix)

    def objective(weights):

        portfolio_vol = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )

        if portfolio_vol <= 1e-8:
            return 0.0

        marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
        contributions = weights * marginal_contrib

        target = 1.0 / num_assets

        value = np.sum((contributions - target) ** 2)

        return float(value)

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})

    min_w = min(MIN_WEIGHT, 1.0 / num_assets)
    max_w = min(MAX_WEIGHT, 1.0)
    bounds = tuple((min_w, max_w) for _ in range(num_assets))
    init_guess = np.ones(num_assets) / num_assets

    try:
        result = minimize(
            objective,
            init_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            return result.x
        else:
            return init_guess

    except Exception:
        return init_guess


def calculate_portfolio_metrics(weights,
                                expected_returns,
                                cov_matrix,
                                risk_free_rate: float = 0.02):

    expected_returns = _prepare_array(expected_returns)
    cov_matrix = _prepare_array(cov_matrix)

    portfolio_return = np.dot(weights, expected_returns)

    portfolio_variance = np.dot(
        weights.T,
        np.dot(cov_matrix, weights)
    )

    portfolio_risk = np.sqrt(portfolio_variance)

    if portfolio_risk <= 1e-8:
        sharpe_ratio = 0.0
    else:
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_risk
        
    annual_return = portfolio_return * 252
    annual_vol = portfolio_risk * np.sqrt(252)

    return {
        "expected_return": float(portfolio_return),
        "volatility": float(portfolio_risk),
        "variance": float(portfolio_variance),
        "sharpe_ratio": float(sharpe_ratio),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_vol)
    }


def backtesting_metrics(returns, weights):

    returns = _prepare_array(returns)

    portfolio_returns = np.dot(returns, weights)

    cumulative_return = np.prod(1 + portfolio_returns) - 1

    annual_return = (1 + cumulative_return) ** (
        252 / len(portfolio_returns)
    ) - 1

    annual_volatility = np.std(portfolio_returns) * np.sqrt(252)

    if annual_volatility <= 1e-8:
        sharpe = 0.0
    else:
        sharpe = annual_return / annual_volatility

    max_drawdown = np.min(np.cumsum(portfolio_returns))

    return {
        "cumulative_return": float(cumulative_return),
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_volatility),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(max_drawdown)
    }

def generate_efficient_frontier(expected_returns,
                                cov_matrix,
                                n_points=40):

    expected_returns = _prepare_array(expected_returns)
    cov_matrix = _prepare_array(cov_matrix)

    num_assets = len(expected_returns)

    frontier = []

    target_returns = np.linspace(
        np.min(expected_returns) * 0.5,
        np.max(expected_returns) * 1.5,
        n_points
    )

    for target in target_returns:

        def objective(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: np.dot(w, expected_returns) - target},
        )

        min_w = min(MIN_WEIGHT, 1.0 / num_assets)
        max_w = min(MAX_WEIGHT, 1.0)

        bounds = tuple((min_w, max_w) for _ in range(num_assets))

        init_guess = np.ones(num_assets) / num_assets

        try:

            result = minimize(
                objective,
                init_guess,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 500}
            )

            if result.success:

                w = result.x

                port_return = np.dot(w, expected_returns)

                port_vol = np.sqrt(
                    np.dot(w.T, np.dot(cov_matrix, w))
                )

                frontier.append({
                    "risk": float(port_vol),
                    "return": float(port_return),
                    "weights": w.tolist()
                })

        except Exception:
            continue

    return frontier

def compute_confidence_band(weights, expected_returns, cov_matrix, n_sim=1000):

    simulations = []

    daily_mean = expected_returns / 252
    daily_cov = cov_matrix / 252

    for _ in range(n_sim):

        sim_returns = np.random.multivariate_normal(
            daily_mean,
            daily_cov
        )

        port_return = np.dot(weights, sim_returns) * 252

        simulations.append(port_return)

    lower = np.percentile(simulations, 5)
    upper = np.percentile(simulations, 95)

    return float(lower), float(upper)

def compute_frontier_confidence_band(frontier, cov_matrix, expected_returns):

    bands = []

    sims = np.random.multivariate_normal(
        expected_returns,
        cov_matrix,
        size=500
    )

    for point in frontier:

        w = np.array(point["weights"])

        portfolio_returns = sims @ w

        lower = np.percentile(portfolio_returns, 5)
        upper = np.percentile(portfolio_returns, 95)

        bands.append({
            "risk": point["risk"],
            "lower": float(lower),
            "upper": float(upper)
        })

    return bands
