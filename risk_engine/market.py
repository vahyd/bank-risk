"""
Market Risk Engine.
Computes VaR (Historical, Parametric, Monte Carlo), Expected Shortfall,
volatility, drawdowns, rolling correlations, and stress test scenarios.
"""
import numpy as np
import pandas as pd
from scipy import stats


def compute_var_historic(returns: np.ndarray, confidence: float = 0.99) -> float:
    """Historical VaR at given confidence level."""
    return float(np.percentile(returns, (1 - confidence) * 100))


def compute_var_parametric(returns: np.ndarray, confidence: float = 0.99) -> float:
    """Parametric VaR assuming normal distribution."""
    mu = returns.mean()
    sigma = returns.std()
    return float(mu + sigma * stats.norm.ppf(1 - confidence))


def compute_var_monte_carlo(returns: np.ndarray, confidence: float = 0.99,
                             n_simulations: int = 10000) -> float:
    """Monte Carlo VaR simulation."""
    mu = returns.mean()
    sigma = returns.std()
    simulated = np.random.normal(mu, sigma, n_simulations)
    return float(np.percentile(simulated, (1 - confidence) * 100))


def compute_expected_shortfall(returns: np.ndarray, confidence: float = 0.99) -> float:
    """Expected Shortfall (CVaR) — average loss beyond VaR."""
    var = compute_var_historic(returns, confidence)
    tail_losses = returns[returns <= var]
    return float(tail_losses.mean()) if len(tail_losses) > 0 else var


def compute_drawdowns(cumulative_returns: np.ndarray) -> pd.DataFrame:
    """Compute drawdown series from cumulative returns."""
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = (cumulative_returns - running_max) / running_max
    return drawdowns


def compute_max_drawdown(cumulative_returns: np.ndarray) -> float:
    """Maximum drawdown."""
    dd = compute_drawdowns(cumulative_returns)
    return float(dd.min())


def compute_market_risk_metrics(market_data: pd.DataFrame, portfolio_returns_col: str = None) -> dict:
    """Compute comprehensive market risk metrics from market data."""

    results = {}

    # If we have market time-series, compute from the data
    if market_data is not None and len(market_data) > 1:
        latest = market_data.iloc[-1]

        results["policy_rate"] = float(latest.get("policy_rate", 0))
        results["yield_spread"] = float(latest.get("yield_spread", 0))
        results["credit_spread_bbb"] = float(latest.get("credit_spread_bbb", 0))
        results["fx_rate"] = float(latest.get("fx_rate", 0))
        results["fx_volatility"] = float(latest.get("fx_volatility", 0))
        results["commodity_index"] = float(latest.get("commodity_index", 0))
        results["oil_price"] = float(latest.get("oil_price", 0))
        results["housing_index"] = float(latest.get("housing_index", 0))
        results["pmi"] = float(latest.get("pmi", 0))
        results["consumer_confidence"] = float(latest.get("consumer_confidence", 0))

        # Month-over-month changes
        if len(market_data) > 1:
            prev = market_data.iloc[-2]
            results["policy_rate_change"] = float(latest.get("policy_rate", 0) - prev.get("policy_rate", 0))
            results["yield_spread_change"] = float(latest.get("yield_spread", 0) - prev.get("yield_spread", 0))
            results["fx_rate_change"] = float(latest.get("fx_rate", 1) - prev.get("fx_rate", 1)) / float(prev.get("fx_rate", 1))
            results["commodity_change"] = float(latest.get("commodity_index", 100) - prev.get("commodity_index", 100)) / float(prev.get("commodity_index", 100))
            results["oil_price_change"] = float(latest.get("oil_price", 78) - prev.get("oil_price", 78)) / float(prev.get("oil_price", 78))
            results["housing_change"] = float(latest.get("housing_index", 220) - prev.get("housing_index", 220)) / float(prev.get("housing_index", 220))

    # Compute VaR from portfolio if returns provided
    if portfolio_returns_col and portfolio_returns_col in market_data.columns:
        rets = market_data[portfolio_returns_col].dropna().values
        if len(rets) > 10:
            results["var_historic_99"] = compute_var_historic(rets, 0.99)
            results["var_parametric_99"] = compute_var_parametric(rets, 0.99)
            results["var_monte_carlo_99"] = compute_var_monte_carlo(rets, 0.99)
            results["expected_shortfall_99"] = compute_expected_shortfall(rets, 0.99)
            results["var_historic_95"] = compute_var_historic(rets, 0.95)
            results["volatility_annual"] = float(rets.std() * np.sqrt(12))
            results["sharpe_ratio"] = float(rets.mean() / rets.std() * np.sqrt(12)) if rets.std() > 0 else 0
            cum_rets = np.cumprod(1 + rets)
            results["max_drawdown"] = compute_max_drawdown(cum_rets)

    return results
