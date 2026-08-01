"""
Liquidity & Funding Risk Engine.
Computes LCR, NSFR, liquidity gap, deposit concentration, and funding metrics.
"""
import numpy as np
import pandas as pd
from config.settings import bank


def compute_liquidity_metrics(deposit_data: pd.DataFrame, bank_cfg=None) -> dict:
    """Compute liquidity and funding risk metrics."""

    if bank_cfg is None:
        bank_cfg = bank

    hqla = bank_cfg.high_quality_liquid_assets
    net_outflows_30d = bank_cfg.net_cash_outflows_30d
    asf = bank_cfg.available_stable_funding
    rsf = bank_cfg.required_stable_funding
    total_assets = bank_cfg.total_assets
    total_deposits_val = bank_cfg.total_deposits
    interest_expense = bank_cfg.interest_expense

    # Liquidity Coverage Ratio (LCR)
    lcr = hqla / net_outflows_30d if net_outflows_30d > 0 else 0

    # Net Stable Funding Ratio (NSFR)
    nsfr = asf / rsf if rsf > 0 else 0

    # Cash Buffer
    cash_buffer = hqla / total_assets if total_assets > 0 else 0

    # Funding Cost
    funding_cost = interest_expense / total_deposits_val if total_deposits_val > 0 else 0

    # Deposit Concentration
    if deposit_data is not None and len(deposit_data) > 0:
        total_dep = deposit_data["balance"].sum()
        top_10_deposits = deposit_data.nlargest(10, "balance")["balance"].sum()
        deposit_concentration = top_10_deposits / total_dep if total_dep > 0 else 0

        # Segment breakdown
        if "segment" in deposit_data.columns:
            segment_breakdown = deposit_data.groupby("segment")["balance"].sum().to_dict()
        else:
            segment_breakdown = {}

        # Stable deposits (low withdrawal rate)
        if "is_stable" in deposit_data.columns:
            stable_ratio = deposit_data["is_stable"].mean()
        else:
            stable_ratio = 1.0 - deposit_data["monthly_withdrawal_rate"].mean()
    else:
        deposit_concentration = 0.25  # estimate
        segment_breakdown = {}
        stable_ratio = 0.70
        total_dep = total_deposits_val

    # Liquidity Gap (simple: assets - liabilities by maturity proxy)
    liquidity_gap = hqla - net_outflows_30d

    return {
        "lcr": lcr,
        "nsfr": nsfr,
        "liquidity_gap": liquidity_gap,
        "cash_buffer_ratio": cash_buffer,
        "deposit_concentration_top10": deposit_concentration,
        "funding_cost": funding_cost,
        "segment_breakdown": segment_breakdown,
        "stable_deposit_ratio": stable_ratio,
        "hqla": hqla,
        "net_outflows_30d": net_outflows_30d,
        "total_deposits": total_dep,
        "lcr_surplus": lcr - 1.0,
        "nsfr_surplus": nsfr - 1.0,
    }


def compute_maturity_ladder(deposit_data: pd.DataFrame) -> pd.DataFrame:
    """Construct a simplified maturity ladder (assets vs liabilities by time bucket)."""
    buckets = ["Overnight", "1-7 Days", "8-30 Days", "31-90 Days",
               "91-180 Days", "181-365 Days", "1-3 Years", "3-5 Years", "5+ Years"]

    # Simulate assets and liabilities per bucket (would come from real treasury data)
    np.random.seed(99)
    assets = np.random.lognormal(mean=10, sigma=1.5, size=len(buckets))
    liabilities = assets * np.random.uniform(0.7, 1.3, size=len(buckets))
    gaps = assets - liabilities
    cumulative_gap = np.cumsum(gaps)

    return pd.DataFrame({
        "bucket": buckets,
        "assets": np.round(assets / 1e6, 1),
        "liabilities": np.round(liabilities / 1e6, 1),
        "gap": np.round(gaps / 1e6, 1),
        "cumulative_gap": np.round(cumulative_gap / 1e6, 1),
    })
