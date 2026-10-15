"""Feature engineering for all six applications.

Engineered features are computed deterministically from the cleaned data and
stored separately from raw/cleaned layers (feature layer -> predictions).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.generator import HIGH_RISK_COUNTRIES, INDUSTRIES

# ---------------------------------------------------------------------------
# Credit risk — customer-level features
# ---------------------------------------------------------------------------

def credit_features(customers: pd.DataFrame, accounts: pd.DataFrame,
                    facilities: pd.DataFrame, repayments: pd.DataFrame,
                    transactions: pd.DataFrame) -> pd.DataFrame:
    cust = customers.set_index("id")

    feat = pd.DataFrame(index=customers["id"].values)
    feat["log_turnover"] = np.log10(customers["annual_turnover"].values)
    feat["log_employees"] = np.log10(customers["employees"].clip(lower=1).values)
    feat["industry_risk"] = customers["industry"].map(lambda i: INDUSTRIES.get(i, {}).get("risk", 0.1)).values
    feat["country_risk"] = customers["country"].map(lambda c: 0.06 if c in HIGH_RISK_COUNTRIES else 0.02).values
    feat["size_ordinal"] = customers["size"].map({"SME": 0, "Mid": 1, "Large": 2}).fillna(0).values
    feat["n_products"] = customers["products"].map(len).values
    feat["sanctioned"] = customers["sanctioned"].astype(int).values
    feat["pep"] = customers["pep"].astype(int).values
    feat["adverse_media"] = customers["adverse_media"].astype(int).values

    # facilities
    fac = facilities.copy()
    fac["collateral_ratio"] = fac["collateral_value"] / fac["limit_amount"].clip(lower=1)
    g = fac.groupby("customer_id").agg(
        total_limit=("limit_amount", "sum"),
        mean_utilization=("utilization", "mean"),
        max_utilization=("utilization", "max"),
        mean_collateral_ratio=("collateral_ratio", "mean"),
        n_facilities=("id", "count"),
        mean_spread=("interest_spread_bps", "mean"),
    )
    for col in g.columns:
        feat[col] = feat.index.map(g[col]).fillna(0.0)

    # repayments
    if len(repayments):
        r = repayments.merge(facilities[["id", "customer_id"]], left_on="facility_id", right_on="id", suffixes=("", "_fac"))
        rg = r.groupby("customer_id").agg(
            max_days_late=("days_late", "max"),
            mean_days_late=("days_late", "mean"),
            missed_payments=("days_late", lambda s: int((s > 30).sum())),
        )
        for col in rg.columns:
            feat[col] = feat.index.map(rg[col]).fillna(0.0)
    else:
        feat["max_days_late"] = feat["mean_days_late"] = feat["missed_payments"] = 0.0

    # transactions
    t = transactions.copy()
    t["month"] = t["timestamp"].dt.tz_localize(None).dt.to_period("M").astype(str)
    t["credit_amt"] = np.where(t["direction"] == "credit", t["amount"], 0.0)
    t["debit_amt"] = np.where(t["direction"] == "debit", t["amount"], 0.0)
    tg = t.groupby("customer_id").agg(
        n_tx=("id", "count"),
        avg_monthly_credit=("credit_amt", "sum"),
        avg_monthly_debit=("debit_amt", "sum"),
        tx_volatility=("amount", "std"),
        max_tx=("amount", "max"),
        mean_tx=("amount", "mean"),
    )
    tg["avg_monthly_credit"] /= max(t["month"].nunique(), 1)
    tg["avg_monthly_debit"] /= max(t["month"].nunique(), 1)
    tg["net_flow_ratio"] = (tg["avg_monthly_credit"] - tg["avg_monthly_debit"]) / tg["avg_monthly_credit"].clip(lower=1)
    tg["high_risk_share"] = t.assign(hr=t["counterparty_country"].isin(HIGH_RISK_COUNTRIES)).groupby("customer_id")["hr"].mean()
    for col in tg.columns:
        feat[col] = feat.index.map(tg[col]).fillna(0.0)

    # target: any facility defaulted
    defaulted = facilities.groupby("customer_id")["status"].apply(lambda s: int((s == "Defaulted").any()))
    feat["default"] = feat.index.map(defaulted).fillna(0).astype(int)

    return feat.reset_index().rename(columns={"index": "customer_id"})


# ---------------------------------------------------------------------------
# Fraud / AML — transaction-level features
# ---------------------------------------------------------------------------

def txn_features(transactions: pd.DataFrame) -> pd.DataFrame:
    """Transaction-level features shared by fraud and AML models."""
    t = transactions.copy().sort_values(["customer_id", "timestamp"])
    t["hour"] = t["timestamp"].dt.hour
    t["dayofweek"] = t["timestamp"].dt.dayofweek
    t["is_night"] = ((t["hour"] >= 22) | (t["hour"] <= 5)).astype(int)
    t["is_weekend"] = (t["dayofweek"] >= 5).astype(int)
    t["log_amount"] = np.log10(t["amount"].clip(lower=1))
    t["round_amount"] = ((t["amount"] % 1000) == 0).astype(int)
    t["high_risk_country"] = t["counterparty_country"].isin(HIGH_RISK_COUNTRIES).astype(int)
    t["internal"] = t["is_internal"].astype(int)

    # per-customer history (careful: use expanding stats to avoid leakage)
    grp = t.groupby("customer_id")
    t["mean_amount"] = grp["amount"].transform("mean")
    t["std_amount"] = grp["amount"].transform("std").replace(0, 1e-6)
    t["amount_zscore"] = (t["amount"] - t["mean_amount"]) / t["std_amount"]

    # new beneficiary: first time this counterparty appears for the customer
    t["seen_before"] = t.groupby(["customer_id", "counterparty_account"])["timestamp"].rank(method="first") > 1
    t["new_beneficiary"] = (~t["seen_before"]).astype(int)

    # velocity: count of txns in the past 3 days for the customer
    # (use a DatetimeIndex so pandas rolling("3D") works per group)
    t = t.set_index("timestamp")
    vel = t.groupby("customer_id")["amount"].rolling("3D").count().fillna(1)
    t = t.reset_index()
    vel = vel.reset_index(level=0, drop=True)
    t["txn_velocity_3d"] = vel.values
    return t


def fraud_features(transactions: pd.DataFrame) -> pd.DataFrame:
    t = txn_features(transactions)
    cols = ["log_amount", "amount_zscore", "is_night", "is_weekend", "new_beneficiary",
            "high_risk_country", "round_amount", "txn_velocity_3d"]
    return t[["id", "customer_id", "amount", "fraud_label"] + cols]


def aml_features(transactions: pd.DataFrame) -> pd.DataFrame:
    t = txn_features(transactions)
    t["near_threshold"] = ((t["amount"] >= 9_000) & (t["amount"] < 10_000)).astype(int)
    t["large_txn"] = (t["amount"] >= 100_000).astype(int)
    t["internal"] = t["is_internal"].astype(int)
    cols = ["log_amount", "amount_zscore", "near_threshold", "large_txn", "internal",
            "high_risk_country", "new_beneficiary", "txn_velocity_3d", "round_amount"]
    return t[["id", "customer_id", "amount", "aml_label"] + cols]


# ---------------------------------------------------------------------------
# Segmentation — customer-level behavioral features
# ---------------------------------------------------------------------------

def segmentation_features(customers: pd.DataFrame, transactions: pd.DataFrame,
                          facilities: pd.DataFrame) -> pd.DataFrame:
    t = transactions.copy()
    t["credit_amt"] = np.where(t["direction"] == "credit", t["amount"], 0.0)
    t["debit_amt"] = np.where(t["direction"] == "debit", t["amount"], 0.0)
    tg = t.groupby("customer_id").agg(
        tx_count=("id", "count"),
        total_credit=("credit_amt", "sum"),
        total_debit=("debit_amt", "sum"),
        avg_amount=("amount", "mean"),
        cross_border_share=("is_internal", lambda s: 1.0 - float(s.mean())),
    ).reset_index()
    fac = facilities.groupby("customer_id").agg(
        total_credit_limit=("limit_amount", "sum"),
        avg_utilization=("utilization", "mean"),
        n_facilities=("id", "count"),
    ).reset_index()

    df = customers[["id", "industry", "size", "annual_turnover", "employees"]].merge(tg, left_on="id", right_on="customer_id", how="left")
    df = df.merge(fac, left_on="id", right_on="customer_id", how="left")
    for col in ["tx_count", "total_credit", "total_debit", "avg_amount", "cross_border_share",
                "total_credit_limit", "avg_utilization", "n_facilities"]:
        df[col] = df[col].fillna(0.0)

    df["log_turnover"] = np.log10(df["annual_turnover"].clip(lower=1))
    df["log_employees"] = np.log10(df["employees"].clip(lower=1))
    df["credit_intensity"] = df["total_credit"] / df["annual_turnover"].clip(lower=1)
    df["size_ordinal"] = df["size"].map({"SME": 0, "Mid": 1, "Large": 2}).fillna(0)
    return df
