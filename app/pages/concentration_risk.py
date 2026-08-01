"""
Portfolio Concentration Risk Dashboard Page.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.components.ui import (
    kpi_card, fmt_currency, fmt_pct, section_header, styled_dataframe,
)
from data.loader import load_loan_portfolio
from risk_engine.concentration import (
    compute_concentration_metrics, compute_concentration_by_sector_over_time
)


def show_concentration_risk():
    st.title("🎯 Portfolio Concentration Risk")
    st.caption("Single Borrower | Sector | Geographic | HHI | Diversification")

    portfolio = load_loan_portfolio()
    conc = compute_concentration_metrics(portfolio)
    sector_data = compute_concentration_by_sector_over_time(portfolio)

    # === KPI ROW ===
    section_header("Concentration Indicators")
    cols = st.columns(5)
    with cols[0]:
        kpi_card("HHI (Borrower)", f"{conc['hhi_borrower']:.4f}",
                  help_text="Herfindahl-Hirschman Index — lower = more diversified")
    with cols[1]:
        kpi_card("Single Borrower / Capital", fmt_pct(conc["single_borrower_ratio"]),
                  help_text=f"Largest: {fmt_currency(conc['largest_exposure'])}")
    with cols[2]:
        kpi_card("Top-10 Share", fmt_pct(conc["top_10_ratio"]))
    with cols[3]:
        kpi_card("HHI (Sector)", f"{conc['hhi_sector']:.4f}",
                  delta=f"Top: {conc['largest_sector']} ({fmt_pct(conc['largest_sector_share'])})")
    with cols[4]:
        kpi_card("Diversification Benefit", fmt_pct(conc["diversification_benefit"]),
                  help_text="Risk reduction vs fully concentrated portfolio")

    # === CHARTS ROW ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Exposure by Sector", "🏭")
        if len(sector_data) > 0:
            fig = px.treemap(sector_data, path=["sector"], values="exposure",
                              color="npl_ratio", color_continuous_scale="RdYlGn_r",
                              title="Portfolio Exposure & NPL by Sector")
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Top-20 Borrower Concentration", "👤")
        top20 = portfolio.groupby("borrower_id")["outstanding_balance"].sum().nlargest(20)
        fig = px.bar(x=top20.values, y=top20.index, orientation="h",
                      title="Top 20 Borrower Exposures",
                      color=top20.values, color_continuous_scale="Blues")
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # === SECOND ROW ===
    col1, col2 = st.columns(2)

    with col1:
        section_header("Geographic Concentration", "🗺️")
        if conc["region_concentration"]:
            regions = list(conc["region_concentration"].keys())
            shares = list(conc["region_concentration"].values())
            fig = go.Figure(data=[go.Pie(labels=regions, values=shares, hole=0.5)])
            fig.update_layout(title="Exposure by Region", height=350,
                               margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Concentration Risk Metrics", "📋")
        conc_table = pd.DataFrame([
            {"Metric": "Single Borrower Ratio", "Value": fmt_pct(conc["single_borrower_ratio"]),
             "Regulatory Guideline": "< 25%", "Status": "⚠️" if conc["single_borrower_ratio"] > 0.25 else "✅"},
            {"Metric": "Top-10 Exposure Ratio", "Value": fmt_pct(conc["top_10_ratio"]),
             "Regulatory Guideline": "< 50%", "Status": "⚠️" if conc["top_10_ratio"] > 0.50 else "✅"},
            {"Metric": "Related Party / Capital", "Value": fmt_pct(conc["related_party_ratio"]),
             "Regulatory Guideline": "< 20%", "Status": "⚠️" if conc["related_party_ratio"] > 0.20 else "✅"},
            {"Metric": "Largest Sector Share", "Value": fmt_pct(conc["largest_sector_share"]),
             "Regulatory Guideline": "< 30%", "Status": "⚠️" if conc["largest_sector_share"] > 0.30 else "✅"},
            {"Metric": "Diversification Benefit", "Value": fmt_pct(conc["diversification_benefit"]),
             "Regulatory Guideline": "> 50%", "Status": "⚠️" if conc["diversification_benefit"] < 0.50 else "✅"},
        ])
        styled_dataframe(conc_table, height=280)

    # === SECTOR DETAIL TABLE ===
    st.markdown("---")
    section_header("Sector Exposure Detail", "📊")
    if len(sector_data) > 0:
        display = sector_data.copy()
        display["exposure"] = display["exposure"].apply(fmt_currency)
        display["exposure_share"] = display["exposure_share"].apply(fmt_pct)
        display["npl_ratio"] = display["npl_ratio"].apply(fmt_pct)
        display.columns = ["Sector", "Exposure", "Count", "Avg PD", "NPL Balance", "Share", "NPL Ratio"]
        styled_dataframe(display, height=350)
