"""
Enterprise Banking Risk Management Dashboard
Main entry point with st.navigation sidebar.
"""
import streamlit as st

# Page configuration - MUST be the first Streamlit call
st.set_page_config(
    page_title="Enterprise Bank Risk Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
from data.lendingclub_adapter import load_lendingclub_portfolio
from data.sample_generator import (
    generate_loan_portfolio,
    generate_market_data,
    generate_macro_data,
    generate_deposit_data,
)

# Import page renderers
from app.pages.executive_overview import show_executive_overview
from app.pages.credit_risk import show_credit_risk
from app.pages.concentration_risk import show_concentration_risk
from app.pages.risk_adjusted_performance import show_risk_adjusted_performance
from app.pages.sector_market import show_sector_market
from app.pages.macroeconomic import show_macroeconomic
from app.pages.liquidity_funding import show_liquidity_funding
from app.pages.capital_adequacy import show_capital_adequacy
from app.pages.stress_testing import show_stress_testing
from app.pages.ai_early_warning import show_ai_early_warning


def _load_portfolio():
    """Load portfolio: LendingClub data first, synthetic fallback."""
    try:
        df = load_lendingclub_portfolio(n_samples=50000)
        if df is not None and len(df) > 0:
            return df
    except Exception:
        pass
    return generate_loan_portfolio(2000)


def init_session_state():
    """Initialize session state with real data if available, else synthetic."""
    if "initialized" not in st.session_state:
        with st.spinner("Loading loan portfolio..."):
            st.session_state.loan_portfolio = _load_portfolio()
            st.session_state.market_data = generate_market_data(60)
            st.session_state.macro_data = generate_macro_data(24)
            st.session_state.deposit_data = generate_deposit_data(500)
            st.session_state.initialized = True


def main():
    """Main application entry point."""
    init_session_state()

    # Build navigation
    nav = st.navigation({
        "DASHBOARD": [
            st.Page(show_executive_overview, title="Executive Overview", icon="🏦"),
            st.Page(show_credit_risk, title="Credit Portfolio Risk", icon="💳"),
            st.Page(show_concentration_risk, title="Portfolio Concentration", icon="🎯"),
            st.Page(show_risk_adjusted_performance, title="Risk-Adjusted Performance", icon="📈"),
            st.Page(show_sector_market, title="Sector & Market Conditions", icon="🌍"),
            st.Page(show_macroeconomic, title="Macroeconomic Risk", icon="📉"),
            st.Page(show_liquidity_funding, title="Liquidity & Funding", icon="💧"),
            st.Page(show_capital_adequacy, title="Capital Adequacy", icon="🏛️"),
            st.Page(show_stress_testing, title="Stress Testing", icon="⚡"),
            st.Page(show_ai_early_warning, title="AI Early Warning", icon="🤖"),
        ],
    })

    # --- Sidebar: data controls + info ---
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📤 Data Management")

        uploaded = st.file_uploader(
            "Upload Loan Portfolio (CSV/Excel)",
            type=["csv", "xlsx", "xls"],
            help="Upload your own loan portfolio CSV/Excel. LendingClub data is used by default.",
        )
        if uploaded is not None:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)
                st.session_state.loan_portfolio = df
                st.success(f"✅ Loaded {len(df):,} loans")
            except Exception as e:
                st.error(f"Failed to load file: {e}")

        if st.button("🔄 Reload Portfolio Data", use_container_width=True):
            st.session_state.loan_portfolio = _load_portfolio()
            st.session_state.market_data = generate_market_data(60)
            st.session_state.macro_data = generate_macro_data(24)
            st.session_state.deposit_data = generate_deposit_data(500)
            st.success("✅ Data reloaded")
            st.rerun()

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption(
            "AI-enabled enterprise banking risk management platform. "
            "Covers credit, concentration, market, macro, liquidity, "
            "capital, stress testing, and AI early warning."
        )
        n = len(st.session_state.get("loan_portfolio", []))
        st.caption(f"Portfolio: {n:,} loans | v1.0.0")

    # Render the selected page
    nav.run()


if __name__ == "__main__":
    main()
