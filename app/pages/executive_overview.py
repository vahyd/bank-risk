"""
Executive Overview Dashboard Page.
Top-level C-suite summary of all risk dimensions.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.components.ui import (
    kpi_row, kpi_card, fmt_currency, fmt_pct, fmt_bps,
    build_bar_chart, build_line_chart, build_heatmap,
    build_gauge, section_header, styled_dataframe,
)
from data.loader import load_loan_portfolio, load_market_data, load_macro_data, load_deposit_data
from risk_engine.credit import compute_credit_metrics
from risk_engine.concentration import compute_concentration_metrics
from risk_engine.performance import compute_performance_metrics
from risk_engine.market import compute_market_risk_metrics
from risk_engine.macro import compute_macro_metrics
from risk_engine.liquidity import compute_liquidity_metrics
from risk_engine.capital import compute_capital_metrics
from risk_engine.ai_models import generate_ai_alerts, detect_anomalies


def show_executive_overview():
    """Render the Executive Overview page."""
    st.title("🏦 Enterprise Banking Risk Management")
    st.caption("AI-Enabled Executive Risk Dashboard")

    # Load all data
    portfolio = load_loan_portfolio()
    market_data = load_market_data()
    macro_data = load_macro_data()
    deposit_data = load_deposit_data()

    # Compute all metrics
    credit = compute_credit_metrics(portfolio)
    conc = compute_concentration_metrics(portfolio)
    perf = compute_performance_metrics(credit)
    market = compute_market_risk_metrics(market_data)
    macro = compute_macro_metrics(macro_data)
    liq = compute_liquidity_metrics(deposit_data)
    cap = compute_capital_metrics(credit)

    # Run anomaly detection
    portfolio_with_anomalies = detect_anomalies(portfolio)
    alerts = generate_ai_alerts(portfolio_with_anomalies)

    # === TOP KPI ROW ===
    st.markdown("---")
    section_header("Key Risk Indicators")

    cols = st.columns(6)
    with cols[0]:
        kpi_card("Expected Credit Loss", fmt_currency(credit["total_ecl"]),
                  delta=fmt_pct(credit["ecl_ratio"]), help_text="Total Expected Credit Loss (PD × EAD × LGD)")
    with cols[1]:
        kpi_card("NPL Ratio", fmt_pct(credit["npl_ratio"]),
                  delta=f"{credit['npl_count']} loans", color="inverse", help_text="Non-Performing Loans / Total Loans")
    with cols[2]:
        kpi_card("Total CAR", fmt_pct(cap["total_car"]),
                  delta=fmt_bps(cap["car_headroom"]), help_text="Total Capital Adequacy Ratio")
    with cols[3]:
        kpi_card("LCR", fmt_pct(liq["lcr"]),
                  delta=fmt_pct(liq["lcr_surplus"]), help_text="Liquidity Coverage Ratio")
    with cols[4]:
        kpi_card("RAROC", fmt_pct(perf["raroc"]),
                  delta=None, help_text="Risk-Adjusted Return on Capital")
    with cols[5]:
        critical = sum(1 for a in alerts if a["severity"] == "Critical")
        warnings = sum(1 for a in alerts if a["severity"] == "Warning")
        kpi_card("AI Alerts", f"{critical}🔴 {warnings}🟠",
                  help_text="Active AI Early Warning Signals")

    # === MIDDLE ROW: Risk Heatmap + ECL Trend ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Risk Domain Heatmap", "🔥")
        domains = ["Credit", "Concentration", "Market", "Liquidity", "Capital", "Macro"]
        metrics = ["Current", "Outlook"]
        scores = [
            [min(credit["npl_ratio"] * 20, 1), min(credit["delinquency_90"] * 10, 1)],
            [min(conc["single_borrower_ratio"] * 5, 1), min(conc["hhi_sector"] * 2, 1)],
            [abs(market.get("policy_rate_change", 0.01)) * 10, abs(market.get("fx_volatility", 0.1)) * 5],
            [max(0, 1 - liq["lcr"]), max(0, 1 - liq["nsfr"])],
            [max(0, 1 - cap["total_car"] / 0.12), max(0, 1 - cap["cet1_ratio"] / 0.07)],
            [macro.get("crisis_probability", 0.1), abs(macro.get("gdp_growth", 0.02)) * 5],
        ]
        fig = px.imshow(scores, x=metrics, y=domains,
                         color_continuous_scale="RdYlGn_r",
                         title="Risk Severity (0=Low, 1=High)",
                         text_auto=".2f", aspect="auto")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("ECL & NPL Trend (12-Month Simulation)", "📉")
        months = pd.date_range("2025-08", periods=12, freq="ME")
        ecl_base = credit["total_ecl"]
        trend_data = pd.DataFrame({
            "Month": months,
            "ECL": [ecl_base * (1 + i * 0.008) for i in range(12)],
            "NPL": [credit["npl_ratio"] * (1 + i * 0.005) for i in range(12)],
        })
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend_data["Month"], y=trend_data["ECL"],
                                  mode="lines+markers", name="ECL ($)",
                                  line=dict(color="#e74c3c", width=3)))
        fig.add_trace(go.Scatter(x=trend_data["Month"], y=trend_data["NPL"] * trend_data["ECL"],
                                  mode="lines+markers", name="NPL Exposure ($)",
                                  line=dict(color="#f39c12", width=2),
                                  yaxis="y2"))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # === BOTTOM ROW: Alerts + Top Exposures ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("AI Early Warning Alerts", "🤖")
        for alert in alerts:
            icon = {"Critical": "🔴", "Warning": "🟠", "Watch": "🟡", "Info": "🔵"}.get(alert["severity"], "⚪")
            bg = {"Critical": "#ffeaea", "Warning": "#fff4e6", "Watch": "#feffdb", "Info": "#e8f4fd"}.get(alert["severity"], "#f0f0f0")
            st.markdown(
                f'<div style="background:{bg};padding:10px;border-radius:8px;margin:4px 0;'
                f'border-left:4px solid {icon[0]};"><b>{icon} [{alert["domain"]}]</b> {alert["message"]}</div>',
                unsafe_allow_html=True
            )

    with col2:
        section_header("Top 10 Risk Exposures", "🏢")
        top10 = portfolio.nlargest(10, "outstanding_balance")[
            ["borrower_id", "sector", "outstanding_balance", "risk_grade", "probability_of_default"]
        ].copy()
        top10["outstanding_balance"] = top10["outstanding_balance"].apply(fmt_currency)
        top10["probability_of_default"] = top10["probability_of_default"].apply(fmt_pct)
        top10.columns = ["Borrower", "Sector", "Exposure", "Grade", "PD"]
        styled_dataframe(top10, height=350)

    # === REGULATORY HEADROOM TABLE ===
    st.markdown("---")
    section_header("Regulatory Capital Headroom", "🏛️")
    reg_data = pd.DataFrame([
        {"Metric": "CET1 Ratio", "Current": fmt_pct(cap["cet1_ratio"]),
         "Regulatory Min": fmt_pct(cap["regulatory_min_cet1"]),
         "Buffer": fmt_bps(cap["cet1_headroom"])},
        {"Metric": "Tier 1 Ratio", "Current": fmt_pct(cap["tier1_ratio"]),
         "Regulatory Min": fmt_pct(0.06), "Buffer": fmt_bps(cap["tier1_headroom"])},
        {"Metric": "Total CAR", "Current": fmt_pct(cap["total_car"]),
         "Regulatory Min": fmt_pct(cap["regulatory_min_car"]),
         "Buffer": fmt_bps(cap["car_headroom"])},
        {"Metric": "Leverage Ratio", "Current": fmt_pct(cap["leverage_ratio"]),
         "Regulatory Min": "3.0%", "Buffer": fmt_pct(cap["leverage_ratio"] - 0.03)},
        {"Metric": "LCR", "Current": fmt_pct(liq["lcr"]),
         "Regulatory Min": "100%", "Buffer": fmt_pct(liq["lcr_surplus"])},
        {"Metric": "NSFR", "Current": fmt_pct(liq["nsfr"]),
         "Regulatory Min": "100%", "Buffer": fmt_pct(liq["nsfr_surplus"])},
    ])
    styled_dataframe(reg_data, height=260)
