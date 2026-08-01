"""
Risk-Adjusted Performance Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.components.ui import (
    kpi_card, fmt_currency, fmt_pct, section_header, build_waterfall,
)
from data.loader import load_loan_portfolio
from risk_engine.credit import compute_credit_metrics
from risk_engine.performance import compute_performance_metrics


def show_risk_adjusted_performance():
    st.title("📈 Risk-Adjusted Portfolio Performance")
    st.caption("RAROC | NIM | ROA | ROE | Cost of Credit | Economic Capital")

    portfolio = load_loan_portfolio()
    credit = compute_credit_metrics(portfolio)
    perf = compute_performance_metrics(credit)

    # === KPI ROW ===
    section_header("Performance Indicators")
    cols = st.columns(5)
    with cols[0]:
        kpi_card("RAROC", fmt_pct(perf["raroc"]),
                  help_text="Risk-Adjusted Return on Capital")
    with cols[1]:
        kpi_card("Net Interest Margin", fmt_pct(perf["nim"]))
    with cols[2]:
        kpi_card("Return on Assets", fmt_pct(perf["roa"]))
    with cols[3]:
        kpi_card("Return on Equity", fmt_pct(perf["roe"]))
    with cols[4]:
        kpi_card("Cost of Credit Risk", fmt_pct(perf["cost_of_credit"]))

    # === INCOME WATERFALL ===
    st.markdown("---")
    section_header("Income Statement Waterfall", "💧")

    waterfall_names = ["Interest Income", "Interest Expense", "= Net Interest Income",
                        "Operating Cost", "= Pre-Provision Profit",
                        "Credit Losses", "= Post-Provision Profit"]
    waterfall_values = [
        perf["interest_income"],
        -perf["interest_expense"],
        perf["gross_interest_margin"],
        -perf["operating_cost"],
        perf["pre_provision_profit"],
        -perf["credit_losses"],
        perf["post_provision_profit"],
    ]
    fig = go.Figure(go.Waterfall(
        name="P&L", orientation="v",
        measure=["absolute", "relative", "total", "relative", "total",
                 "relative", "total"],
        x=waterfall_names, y=[v / 1e6 for v in waterfall_values],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        increasing={"marker": {"color": "#27ae60"}},
        totals={"marker": {"color": "darkblue"}},
        text=[f"${v/1e6:.1f}M" for v in waterfall_values],
    ))
    fig.update_layout(title="Income & Provision Waterfall ($M)",
                       height=400, margin=dict(l=10, r=10, t=40, b=10),
                       template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # === PERFORMANCE METRICS TABLE ===
    st.markdown("---")
    section_header("Performance Breakdown", "📊")

    col1, col2 = st.columns(2)
    with col1:
        perf_detail = pd.DataFrame([
            {"Metric": "Interest Income", "Value": fmt_currency(perf["interest_income"])},
            {"Metric": "Interest Expense", "Value": fmt_currency(perf["interest_expense"])},
            {"Metric": "Net Interest Margin (NIM)", "Value": fmt_pct(perf["nim"])},
            {"Metric": "Operating Cost", "Value": fmt_currency(perf["operating_cost"])},
            {"Metric": "Pre-Provision Profit", "Value": fmt_currency(perf["pre_provision_profit"])},
            {"Metric": "Credit Losses", "Value": fmt_currency(perf["credit_losses"])},
            {"Metric": "Post-Provision Profit", "Value": fmt_currency(perf["post_provision_profit"])},
        ])
        styled_dataframe = st.dataframe
        st.dataframe(perf_detail, hide_index=True, use_container_width=True, height=280)

    with col2:
        ratios = pd.DataFrame([
            {"Metric": "RAROC", "Value": fmt_pct(perf["raroc"]),
             "Benchmark": "> 15%"},
            {"Metric": "NIM", "Value": fmt_pct(perf["nim"]),
             "Benchmark": "> 2.5%"},
            {"Metric": "ROA", "Value": fmt_pct(perf["roa"]),
             "Benchmark": "> 1.0%"},
            {"Metric": "ROE", "Value": fmt_pct(perf["roe"]),
             "Benchmark": "> 10%"},
            {"Metric": "Cost of Credit", "Value": fmt_pct(perf["cost_of_credit"]),
             "Benchmark": "< 1.5%"},
            {"Metric": "Economic Capital Usage", "Value": fmt_pct(perf["economic_capital_usage_pct"]),
             "Benchmark": "< 100%"},
        ])
        st.dataframe(ratios, hide_index=True, use_container_width=True, height=280)

    # === ECONOMIC CAPITAL ===
    st.markdown("---")
    section_header("Economic Capital Allocation", "💰")
    cols = st.columns(3)
    with cols[0]:
        st.metric("Economic Capital", fmt_currency(perf["economic_capital"]))
    with cols[1]:
        st.metric("Total ECL", fmt_currency(credit["total_ecl"]))
    with cols[2]:
        st.metric("Risk-Adjusted Income", fmt_currency(perf["risk_adjusted_income"]))
