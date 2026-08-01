"""
Sector & Market Conditions Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.components.ui import (
    kpi_card, fmt_currency, fmt_pct, fmt_bps,
    section_header, build_line_chart,
)
from data.loader import load_market_data
from risk_engine.market import compute_market_risk_metrics


def show_sector_market():
    st.title("🌍 Sector & Market Conditions")
    st.caption("Interest Rates | Yield Curve | FX | Commodities | Sector Indicators")

    market_data = load_market_data(periods=60)
    market = compute_market_risk_metrics(market_data)
    latest = market_data.iloc[-1]
    prev = market_data.iloc[-2] if len(market_data) > 1 else latest

    # === KPI ROW 1: Interest & Credit ===
    section_header("Interest Rates & Credit Spreads")
    cols = st.columns(5)
    with cols[0]:
        kpi_card("Policy Rate", fmt_pct(market.get("policy_rate", 0)),
                  delta=fmt_bps(market.get("policy_rate_change", 0)))
    with cols[1]:
        kpi_card("10Y-2Y Spread", fmt_bps(market.get("yield_spread", 0)),
                  delta=fmt_bps(market.get("yield_spread_change", 0)),
                  color="normal" if market.get("yield_spread", 0) > 0 else "inverse")
    with cols[2]:
        kpi_card("AAA Credit Spread", fmt_bps(latest.get("credit_spread_aaa", 0)))
    with cols[3]:
        kpi_card("BBB Credit Spread", fmt_bps(latest.get("credit_spread_bbb", 0)))
    with cols[4]:
        kpi_card("HY Credit Spread", fmt_bps(latest.get("credit_spread_hy", 0)))

    # === KPI ROW 2: FX & Commodities ===
    cols = st.columns(5)
    with cols[0]:
        kpi_card("FX Rate (LCY/USD)", f"{market.get('fx_rate', 1):.4f}",
                  delta=fmt_pct(market.get("fx_rate_change", 0)))
    with cols[1]:
        kpi_card("FX Volatility", fmt_pct(market.get("fx_volatility", 0)))
    with cols[2]:
        kpi_card("Commodity Index", f"{market.get('commodity_index', 100):.1f}",
                  delta=fmt_pct(market.get("commodity_change", 0)))
    with cols[3]:
        kpi_card("Oil Price", f"${market.get('oil_price', 78):.1f}",
                  delta=fmt_pct(market.get("oil_price_change", 0)))
    with cols[4]:
        kpi_card("Housing Index", f"{market.get('housing_index', 220):.1f}",
                  delta=fmt_pct(market.get("housing_change", 0)))

    # === YIELD CURVE + CREDIT SPREADS ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Yield Curve", "📉")
        # Simulate current and 3-month-ago yield curves
        maturities = ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "20Y", "30Y"]
        policy = latest["policy_rate"]
        current_yields = [policy * (1 - 0.02 * i) + i * 0.003 for i in range(len(maturities))]
        prev_yields = [prev["policy_rate"] * (1 - 0.02 * i) + i * 0.003 for i in range(len(maturities))]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=maturities, y=current_yields, mode="lines+markers",
                                  name="Current", line=dict(color="#2c3e50", width=3)))
        fig.add_trace(go.Scatter(x=maturities, y=prev_yields, mode="lines+markers",
                                  name="3 Months Ago", line=dict(color="#bdc3c7", width=2, dash="dash")))
        fig.update_layout(title="Yield Curve Comparison", height=350,
                           margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white", yaxis_tickformat=".1%")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Credit Spreads Time Series", "📊")
        fig = go.Figure()
        for col_name, label, color in [("credit_spread_aaa", "AAA", "#27ae60"),
                                         ("credit_spread_bbb", "BBB", "#f39c12"),
                                         ("credit_spread_hy", "High Yield", "#e74c3c")]:
            if col_name in market_data.columns:
                fig.add_trace(go.Scatter(x=market_data["date"], y=market_data[col_name],
                                          mode="lines", name=label,
                                          line=dict(color=color, width=2)))
        fig.update_layout(title="Credit Spreads Over Time", height=350,
                           margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white", yaxis_tickformat=".2%")
        st.plotly_chart(fig, use_container_width=True)

    # === SECTOR INDICATORS ===
    st.markdown("---")
    section_header("Economic & Business Activity", "📊")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("PMI (Manufacturing)", f"{latest['pmi']:.1f}",
                  delta=f"{latest['pmi'] - prev['pmi']:+.1f}" if len(market_data) > 1 else None)
    with col2:
        st.metric("Consumer Confidence", f"{latest['consumer_confidence']:.1f}",
                  delta=f"{latest['consumer_confidence'] - prev['consumer_confidence']:+.1f}" if len(market_data) > 1 else None)
    with col3:
        housing_change = (latest["housing_index"] - market_data.iloc[-13]["housing_index"]) / market_data.iloc[-13]["housing_index"] if len(market_data) > 12 else 0
        st.metric("Housing YoY", f"{latest['housing_index']:.1f}",
                  delta=fmt_pct(housing_change))

    # === MARKET TIMES SERIES OVERVIEW ===
    st.markdown("---")
    section_header("12-Month Market Overview", "📅")
    recent = market_data.tail(12)
    fig = go.Figure()
    indicators = [
        ("policy_rate", "Policy Rate", "#2c3e50"),
        ("fx_rate", "FX Rate", "#e74c3c"),
        ("commodity_index", "Commodity Index", "#f39c12"),
    ]
    for col, label, color in indicators:
        if col in recent.columns:
            # Normalize for comparison
            vals = recent[col].values
            norm = vals / vals[0] * 100
            fig.add_trace(go.Scatter(x=recent["date"], y=norm,
                                      mode="lines+markers", name=label,
                                      line=dict(color=color, width=2)))
    fig.update_layout(title="Key Indicators (Indexed: 100 = 12M Ago)",
                       height=350, margin=dict(l=10, r=10, t=40, b=10),
                       template="plotly_white", yaxis_title="Index (100 = Base)")
    st.plotly_chart(fig, use_container_width=True)
