"""
Stress Testing & Scenario Analysis Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from app.components.ui import (
    kpi_card, fmt_currency, fmt_pct, fmt_bps,
    section_header, styled_dataframe,
)
from data.loader import load_loan_portfolio
from risk_engine.credit import compute_credit_metrics
from risk_engine.capital import compute_capital_metrics
from risk_engine.stress import (
    SCENARIOS, apply_scenario, run_all_scenarios, compute_reverse_stress_test
)


def show_stress_testing():
    st.title("⚡ Stress Testing & Scenario Analysis")
    st.caption("Adverse Scenarios | Capital Impact | ECL Projection | Reverse Stress Test")

    portfolio = load_loan_portfolio()
    credit = compute_credit_metrics(portfolio)
    cap = compute_capital_metrics(credit)

    # Combine for base metrics
    base_metrics = {**credit, **cap}

    # === SCENARIO SELECTOR ===
    st.markdown("---")
    section_header("Scenario Selection", "🎯")

    selected_scenario = st.selectbox(
        "Select Stress Scenario",
        list(SCENARIOS.keys()),
        index=0,
        help="Choose a predefined stress scenario or start with Baseline"
    )

    scenario = SCENARIOS[selected_scenario]

    # Show scenario parameters
    cols = st.columns(4)
    with cols[0]:
        st.metric("GDP Shock", f"{scenario.gdp_shock:+.1%}")
    with cols[1]:
        st.metric("Rate Shock", f"{scenario.rate_shock:+.2f}%")
    with cols[2]:
        st.metric("Unemployment Shock", f"{scenario.unemployment_shock:+.1%}")
    with cols[3]:
        st.metric("Housing Shock", f"{scenario.housing_shock:+.1%}")

    # Apply selected scenario
    result = apply_scenario(portfolio, scenario, base_metrics)

    # === SCENARIO IMPACT ===
    st.markdown("---")
    section_header(f"Impact: {selected_scenario}", "📊")

    cols = st.columns(4)
    with cols[0]:
        kpi_card("Stressed NPL Ratio", fmt_pct(result["stressed_npl_ratio"]),
                  delta=f"{result['npl_increase_bps']:+.0f} bps", color="inverse")
    with cols[1]:
        kpi_card("Stressed ECL", fmt_currency(result["stressed_ecl"]),
                  delta=fmt_currency(result["ecl_impact"]),
                  color="inverse" if result["ecl_impact"] > 0 else "normal")
    with cols[2]:
        kpi_card("Stressed CAR", fmt_pct(result["stressed_car"]),
                  delta=f"{result['car_impact_bps']:+.0f} bps")
    with cols[3]:
        shortfall = result["capital_shortfall"]
        kpi_card("Capital Shortfall", fmt_currency(shortfall),
                  color="normal" if shortfall == 0 else "inverse")

    # === ALL SCENARIOS COMPARISON ===
    st.markdown("---")
    section_header("Scenario Comparison", "📊")
    all_results = run_all_scenarios(portfolio, base_metrics)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(all_results, x="scenario", y="npl_increase_bps",
                      title="NPL Increase by Scenario (bps)",
                      color="npl_increase_bps",
                      color_continuous_scale="Reds")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white",
                           xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(all_results, x="scenario", y="car_impact_bps",
                      title="CAR Impact by Scenario (bps)",
                      color="car_impact_bps",
                      color_continuous_scale="RdBu_r")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white",
                           xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # === ECL TRAJECTORY FAN CHART ===
    st.markdown("---")
    section_header("ECL Projection by Scenario (5-Year Horizon)", "📈")

    # Simulate 5-year paths
    years = list(range(2026, 2032))
    fig = go.Figure()
    severity_colors = {
        "Baseline": "#27ae60", "Economic Recession": "#f39c12",
        "Severe Combined Shock": "#e74c3c", "Housing Market Crisis": "#e67e22",
        "Currency Crisis": "#9b59b6",
    }

    for sc_name in ["Baseline", "Economic Recession", "Housing Market Crisis",
                     "Currency Crisis", "Severe Combined Shock"]:
        sc = SCENARIOS[sc_name]
        r = apply_scenario(portfolio, sc, base_metrics)
        ecl_start = credit["total_ecl"]
        # Simulate ECL path: immediate jump then gradual mean reversion
        ecl_path = [ecl_start]
        jump = r["ecl_impact"]
        for yr in range(1, 6):
            reversion = jump * (0.8 ** yr)
            ecl_path.append(ecl_start + reversion)

        color = severity_colors.get(sc_name, "#95a5a6")
        width = 4 if sc_name == selected_scenario else 1.5
        fig.add_trace(go.Scatter(x=years, y=[e / 1e9 for e in ecl_path],
                                  mode="lines+markers", name=sc_name,
                                  line=dict(color=color, width=width)))

    fig.update_layout(title="Expected Credit Loss Trajectory ($B)",
                       height=400, margin=dict(l=10, r=10, t=40, b=10),
                       template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # === REVERSE STRESS TEST ===
    st.markdown("---")
    section_header("Reverse Stress Test — 'What Breaks the Bank?'", "🔍")
    reverse = compute_reverse_stress_test(portfolio, base_metrics)

    cols = st.columns(3)
    with cols[0]:
        st.metric("Break NPL Ratio", fmt_pct(reverse["break_npl_ratio"]))
        st.caption("NPL level at which CAR drops to regulatory minimum")
    with cols[1]:
        st.metric("Break GDP Decline", fmt_pct(reverse["break_gdp_decline"]))
        st.caption("GDP decline needed to reach break NPL")
    with cols[2]:
        st.metric("Break Unemployment", fmt_pct(reverse["break_unemployment"]))
        st.caption("Unemployment rate at which CAR reaches minimum")

    st.caption(f"Current CAR Buffer: {reverse['current_car_buffer_bps']:,.0f} bps above regulatory minimum")

    # === ALL SCENARIOS TABLE ===
    st.markdown("---")
    section_header("Detailed Scenario Results", "📋")
    display = all_results.copy()
    display["npl_increase_bps"] = display["npl_increase_bps"].apply(lambda x: f"{x:,.0f}")
    display["car_impact_bps"] = display["car_impact_bps"].apply(lambda x: f"{x:,.0f}")
    display["stressed_ecl"] = display["stressed_ecl"].apply(fmt_currency)
    display["ecl_impact"] = display["ecl_impact"].apply(fmt_currency)
    display["capital_shortfall"] = display["capital_shortfall"].apply(fmt_currency)
    display["stressed_npl_ratio"] = display["stressed_npl_ratio"].apply(fmt_pct)
    display["stressed_car"] = display["stressed_car"].apply(fmt_pct)
    display.columns = [c.replace("_", " ").title() for c in display.columns]
    st.dataframe(display, hide_index=True, use_container_width=True, height=350)
