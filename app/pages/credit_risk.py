"""
Credit Portfolio Risk Dashboard Page.
PD, EAD, LGD, ECL, NPL, delinquency, recovery, vintage analysis.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.components.ui import (
    kpi_row, kpi_card, fmt_currency, fmt_pct, fmt_bps, severity_color,
    build_bar_chart, build_line_chart, build_pie_chart,
    section_header, styled_dataframe,
)
from data.loader import load_loan_portfolio
from risk_engine.credit import compute_credit_metrics, compute_vintage_analysis


def show_credit_risk():
    """Render the Credit Portfolio Risk page."""
    st.title("💳 Credit Portfolio Risk")
    st.caption("Probability of Default | Loss Given Default | Expected Credit Loss | Asset Quality")

    portfolio = load_loan_portfolio()
    metrics = compute_credit_metrics(portfolio)
    vintage = compute_vintage_analysis(portfolio)

    # === KPI ROW 1: Core Credit Metrics ===
    section_header("Core Credit Risk Indicators")

    cols = st.columns(5)
    with cols[0]:
        kpi_card("Avg Probability of Default", fmt_pct(metrics["avg_pd"]),
                  delta=fmt_pct(metrics["weighted_pd"]), help_text="Simple avg vs EAD-weighted avg")
    with cols[1]:
        kpi_card("Avg Loss Given Default", fmt_pct(metrics["avg_lgd"]),
                  delta=fmt_pct(metrics["weighted_lgd"]), help_text="Simple avg vs EAD-weighted avg")
    with cols[2]:
        kpi_card("Total EAD", fmt_currency(metrics["total_ead"]),
                  help_text="Exposure at Default (outstanding + undrawn committed)")
    with cols[3]:
        kpi_card("Expected Credit Loss", fmt_currency(metrics["total_ecl"]),
                  delta=fmt_pct(metrics["ecl_ratio"]),
                  help_text="ECL = PD × EAD × LGD")
    with cols[4]:
        kpi_card("Unexpected Loss (99.9%)", fmt_currency(metrics["total_ul"]),
                  help_text="UL = Loss exceeding ECL in tail scenarios")

    # === KPI ROW 2: Asset Quality ===
    cols = st.columns(5)
    with cols[0]:
        kpi_card("NPL Ratio", fmt_pct(metrics["npl_ratio"]),
                  delta=f"{metrics['npl_count']} loans", color="inverse")
    with cols[1]:
        kpi_card("Default Rate", fmt_pct(metrics["default_rate"]))
    with cols[2]:
        kpi_card("Recovery Rate", fmt_pct(metrics["recovery_rate"]))
    with cols[3]:
        kpi_card("Write-off Rate", fmt_pct(metrics["write_off_rate"]))
    with cols[4]:
        kpi_card("Restructuring Rate", fmt_pct(metrics["restructuring_rate"]))

    # === DELINQUENCY FUNNEL + PD DISTRIBUTION ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Delinquency Funnel", "🔻")
        funnel_data = pd.DataFrame({
            "Stage": ["30+ DPD", "60+ DPD", "90+ DPD (NPL)", "180+ DPD", "Default"],
            "Count": [
                int(metrics["delinquency_30"] * metrics["n_loans"]),
                int(metrics["delinquency_60"] * metrics["n_loans"]),
                int(metrics["delinquency_90"] * metrics["n_loans"]),
                int(metrics["default_rate"] * metrics["n_loans"] * 0.8),
                int(metrics["default_rate"] * metrics["n_loans"] * 0.5),
            ]
        })
        fig = px.funnel(funnel_data, x="Count", y="Stage", title="Portfolio Delinquency Migration")
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("PD Distribution by Risk Grade", "📊")
        if metrics["pd_by_grade"]:
            grades = list(metrics["pd_by_grade"].keys())
            pd_vals = list(metrics["pd_by_grade"].values())
            colors_palette = px.colors.sequential.Reds_r[:len(grades)]
            fig = go.Figure(data=[go.Bar(x=grades, y=pd_vals, marker_color=colors_palette,
                                          text=[fmt_pct(v) for v in pd_vals], textposition="outside")])
            fig.update_layout(title="Avg PD by Internal Risk Grade",
                               height=350, margin=dict(l=10, r=10, t=40, b=10),
                               template="plotly_white", yaxis_tickformat=".2%")
            st.plotly_chart(fig, use_container_width=True)

    # === VINTAGE ANALYSIS + ECL BY SECTOR ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Vintage Analysis", "📅")
        if len(vintage) > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=vintage["origination_year"], y=vintage["npl_rate"],
                                  name="NPL Rate", marker_color="#e74c3c"))
            fig.add_trace(go.Scatter(x=vintage["origination_year"], y=vintage["n_loans"],
                                      name="Loan Count", yaxis="y2",
                                      line=dict(color="#3498db", width=2)))
            fig.update_layout(title="NPL Rate by Origination Year",
                               height=350, margin=dict(l=10, r=10, t=40, b=10),
                               template="plotly_white",
                               yaxis=dict(tickformat=".1%", title="NPL Rate"),
                               yaxis2=dict(overlaying="y", side="right", title="Count"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Vintage analysis requires 'origination_date' column.")

    with col2:
        section_header("ECL by Sector", "🏭")
        if metrics["ecl_by_sector"]:
            ecl_sector = pd.DataFrame({
                "Sector": list(metrics["ecl_by_sector"].keys()),
                "ECL": list(metrics["ecl_by_sector"].values()),
            }).sort_values("ECL", ascending=True)
            fig = px.bar(ecl_sector, x="ECL", y="Sector", orientation="h",
                          title="Expected Credit Loss by Industry Sector",
                          color="ECL", color_continuous_scale="Reds")
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    # === HIGH RISK WATCHLIST ===
    st.markdown("---")
    section_header("High-Risk Loan Watchlist", "🚨")
    high_risk = portfolio.nlargest(20, "probability_of_default")[
        ["loan_id", "borrower_id", "sector", "outstanding_balance",
         "probability_of_default", "loss_given_default", "expected_credit_loss",
         "days_past_due", "risk_grade"]
    ].copy()
    high_risk["probability_of_default"] = high_risk["probability_of_default"].apply(fmt_pct)
    high_risk["loss_given_default"] = high_risk["loss_given_default"].apply(fmt_pct)
    high_risk["outstanding_balance"] = high_risk["outstanding_balance"].apply(fmt_currency)
    high_risk["expected_credit_loss"] = high_risk["expected_credit_loss"].apply(fmt_currency)
    high_risk.columns = ["Loan ID", "Borrower", "Sector", "Balance", "PD", "LGD", "ECL", "DPD", "Grade"]
    styled_dataframe(high_risk, height=400)
