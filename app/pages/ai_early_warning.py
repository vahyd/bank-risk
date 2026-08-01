"""
AI Early Warning & Forecasting Dashboard Page.
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
from risk_engine.ai_models import (
    train_default_prediction_model, predict_pd,
    detect_anomalies, compute_risk_drivers, generate_ai_alerts
)


def show_ai_early_warning():
    st.title("🤖 AI Early Warning & Forecasting")
    st.caption("ML Default Prediction | Anomaly Detection | Risk Drivers | Model Performance")

    portfolio = load_loan_portfolio()
    credit = compute_credit_metrics(portfolio)

    # Train AI model
    with st.spinner("Training AI models..."):
        model_result = train_default_prediction_model(portfolio)
        portfolio_with_anomalies = detect_anomalies(portfolio)
        risk_drivers = compute_risk_drivers(portfolio)
        alerts = generate_ai_alerts(portfolio_with_anomalies, model_result)

    # === ALERT SUMMARY ===
    section_header("AI Alert Summary", "🔔")
    critical = sum(1 for a in alerts if a["severity"] == "Critical")
    warning = sum(1 for a in alerts if a["severity"] == "Warning")
    watch = sum(1 for a in alerts if a["severity"] == "Watch")

    cols = st.columns(4)
    with cols[0]:
        st.metric("🔴 Critical", critical)
    with cols[1]:
        st.metric("🟠 Warning", warning)
    with cols[2]:
        st.metric("🟡 Watch", watch)
    with cols[3]:
        st.metric("Total Alerts", len(alerts))

    # Alert detail
    for alert in alerts:
        icon = {"Critical": "🔴", "Warning": "🟠", "Watch": "🟡", "Info": "🔵"}.get(alert["severity"], "⚪")
        bg = {"Critical": "#ffeaea", "Warning": "#fff4e6", "Watch": "#feffdb", "Info": "#e8f4fd"}.get(alert["severity"], "#f0f0f0")
        st.markdown(
            f'<div style="background:{bg};padding:8px;border-radius:6px;margin:3px 0;'
            f'border-left:4px solid {icon[0]};font-size:14px;">'
            f'<b>{icon} [{alert["domain"]}]</b> {alert["message"]}</div>',
            unsafe_allow_html=True
        )

    # === MODEL PERFORMANCE ===
    st.markdown("---")
    section_header("ML Model Performance", "📊")

    if "error" not in model_result:
        cols = st.columns(5)
        with cols[0]:
            kpi_card("AUC-ROC", f"{model_result['auc']:.3f}",
                      help_text="Area under ROC curve (0.5=random, 1.0=perfect)")
        with cols[1]:
            kpi_card("Precision", f"{model_result['precision']:.3f}")
        with cols[2]:
            kpi_card("Recall", f"{model_result['recall']:.3f}")
        with cols[3]:
            kpi_card("F1 Score", f"{model_result['f1']:.3f}")
        with cols[4]:
            kpi_card("Samples", f"{model_result['n_samples']:,}",
                      delta=f"{model_result['n_features']} features")

    else:
        st.warning(model_result["error"])

    # === FEATURE IMPORTANCE + RISK DRIVERS ===
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        section_header("Feature Importance (Model)", "🎯")
        if "error" not in model_result and model_result.get("feature_importance"):
            fi_data = pd.DataFrame(
                model_result["feature_importance"],
                columns=["Feature", "Importance"]
            )
            fig = px.bar(fi_data, x="Importance", y="Feature", orientation="h",
                          title="Gradient Boosting Feature Importance",
                          color="Importance", color_continuous_scale="Blues")
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Train model with sufficient features to see importance.")

    with col2:
        section_header("Top Risk Drivers (Correlation)", "🔍")
        if risk_drivers:
            drivers_df = pd.DataFrame(
                list(risk_drivers.items()),
                columns=["Feature", "Correlation with NPL"]
            ).head(10)
            fig = px.bar(drivers_df, x="Correlation with NPL", y="Feature",
                          orientation="h", title="Top-10 NPL Correlates",
                          color="Correlation with NPL",
                          color_continuous_scale="Reds")
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need 'is_npl' column to compute risk drivers.")

    # === ANOMALY DETECTION ===
    st.markdown("---")
    section_header("Anomaly Detection (Isolation Forest)", "🕵️")

    n_anomalies = portfolio_with_anomalies["is_anomaly"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Anomalous Loans", n_anomalies)
    with col2:
        st.metric("Anomaly Rate", fmt_pct(n_anomalies / len(portfolio)))
    with col3:
        avg_ecl_anomaly = portfolio_with_anomalies[portfolio_with_anomalies["is_anomaly"]]["expected_credit_loss"].mean() if n_anomalies > 0 else 0
        avg_ecl_normal = portfolio_with_anomalies[~portfolio_with_anomalies["is_anomaly"]]["expected_credit_loss"].mean()
        st.metric("Avg ECL (Anomalous)", fmt_currency(avg_ecl_anomaly),
                  delta=f"vs {fmt_currency(avg_ecl_normal)} normal")

    # Anomaly scatter
    if "probability_of_default" in portfolio_with_anomalies.columns and "outstanding_balance" in portfolio_with_anomalies.columns:
        fig = px.scatter(
            portfolio_with_anomalies,
            x="outstanding_balance",
            y="probability_of_default",
            color="is_anomaly",
            color_discrete_map={True: "#e74c3c", False: "#bdc3c7"},
            title="Loan Anomaly Detection (PD vs Balance)",
            hover_data=["sector", "risk_grade"],
            log_x=True,
            opacity=0.6,
        )
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10),
                           template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    # === PD PREDICTION DISTRIBUTION ===
    st.markdown("---")
    section_header("AI-Predicted Default Probability Distribution", "📊")

    if "error" not in model_result:
        predicted_pd = predict_pd(model_result, portfolio)
        portfolio["ai_predicted_pd"] = predicted_pd

        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(portfolio, x="ai_predicted_pd", nbins=50,
                                title="AI PD Distribution",
                                color_discrete_sequence=["#3498db"])
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10),
                               template="plotly_white", xaxis_tickformat=".1%")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            comparison = pd.DataFrame({
                "Risk Grade": portfolio["risk_grade"].unique(),
                "Original PD": [portfolio[portfolio["risk_grade"] == g]["probability_of_default"].mean()
                                 for g in portfolio["risk_grade"].unique()],
                "AI Predicted PD": [portfolio[portfolio["risk_grade"] == g]["ai_predicted_pd"].mean()
                                     for g in portfolio["risk_grade"].unique()],
            })
            fig = go.Figure()
            fig.add_trace(go.Bar(x=comparison["Risk Grade"], y=comparison["Original PD"],
                                  name="Original PD", marker_color="#bdc3c7"))
            fig.add_trace(go.Bar(x=comparison["Risk Grade"], y=comparison["AI Predicted PD"],
                                  name="AI Predicted PD", marker_color="#3498db"))
            fig.update_layout(title="Original vs AI-Predicted PD by Grade",
                               height=350, margin=dict(l=10, r=10, t=40, b=10),
                               template="plotly_white", barmode="group",
                               yaxis_tickformat=".2%")
            st.plotly_chart(fig, use_container_width=True)
