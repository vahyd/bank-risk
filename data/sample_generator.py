"""
Generates synthetic data for demonstration when real loan portfolio data
is not yet available. Designed to be swapped out when real data is provided.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config.settings import sectors_cfg, regions_cfg, ratings_cfg, bank

np.random.seed(42)

def generate_loan_portfolio(n_loans: int = 2000) -> pd.DataFrame:
    """Generate synthetic loan portfolio data."""

    sectors = sectors_cfg.sectors
    regions = regions_cfg.regions
    grades = ratings_cfg.grades

    # Weights for realistic distributions
    sector_weights = [0.18, 0.14, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.06, 0.05, 0.03, 0.02]
    region_weights = [0.22, 0.20, 0.18, 0.16, 0.14, 0.10]
    grade_weights = [0.05, 0.10, 0.15, 0.25, 0.20, 0.12, 0.07, 0.03, 0.02, 0.01]

    origination_dates = [
        datetime(2026, 7, 27) - timedelta(days=int(d))
        for d in np.random.exponential(scale=900, size=n_loans)
    ]

    terms_months = np.random.choice([12, 24, 36, 48, 60, 84, 120, 180, 240, 300, 360],
                                     size=n_loans,
                                     p=[0.05, 0.08, 0.12, 0.10, 0.15, 0.12, 0.13, 0.10, 0.08, 0.04, 0.03])

    amounts = np.random.lognormal(mean=12.5, sigma=1.2, size=n_loans)
    amounts = np.clip(amounts, 50_000, 50_000_000)

    base_rates = {
        "AAA": 0.035, "AA": 0.042, "A": 0.052, "BBB": 0.065,
        "BB": 0.085, "B": 0.110, "CCC": 0.140, "CC": 0.180, "C": 0.240, "D": 0.350
    }

    assigned_grades = np.random.choice(grades, size=n_loans, p=grade_weights)
    interest_rates = np.array([base_rates[g] + np.random.uniform(-0.005, 0.015) for g in assigned_grades])

    # PD from grade map plus some noise
    grade_pd = ratings_cfg.grade_pd_map
    pd_values = np.array([grade_pd[g] * np.random.uniform(0.5, 2.0) for g in assigned_grades])
    pd_values = np.clip(pd_values, 0.0001, 0.50)

    lgd_values = np.random.beta(a=2, b=3, size=n_loans)
    lgd_values = np.clip(lgd_values, 0.10, 0.95)

    outstanding = amounts * np.random.uniform(0.3, 1.0, size=n_loans)
    committed_undrawn = np.where(np.random.random(n_loans) < 0.3,
                                 amounts * np.random.uniform(0.1, 0.5, size=n_loans), 0)
    ead_values = outstanding + committed_undrawn

    collateral_values = outstanding * np.random.uniform(0.5, 2.0, size=n_loans)
    recovery_amounts = collateral_values * np.random.uniform(0.4, 0.9, size=n_loans)

    ecl_values = pd_values * ead_values * lgd_values
    ul_values = ecl_values * np.random.uniform(1.5, 4.0, size=n_loans)

    # Payment status
    days_past_due = np.random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       1, 1, 1, 1,
                                       30, 30, 30,
                                       60, 60,
                                       90, 90,
                                       180], size=n_loans)

    is_npl = days_past_due >= 90
    is_defaulted = is_npl & (np.random.random(n_loans) < 0.3)
    is_restructured = (np.random.random(n_loans) < 0.04) & ~is_defaulted
    is_written_off = np.random.random(n_loans) < 0.01

    df = pd.DataFrame({
        "loan_id": [f"LN-{i:06d}" for i in range(1, n_loans + 1)],
        "borrower_id": [f"BR-{np.random.randint(1, 801):06d}" for _ in range(n_loans)],
        "borrower_name": [f"Borrower Corp {chr(65 + i % 26)}" for i in range(n_loans)],
        "sector": np.random.choice(sectors, size=n_loans, p=sector_weights),
        "region": np.random.choice(regions, size=n_loans, p=region_weights),
        "origination_date": origination_dates,
        "maturity_date": [origination_dates[i] + timedelta(days=int(terms_months[i] * 30.42))
                          for i in range(n_loans)],
        "term_months": terms_months,
        "original_amount": amounts,
        "outstanding_balance": outstanding,
        "committed_undrawn": committed_undrawn,
        "ead": ead_values,
        "interest_rate": np.round(interest_rates, 4),
        "risk_grade": assigned_grades,
        "probability_of_default": np.round(pd_values, 6),
        "loss_given_default": np.round(lgd_values, 4),
        "expected_credit_loss": np.round(ecl_values, 2),
        "unexpected_loss": np.round(ul_values, 2),
        "collateral_value": np.round(collateral_values, 2),
        "recovery_amount": np.round(recovery_amounts, 2),
        "days_past_due": days_past_due,
        "is_npl": is_npl,
        "is_defaulted": is_defaulted,
        "is_restructured": is_restructured,
        "is_written_off": is_written_off,
        "borrower_income": np.random.lognormal(mean=11, sigma=1.0, size=n_loans),
        "borrower_employees": np.random.randint(5, 5000, size=n_loans),
        "credit_score": np.clip(np.random.normal(680, 80, size=n_loans), 300, 850).astype(int),
    })

    df["origination_date"] = pd.to_datetime(df["origination_date"])
    df["maturity_date"] = pd.to_datetime(df["maturity_date"])

    return df


def generate_market_data(periods: int = 60) -> pd.DataFrame:
    """Generate synthetic market conditions time series."""
    dates = pd.date_range(end=datetime(2026, 7, 27), periods=periods, freq="ME")

    policy_rate = _generate_random_walk(0.0425, 0.0015, periods, 0.01, 0.12)
    yield_10y = policy_rate + np.random.uniform(0.005, 0.025, periods)
    yield_2y = policy_rate + np.random.uniform(-0.005, 0.010, periods)
    yield_spread = yield_10y - yield_2y

    credit_spread_aaa = 0.008 + np.random.uniform(-0.003, 0.005, periods)
    credit_spread_bbb = 0.025 + np.random.uniform(-0.008, 0.015, periods)
    credit_spread_hy = 0.065 + np.random.uniform(-0.020, 0.030, periods)

    fx_rate = _generate_random_walk(1.10, 0.015, periods, 0.80, 1.50)
    fx_volatility = np.random.uniform(0.05, 0.18, periods)

    commodity_index = _generate_random_walk(100, 2.0, periods, 55, 160)
    oil_price = _generate_random_walk(78, 2.5, periods, 40, 130)
    housing_index = _generate_random_walk(220, 1.8, periods, 140, 310)

    pmi = np.clip(np.random.normal(51, 4, periods), 35, 65)
    consumer_confidence = np.clip(np.random.normal(100, 8, periods), 60, 140)

    return pd.DataFrame({
        "date": dates,
        "policy_rate": np.round(policy_rate, 4),
        "yield_10y": np.round(yield_10y, 4),
        "yield_2y": np.round(yield_2y, 4),
        "yield_spread": np.round(yield_spread, 4),
        "credit_spread_aaa": np.round(credit_spread_aaa, 4),
        "credit_spread_bbb": np.round(credit_spread_bbb, 4),
        "credit_spread_hy": np.round(credit_spread_hy, 4),
        "fx_rate": np.round(fx_rate, 4),
        "fx_volatility": np.round(fx_volatility, 4),
        "commodity_index": np.round(commodity_index, 2),
        "oil_price": np.round(oil_price, 2),
        "housing_index": np.round(housing_index, 2),
        "pmi": np.round(pmi, 1),
        "consumer_confidence": np.round(consumer_confidence, 1),
    })


def generate_macro_data(periods: int = 24) -> pd.DataFrame:
    """Generate synthetic macroeconomic indicators."""
    dates = pd.date_range(end=datetime(2026, 7, 27), periods=periods, freq="QE")

    gdp_growth = np.random.uniform(-0.02, 0.045, periods)
    inflation_cpi = np.clip(np.random.normal(0.032, 0.012, periods), -0.01, 0.09)
    unemployment = np.clip(np.random.normal(0.052, 0.015, periods), 0.025, 0.11)
    govt_debt_gdp = np.clip(_generate_random_walk(0.85, 0.02, periods, 0.5, 1.4), 0.5, 1.4)
    fiscal_balance_gdp = np.random.uniform(-0.06, 0.01, periods)
    industrial_production = np.random.uniform(-0.03, 0.06, periods)
    retail_sales = np.random.uniform(-0.02, 0.05, periods)

    return pd.DataFrame({
        "date": dates,
        "gdp_growth_yoy": np.round(gdp_growth, 4),
        "inflation_cpi": np.round(inflation_cpi, 4),
        "unemployment_rate": np.round(unemployment, 4),
        "govt_debt_to_gdp": np.round(govt_debt_gdp, 4),
        "fiscal_balance_to_gdp": np.round(fiscal_balance_gdp, 4),
        "industrial_production_yoy": np.round(industrial_production, 4),
        "retail_sales_yoy": np.round(retail_sales, 4),
    })


def generate_deposit_data(n_depositors: int = 500) -> pd.DataFrame:
    """Generate synthetic deposit/customer data for liquidity analysis."""
    segments = ["Retail", "SME", "Corporate", "Institutional"]
    segment_weights = [0.45, 0.25, 0.20, 0.10]

    balances = np.random.lognormal(mean=11.5, sigma=2.0, size=n_depositors)
    balances = np.clip(balances, 1_000, 200_000_000)

    withdrawal_rates = np.random.beta(a=1.5, b=8, size=n_depositors)

    return pd.DataFrame({
        "depositor_id": [f"DEP-{i:06d}" for i in range(1, n_depositors + 1)],
        "segment": np.random.choice(segments, size=n_depositors, p=segment_weights),
        "balance": np.round(balances, 2),
        "interest_rate": np.round(np.random.uniform(0.005, 0.045, n_depositors), 4),
        "monthly_withdrawal_rate": np.round(withdrawal_rates, 4),
        "account_age_months": np.random.randint(1, 240, n_depositors),
        "is_stable": withdrawal_rates < 0.05,
    })


def _generate_random_walk(start: float, sigma: float, n: int,
                           floor: float = 0, ceiling: float = float("inf")) -> np.ndarray:
    """Helper: generate a random walk with drift toward the start (mean-reverting)."""
    values = np.zeros(n)
    values[0] = start
    for i in range(1, n):
        shock = np.random.normal(0, sigma)
        reversion = 0.05 * (start - values[i - 1])
        values[i] = values[i - 1] + shock + reversion
        values[i] = np.clip(values[i], floor, ceiling)
    return values
