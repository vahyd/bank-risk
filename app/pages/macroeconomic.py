"""
Macroeconomic Risk Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.components.ui import (
    kpi_card, fmt_pct, fmt_bps, section_header, build_gauge,
)
from data.loader import load_macro_data, load_loan_portfolio
from risk_engine.macro import (
    compute_macro_metrics, compute_portfolio_macro_sensitivity
)
from risk_engine.credit import compute_credit_metrics


def show_macroeconomic():
    st.title("🏛️ Macroeconomic Risk")
    st.caption("GDP | Inflation | Unemployment | Fiscal | Sovereign | Crisis Probability")

    macro_data = load_macro_data(periods=24)
    macro = compute_macro_metrics(macro_data)
    portfolio = load_loan_portfolio()
    credit = compute_credit_metrics(portfolio)
    sensitivity = compute_portfolio_macro_sensitivity(credit, macro)

    # === KPI ROW 1 ===
    section_header("Key Macroeconomic Indicators")
    cols = st.columns(6)
    with cols[0]:
        kpi_card("GDP Growth (YoY)", fmt_pct(macro["gdp_growth"]),
                  delta=fmt_bps(macro.get("gdp_trend", 0)))
    with cols[1]:
        kpi_card("Inflation (CPI)", fmt_pct(macro["inflation_cpi"]),
                  delta=fmt_bps(macro.get("inflation_trend", 0)), color="inverse")
    with cols[2]:
        kpi_card("Unemployment", fmt_pct(macro["unemployment_rate"]),
                  delta=fmt_bps(macro.get("unemployment_trend", 0)), color="inverse")
    with cols[3]:
        kpi_card("Govt Debt / GDP", fmt_pct(macro["govt_debt_gdp"]))
    with cols[4]:
        kpi_card("Fiscal Balance / GDP", fmt_pct(macro["fiscal_balance_gdp"]))
    with cols[5]:
        cycle = macro.get("economic_cycle", "N/A")
        kpi_card("Economic Cycle", cycle)

    # === CRISIS PROBABILITY GAUGE + SENSITIVITY ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Recession Probability Model (AI)", "🤖")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=macro["crisis_probability"] * 100,
            title={"text": "Crisis Probability (Next 12 Months)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 25], "color": "#27ae60"},
                    {"range": [25, 50], "color": "#f1c40f"},
                    {"range": [50, 75], "color": "#e67e22"},
                    {"range": [75, 100], "color": "#e74c3c"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 50,
                },
            },
            number={"suffix": "%"},
        ))
        fig.update_layout(height=300, margin=dict(l=40, r=40, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Portfolio Macro Sensitivity", "📊")
        sens_data = pd.DataFrame({
            "Factor": ["GDP Growth", "Unemployment Rate"],
            "Sensitivity (β)": [f"{sensitivity['gdp_sensitivity']:.2f}",
                                 f"{sensitivity['unemployment_sensitivity']:.2f}"],
            "Impact on NPL (bps)": [f"{sensitivity['gdp_impact_bps']:.1f}",
                                      f"{sensitivity['unemployment_impact_bps']:.1f}"],
        })
        st.dataframe(sens_data, hide_index=True, use_container_width=True)

        st.markdown(f"""
        **Estimated NPL Shift from Current Macro:** {sensitivity['estimated_npl_shift']:.1f} bps  
        **Current NPL Ratio:** {fmt_pct(credit['npl_ratio'])}  
        **Stress-Adjusted NPL:** {fmt_pct(credit['npl_ratio'] + sensitivity['estimated_npl_shift'] / 10000)}
        """)

    # === MACRO TREND CHARTS ===
    st.markdown("---")
    section_header("Macroeconomic Trends", "📈")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=macro_data["date"], y=macro_data["gdp_growth_yoy"],
                                  mode="lines+markers", name="GDP Growth",
                                  line=dict(color="#27ae60", width=3)))
        fig.add_trace(go.Scatter(x=macro_data["date"], y=macro_data["inflation_cpi"],
                                  mode="lines+markers", name="CPI Inflation",
                                  line=dict(color="#e74c3c", width=3)))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(title="GDP Growth vs Inflation", height=350,
                           margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white", yaxis_tickformat=".1%",
                           hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=macro_data["date"], y=macro_data["unemployment_rate"],
                                  mode="lines+markers", name="Unemployment",
                                  line=dict(color="#e67e22", width=3)))
        fig.add_trace(go.Scatter(x=macro_data["date"], y=macro_data["govt_debt_to_gdp"],
                                  mode="lines+markers", name="Govt Debt/GDP",
                                  line=dict(color="#9b59b6", width=2), yaxis="y2"))
        fig.update_layout(title="Unemployment & Government Debt", height=350,
                           margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white",
                           yaxis=dict(tickformat=".1%", title="Unemployment"),
                           yaxis2=dict(overlaying="y", side="right",
                                       tickformat=".0%", title="Debt/GDP"),
                           hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # === MACRO DATA TABLE ===
    st.markdown("---")
    section_header("Quarterly Macro Data", "📅")
    display = macro_data.tail(8).sort_values("date", ascending=False)
    for col in display.columns:
        if col != "date" and col in display.columns:
            if "rate" in col or "cpi" in col or "growth" in col:
                display[col] = display[col].apply(fmt_pct)
            elif "to_gdp" in col:
                display[col] = display[col].apply(lambda x: f"{x:.1%}")
    display.columns = [c.replace("_", " ").title() for c in display.columns]
    st.dataframe(display, hide_index=True, use_container_width=True, height=280)
