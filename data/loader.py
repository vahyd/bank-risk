"""
Data loader — loads real or synthetic data with caching via st.session_state.
When the user provides a real loan portfolio CSV, it overrides synthetic data.
"""

import os
import pandas as pd
import streamlit as st
from data.sample_generator import (
    generate_loan_portfolio,
    generate_market_data,
    generate_macro_data,
    generate_deposit_data,
)
from data.lendingclub_adapter import load_lendingclub_portfolio


def load_loan_portfolio(file_path: str = None, n_synthetic: int = 2000) -> pd.DataFrame:
    """
    Load loan portfolio data. Priority:
    0. Previously loaded data in session_state
    1. LendingClub data from sample_data/ folder
    2. File path provided by user (CSV/Excel)
    3. Auto-generated synthetic data
    """
    # Check session cache first
    if "loan_portfolio" in st.session_state and st.session_state.loan_portfolio is not None:
        return st.session_state.loan_portfolio

    # Try LendingClub data first
    df = _try_load_lendingclub()
    if df is not None:
        st.session_state.loan_portfolio = df
        return df

    # Try loading from provided file
    if file_path and os.path.exists(file_path):
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
        st.session_state.loan_portfolio = df
        return df

    # Fall back to synthetic
    df = generate_loan_portfolio(n_synthetic)
    st.session_state.loan_portfolio = df
    return df


def _try_load_lendingclub():
    """Try to load LendingClub data; returns None if unavailable."""
    try:
        df = load_lendingclub_portfolio(n_samples=50000)
        if df is not None and len(df) > 0:
            return df
    except Exception:
        pass
    return None


def load_market_data(periods: int = 60) -> pd.DataFrame:
    """Load or generate market data."""
    if "market_data" in st.session_state and st.session_state.market_data is not None:
        return st.session_state.market_data
    df = generate_market_data(periods)
    st.session_state.market_data = df
    return df


def load_macro_data(periods: int = 24) -> pd.DataFrame:
    """Load or generate macroeconomic data."""
    if "macro_data" in st.session_state and st.session_state.macro_data is not None:
        return st.session_state.macro_data
    df = generate_macro_data(periods)
    st.session_state.macro_data = df
    return df


def load_deposit_data(n_depositors: int = 500) -> pd.DataFrame:
    """Load or generate deposit data."""
    if "deposit_data" in st.session_state and st.session_state.deposit_data is not None:
        return st.session_state.deposit_data
    df = generate_deposit_data(n_depositors)
    st.session_state.deposit_data = df
    return df


def upload_portfolio_file() -> pd.DataFrame:
    """Streamlit file uploader for user-provided loan portfolio."""
    uploaded = st.file_uploader(
        "Upload Loan Portfolio (CSV/Excel)",
        type=["csv", "xlsx", "xls"],
        help="Upload your real loan portfolio data. Expected columns: "
             "loan_id, outstanding_balance, risk_grade, sector, region, "
             "days_past_due, collateral_value, etc."
    )
    if uploaded is not None:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        st.session_state.loan_portfolio = df
        st.success(f"Loaded {len(df):,} loans from {uploaded.name}")
        return df
    return None
