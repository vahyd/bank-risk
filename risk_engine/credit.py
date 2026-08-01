"""
Credit Portfolio Risk Engine.
Computes PD, EAD, LGD, ECL, UL, NPL ratios, default rates, and recovery metrics.
"""
import numpy as np
import pandas as pd
from config.settings import bank


def compute_credit_metrics(portfolio: pd.DataFrame) -> dict:
    """Compute all credit risk metrics from loan portfolio data."""

    total_loans = portfolio["outstanding_balance"].sum()
    total_ead = portfolio.get("ead", portfolio["outstanding_balance"]).sum()
    n_loans = len(portfolio)

    # NPL Ratio
    npl_loans = portfolio[portfolio.get("is_npl", portfolio["days_past_due"] >= 90)]
    npl_balance = npl_loans["outstanding_balance"].sum()
    npl_ratio = npl_balance / total_loans if total_loans > 0 else 0

    # Default Rate
    defaulted = portfolio[portfolio.get("is_defaulted", False)]
    default_rate = len(defaulted) / n_loans if n_loans > 0 else 0

    # Delinquency rates
    dpd = portfolio.get("days_past_due", pd.Series([0] * n_loans))
    delinquency_30 = (dpd >= 30).mean()
    delinquency_60 = (dpd >= 60).mean()
    delinquency_90 = (dpd >= 90).mean()

    # Recovery Rate
    if "recovery_amount" in portfolio.columns and "ead" in portfolio.columns:
        defaulted_loans = portfolio[portfolio.get("is_defaulted", False)]
        if len(defaulted_loans) > 0 and defaulted_loans["ead"].sum() > 0:
            recovery_rate = defaulted_loans["recovery_amount"].sum() / defaulted_loans["ead"].sum()
        else:
            recovery_rate = 0.45  # industry average fallback
    else:
        recovery_rate = 0.45

    # Write-off Rate
    written_off = portfolio[portfolio.get("is_written_off", False)]
    write_off_rate = written_off["outstanding_balance"].sum() / total_loans if total_loans > 0 else 0

    # Restructuring Rate
    restructured = portfolio[portfolio.get("is_restructured", False)]
    restructuring_rate = len(restructured) / n_loans if n_loans > 0 else 0

    # PD (average portfolio PD)
    if "probability_of_default" in portfolio.columns:
        avg_pd = portfolio["probability_of_default"].mean()
        weighted_pd = (portfolio["probability_of_default"] * portfolio["ead"]).sum() / total_ead if total_ead > 0 else 0
    else:
        avg_pd = default_rate
        weighted_pd = default_rate

    # LGD (average)
    if "loss_given_default" in portfolio.columns:
        avg_lgd = portfolio["loss_given_default"].mean()
        weighted_lgd = (portfolio["loss_given_default"] * portfolio["ead"]).sum() / total_ead if total_ead > 0 else 0
    else:
        avg_lgd = 1.0 - recovery_rate
        weighted_lgd = avg_lgd

    # ECL (Expected Credit Loss)
    if "expected_credit_loss" in portfolio.columns:
        total_ecl = portfolio["expected_credit_loss"].sum()
    else:
        total_ecl = total_ead * weighted_pd * weighted_lgd

    # Unexpected Loss (UL) — simple 99.9% VaR approximation
    if "unexpected_loss" in portfolio.columns:
        total_ul = portfolio["unexpected_loss"].sum()
    else:
        # UL ≈ ECL * sqrt(n) * conservative factor for diversification
        pd_std = portfolio["probability_of_default"].std() if "probability_of_default" in portfolio.columns else 0.02
        total_ul = total_ecl * 3.0  # conservative multiplier for 99.9% CI

    # PD distribution by grade
    if "risk_grade" in portfolio.columns and "probability_of_default" in portfolio.columns:
        pd_by_grade = portfolio.groupby("risk_grade")["probability_of_default"].mean().to_dict()
    else:
        pd_by_grade = {}

    # ECL by sector
    if "sector" in portfolio.columns and "expected_credit_loss" in portfolio.columns:
        ecl_by_sector = portfolio.groupby("sector")["expected_credit_loss"].sum().to_dict()
    else:
        ecl_by_sector = {}

    return {
        "total_portfolio": total_loans,
        "total_ead": total_ead,
        "n_loans": n_loans,
        "npl_balance": npl_balance,
        "npl_ratio": npl_ratio,
        "npl_count": len(npl_loans),
        "default_rate": default_rate,
        "delinquency_30": delinquency_30,
        "delinquency_60": delinquency_60,
        "delinquency_90": delinquency_90,
        "avg_pd": avg_pd,
        "weighted_pd": weighted_pd,
        "avg_lgd": avg_lgd,
        "weighted_lgd": weighted_lgd,
        "recovery_rate": recovery_rate,
        "write_off_rate": write_off_rate,
        "restructuring_rate": restructuring_rate,
        "total_ecl": total_ecl,
        "total_ul": total_ul,
        "ecl_ratio": total_ecl / total_loans if total_loans > 0 else 0,
        "pd_by_grade": pd_by_grade,
        "ecl_by_sector": ecl_by_sector,
    }


def compute_vintage_analysis(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Group loans by origination year and compute default rates per vintage."""
    if "origination_date" not in portfolio.columns:
        return pd.DataFrame()
    df = portfolio.copy()
    df["origination_year"] = pd.to_datetime(df["origination_date"]).dt.year
    vintage = df.groupby("origination_year").agg(
        n_loans=("loan_id", "count"),
        total_balance=("outstanding_balance", "sum"),
        npl_count=("is_npl", "sum") if "is_npl" in df.columns else ("days_past_due", lambda x: (x >= 90).sum()),
        default_count=("is_defaulted", "sum") if "is_defaulted" in df.columns else ("days_past_due", lambda x: (x >= 180).sum()),
    ).reset_index()
    vintage["npl_rate"] = vintage["npl_count"] / vintage["n_loans"]
    vintage["default_rate"] = vintage["default_count"] / vintage["n_loans"]
    return vintage
