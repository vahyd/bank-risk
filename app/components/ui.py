"""
Reusable UI components for the Bank Risk Dashboard.
KPI cards, chart builders, formatting utilities.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any


def kpi_card(title: str, value: Any, delta: Any = None,
             prefix: str = "", suffix: str = "",
             color: str = "inverse", help_text: str = None):
    """Render a single KPI metric card."""
    formatted_value = f"{prefix}{value}{suffix}" if not isinstance(value, str) else value

    delta_str = None
    if delta is not None:
        if isinstance(delta, (int, float)):
            delta_str = f"{delta:+.2f}"
        else:
            delta_str = str(delta)

    st.metric(
        label=title,
        value=formatted_value,
        delta=delta_str,
        delta_color=color,
        help=help_text,
    )


def kpi_row(kpis: List[Dict], cols_per_row: int = 4):
    """Render a row of KPI cards."""
    cols = st.columns(cols_per_row)
    for i, kpi in enumerate(kpis):
        with cols[i % cols_per_row]:
            kpi_card(**kpi)


def fmt_currency(value: float, decimals: int = 1) -> str:
    """Format large numbers as readable currency."""
    if abs(value) >= 1e9:
        return f"${value/1e9:,.{decimals}f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:,.{decimals}f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:,.{decimals}f}K"
    return f"${value:,.{decimals}f}"


def fmt_pct(value: float, decimals: int = 2) -> str:
    """Format as percentage string."""
    if isinstance(value, (int, float)):
        return f"{value * 100:,.{decimals}f}%"
    return str(value)


def fmt_bps(value: float) -> str:
    """Format as basis points."""
    return f"{value * 10000:,.0f} bps"


def severity_color(value: float, thresholds: List[float] = None,
                    colors: List[str] = None, invert: bool = False) -> str:
    """Return a color based on value severity thresholds."""
    if thresholds is None:
        thresholds = [0.02, 0.05, 0.10]
    if colors is None:
        colors = ["#27ae60", "#f39c12", "#e74c3c", "#c0392b"]
    if invert:
        value = -value
    for i, t in enumerate(thresholds):
        if value < t:
            return colors[i]
    return colors[-1]


def build_bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "",
                     color: str = "#1f77b4", horizontal: bool = False,
                     height: int = 400) -> go.Figure:
    """Build a bar chart."""
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h", title=title,
                      color_discrete_sequence=[color])
    else:
        fig = px.bar(df, x=x, y=y, title=title,
                      color_discrete_sequence=[color])
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=40, b=20),
                       template="plotly_white")
    return fig


def build_line_chart(df: pd.DataFrame, x: str, y: str or List[str],
                      title: str = "", height: int = 400,
                      secondary_y: List[str] = None) -> go.Figure:
    """Build a multi-line time-series chart."""
    if isinstance(y, str):
        y = [y]
    fig = go.Figure()
    for col in y:
        fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines",
                                  name=col.replace("_", " ").title()))
    fig.update_layout(title=title, height=height,
                       margin=dict(l=20, r=20, t=40, b=20),
                       template="plotly_white",
                       hovermode="x unified")
    return fig


def build_heatmap(data: pd.DataFrame, title: str = "", height: int = 400) -> go.Figure:
    """Build a heatmap."""
    fig = px.imshow(data, title=title, aspect="auto",
                     color_continuous_scale="RdYlGn_r")
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def build_pie_chart(labels: List[str], values: List[float],
                     title: str = "", height: int = 400) -> go.Figure:
    """Build a donut/pie chart."""
    fig = go.Figure(data=[go.Pie(labels=labels, values=values,
                                   hole=0.4, textinfo="label+percent")])
    fig.update_layout(title=title, height=height,
                       margin=dict(l=20, r=20, t=40, b=20),
                       template="plotly_white")
    return fig


def build_treemap(df: pd.DataFrame, path: List[str], values: str,
                   title: str = "", height: int = 450) -> go.Figure:
    """Build a treemap chart."""
    fig = px.treemap(df, path=path, values=values, title=title,
                      color=values, color_continuous_scale="Blues")
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def build_gauge(value: float, title: str, min_val: float = 0,
                 max_val: float = 1, thresholds: Dict[str, float] = None,
                 height: int = 250) -> go.Figure:
    """Build a gauge chart."""
    if thresholds is None:
        thresholds = {"green": 0.3, "yellow": 0.7, "red": 1.0}

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value * 100,
        title={"text": title},
        gauge={
            "axis": {"range": [min_val * 100, max_val * 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [min_val * 100, thresholds.get("green", 0.3) * 100],
                 "color": "#27ae60"},
                {"range": [thresholds.get("green", 0.3) * 100,
                           thresholds.get("yellow", 0.7) * 100],
                 "color": "#f1c40f"},
                {"range": [thresholds.get("yellow", 0.7) * 100,
                           max_val * 100],
                 "color": "#e74c3c"},
            ],
        },
    ))
    fig.update_layout(height=height, margin=dict(l=40, r=40, t=60, b=20))
    return fig


def build_waterfall(names: List[str], values: List[float],
                     title: str = "", height: int = 400) -> go.Figure:
    """Build a waterfall chart."""
    fig = go.Figure(go.Waterfall(
        name="", orientation="v",
        measure=["relative"] * len(values),
        x=names, y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        increasing={"marker": {"color": "#27ae60"}},
        totals={"marker": {"color": "darkblue"}},
    ))
    fig.update_layout(title=title, height=height,
                       margin=dict(l=20, r=20, t=40, b=20),
                       template="plotly_white")
    return fig


def styled_dataframe(df: pd.DataFrame, height: int = 300) -> None:
    """Display a styled dataframe with conditional formatting."""
    st.dataframe(
        df,
        height=height,
        use_container_width=True,
        hide_index=True,
    )


def section_header(title: str, icon: str = "📊"):
    """Render a styled section header."""
    st.markdown(f"### {icon} {title}")
    st.divider()
