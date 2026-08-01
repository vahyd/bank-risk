"""
Liquidity & Funding Risk Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.components.ui import (
    kpi_card, fmt_currency, fmt_pct, fmt_bps,
    section_header, build_gauge, build_bar_chart,
)
from data.loader import load_deposit_data
from risk_engine.liquidity import (
    compute_liquidity_metrics, compute_maturity_ladder
)


def show_liquidity_funding():
    st.title("💧 Liquidity & Funding Risk")
    st.caption("LCR | NSFR | Liquidity Gap | Deposit Concentration | Funding Cost")

    deposit_data = load_deposit_data()
    liq = compute_liquidity_metrics(deposit_data)
    maturity = compute_maturity_ladder(deposit_data)

    # === KPI ROW ===
    section_header("Liquidity Indicators")
    cols = st.columns(5)
    with cols[0]:
        kpi_card("LCR", fmt_pct(liq["lcr"]),
                  delta=fmt_bps(liq["lcr_surplus"]),
                  help_text="Liquidity Coverage Ratio (>100% required)")
    with cols[1]:
        kpi_card("NSFR", fmt_pct(liq["nsfr"]),
                  delta=fmt_bps(liq["nsfr_surplus"]),
                  help_text="Net Stable Funding Ratio (>100% required)")
    with cols[2]:
        kpi_card("Liquidity Gap", fmt_currency(liq["liquidity_gap"]),
                  help_text="HQLA − Net Outflows (30-day)")
    with cols[3]:
        kpi_card("Deposit Concentration", fmt_pct(liq["deposit_concentration_top10"]),
                  help_text="Top 10 Deposits / Total Deposits")
    with cols[4]:
        kpi_card("Funding Cost", fmt_pct(liq["funding_cost"]))

    # === LCR GAUGE + DEPOSIT MIX ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("LCR Gauge", "📊")
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=liq["lcr"] * 100,
            delta={"reference": 100},
            title={"text": "Liquidity Coverage Ratio"},
            gauge={
                "axis": {"range": [50, 200]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [50, 100], "color": "#e74c3c"},
                    {"range": [100, 130], "color": "#f1c40f"},
                    {"range": [130, 200], "color": "#27ae60"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75, "value": 100,
                },
            },
            number={"suffix": "%"},
        ))
        fig.update_layout(height=300, margin=dict(l=40, r=40, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Deposit Segment Breakdown", "🏦")
        if liq["segment_breakdown"]:
            segments = list(liq["segment_breakdown"].keys())
            values = list(liq["segment_breakdown"].values())
            fig = go.Figure(data=[go.Pie(labels=segments, values=values, hole=0.5)])
            fig.update_layout(title="Deposits by Customer Segment",
                               height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    # === MATURITY LADDER ===
    st.markdown("---")
    section_header("Maturity Ladder (Assets vs Liabilities)", "🪜")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=maturity["bucket"], y=maturity["assets"],
                          name="Assets ($M)", marker_color="#3498db"))
    fig.add_trace(go.Bar(x=maturity["bucket"], y=maturity["liabilities"],
                          name="Liabilities ($M)", marker_color="#e74c3c"))
    fig.add_trace(go.Scatter(x=maturity["bucket"], y=maturity["cumulative_gap"],
                              mode="lines+markers", name="Cumulative Gap ($M)",
                              line=dict(color="#2c3e50", width=3), yaxis="y2"))
    fig.update_layout(title="Maturity Profile & Cumulative Gap",
                       height=400, margin=dict(l=10, r=10, t=40, b=10),
                       template="plotly_white", barmode="group",
                       yaxis=dict(title="$ Million"),
                       yaxis2=dict(overlaying="y", side="right", title="$ Million"))
    st.plotly_chart(fig, use_container_width=True)

    # === LIQUIDITY DETAIL TABLE ===
    st.markdown("---")
    section_header("Liquidity Position Detail", "📋")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Assets**")
        liq_assets = pd.DataFrame([
            {"Item": "High Quality Liquid Assets (HQLA)", "Value": fmt_currency(liq["hqla"])},
            {"Item": "Cash Buffer / Total Assets", "Value": fmt_pct(liq["cash_buffer_ratio"])},
            {"Item": "Stable Deposit Ratio", "Value": fmt_pct(liq["stable_deposit_ratio"])},
        ])
        st.dataframe(liq_assets, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("**Liabilities & Ratios**")
        liq_liab = pd.DataFrame([
            {"Item": "Net Cash Outflows (30-Day)", "Value": fmt_currency(liq["net_outflows_30d"])},
            {"Item": "Total Deposits", "Value": fmt_currency(liq["total_deposits"])},
            {"Item": "LCR Surplus/(Deficit)", "Value": fmt_pct(liq["lcr_surplus"])},
            {"Item": "NSFR Surplus/(Deficit)", "Value": fmt_pct(liq["nsfr_surplus"])},
        ])
        st.dataframe(liq_liab, hide_index=True, use_container_width=True)

    # === DEPOSIT CONCENTRATION (TOP 10) ===
    st.markdown("---")
    section_header("Top 10 Deposit Concentration", "📊")
    top_depositors = deposit_data.nlargest(10, "balance")[
        ["depositor_id", "segment", "balance", "monthly_withdrawal_rate"]
    ].copy()
    top_depositors["balance"] = top_depositors["balance"].apply(fmt_currency)
    top_depositors["monthly_withdrawal_rate"] = top_depositors["monthly_withdrawal_rate"].apply(fmt_pct)
    top_depositors.columns = ["Depositor", "Segment", "Balance", "Withdrawal Rate"]
    st.dataframe(top_depositors, hide_index=True, use_container_width=True, height=350)
