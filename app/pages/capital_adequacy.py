"""
Capital Adequacy Risk Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.ui import (
    kpi_card, fmt_currency, fmt_pct, fmt_bps,
    section_header, build_waterfall,
)
from data.loader import load_loan_portfolio
from risk_engine.credit import compute_credit_metrics
from risk_engine.capital import compute_capital_metrics


def show_capital_adequacy():
    st.title("🏛️ Capital Adequacy Risk")
    st.caption("CET1 | Tier 1 | Total CAR | Leverage Ratio | RWA | Capital Buffer")

    portfolio = load_loan_portfolio()
    credit = compute_credit_metrics(portfolio)
    cap = compute_capital_metrics(credit)

    # === KPI ROW ===
    section_header("Capital Adequacy Indicators")
    cols = st.columns(5)
    with cols[0]:
        kpi_card("CET1 Ratio", fmt_pct(cap["cet1_ratio"]),
                  delta=fmt_bps(cap["cet1_headroom"]),
                  help_text=f"Regulatory minimum: {fmt_pct(cap['regulatory_min_cet1'])}")
    with cols[1]:
        kpi_card("Tier 1 Ratio", fmt_pct(cap["tier1_ratio"]),
                  delta=fmt_bps(cap["tier1_headroom"]))
    with cols[2]:
        kpi_card("Total CAR", fmt_pct(cap["total_car"]),
                  delta=fmt_bps(cap["car_headroom"]),
                  help_text=f"Regulatory minimum: {fmt_pct(cap['regulatory_min_car'])}")
    with cols[3]:
        kpi_card("Leverage Ratio", fmt_pct(cap["leverage_ratio"]))
    with cols[4]:
        kpi_card("RWA Density", fmt_pct(cap["rwa_density"]),
                  help_text="RWA / Total Assets")

    # === CAPITAL STACK WATERFALL + GAUGE ===
    st.markdown("---")
    col1, col2 = st.columns([1.2, 1])

    with col1:
        section_header("Capital Stack", "🏗️")
        cap_names = ["CET1 Capital", "+ AT1 Capital", "= Tier 1 Capital",
                      "+ Tier 2 Capital", "= Total Capital"]
        cap_values = [
            cap["core_capital"],
            cap["additional_tier1"],
            cap["tier1_capital"],
            cap["tier2_capital"],
            cap["total_capital"],
        ]
        fig = go.Figure(go.Waterfall(
            name="Capital", orientation="v",
            measure=["absolute", "relative", "total", "relative", "total"],
            x=cap_names,
            y=[v / 1e9 for v in cap_values],
            text=[f"${v/1e9:.2f}B" for v in cap_values],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#3498db"}},
            totals={"marker": {"color": "darkblue"}},
        ))
        fig.update_layout(title="Capital Structure ($ Billions)",
                           height=380, margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("CAR vs Regulatory Minimum", "📊")
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=cap["total_car"] * 100,
            delta={"reference": cap["regulatory_min_car"] * 100},
            title={"text": "Total Capital Adequacy Ratio"},
            gauge={
                "axis": {"range": [0, 25]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 8], "color": "#e74c3c"},
                    {"range": [8, 12], "color": "#f1c40f"},
                    {"range": [12, 25], "color": "#27ae60"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75, "value": cap["regulatory_min_car"] * 100,
                },
            },
            number={"suffix": "%"},
        ))
        fig.update_layout(height=380, margin=dict(l=40, r=40, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # === RWA COMPOSITION ===
    st.markdown("---")
    section_header("Risk-Weighted Assets Composition", "📊")
    col1, col2 = st.columns(2)

    with col1:
        # Simulated RWA breakdown
        rwa_data = pd.DataFrame({
            "Category": ["Credit Risk", "Market Risk", "Operational Risk"],
            "RWA": [cap["risk_weighted_assets"] * 0.75,
                     cap["risk_weighted_assets"] * 0.15,
                     cap["risk_weighted_assets"] * 0.10],
        })
        fig = go.Figure(data=[go.Pie(labels=rwa_data["Category"], values=rwa_data["RWA"],
                                       hole=0.5)])
        fig.update_layout(title="RWA by Risk Type", height=350,
                           margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Capital buffer analysis
        buffer_data = pd.DataFrame({
            "Component": ["CET1 Min", "Conservation Buffer", "Headroom", "Additional Buffer"],
            "Value (% of RWA)": [
                cap["regulatory_min_cet1"] * 100,
                cap["capital_conservation_buffer"] * 100,
                cap["cet1_headroom"] * 100,
                (cap["cet1_ratio"] - cap["regulatory_min_cet1"] - cap["capital_conservation_buffer"]) * 100,
            ]
        })
        fig = go.Figure(go.Bar(
            x=buffer_data["Component"], y=buffer_data["Value (% of RWA)"],
            marker_color=["#e74c3c", "#f39c12", "#27ae60", "#3498db"],
            text=[f"{v:.1f}%" for v in buffer_data["Value (% of RWA)"]],
            textposition="outside",
        ))
        fig.update_layout(title="Capital Buffer Breakdown (% of RWA)",
                           height=350, margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    # === DETAIL TABLE ===
    st.markdown("---")
    section_header("Capital Position Detail", "📋")
    cap_detail = pd.DataFrame([
        {"Item": "Core Equity Tier 1 (CET1)", "Value": fmt_currency(cap["core_capital"])},
        {"Item": "Additional Tier 1 (AT1)", "Value": fmt_currency(cap["additional_tier1"])},
        {"Item": "Tier 1 Capital", "Value": fmt_currency(cap["tier1_capital"])},
        {"Item": "Tier 2 Capital", "Value": fmt_currency(cap["tier2_capital"])},
        {"Item": "Total Capital", "Value": fmt_currency(cap["total_capital"])},
        {"Item": "Risk-Weighted Assets (RWA)", "Value": fmt_currency(cap["risk_weighted_assets"])},
        {"Item": "CET1 Surplus", "Value": fmt_currency(cap["cet1_surplus"])},
    ])
    st.dataframe(cap_detail, hide_index=True, use_container_width=True, height=280)
