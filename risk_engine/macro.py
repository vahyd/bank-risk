"""
Macroeconomic Risk Engine.
Computes macro risk indicators and portfolio sensitivity to economic factors.
"""
import pandas as pd
import numpy as np


def compute_macro_metrics(macro_data: pd.DataFrame) -> dict:
    """Extract latest macroeconomic indicators."""

    if macro_data is None or len(macro_data) == 0:
        return {}

    latest = macro_data.iloc[-1]

    results = {
        "gdp_growth": float(latest.get("gdp_growth_yoy", 0)),
        "inflation_cpi": float(latest.get("inflation_cpi", 0)),
        "unemployment_rate": float(latest.get("unemployment_rate", 0)),
        "govt_debt_gdp": float(latest.get("govt_debt_to_gdp", 0)),
        "fiscal_balance_gdp": float(latest.get("fiscal_balance_to_gdp", 0)),
        "industrial_production": float(latest.get("industrial_production_yoy", 0)),
        "retail_sales": float(latest.get("retail_sales_yoy", 0)),
    }

    # Trends (quarter-over-quarter changes)
    if len(macro_data) > 1:
        prev = macro_data.iloc[-2]
        results["gdp_trend"] = results["gdp_growth"] - float(prev.get("gdp_growth_yoy", 0))
        results["inflation_trend"] = results["inflation_cpi"] - float(prev.get("inflation_cpi", 0))
        results["unemployment_trend"] = results["unemployment_rate"] - float(prev.get("unemployment_rate", 0))

    # Economic cycle phase classification
    gdp = results["gdp_growth"]
    unemployment = results["unemployment_rate"]
    inflation = results["inflation_cpi"]

    if gdp > 0.025 and unemployment < 0.05:
        cycle = "Expansion"
        cycle_color = "green"
    elif gdp > 0.01:
        cycle = "Recovery"
        cycle_color = "#FFD700"
    elif gdp < -0.01:
        cycle = "Recession"
        cycle_color = "red"
    else:
        cycle = "Slowdown"
        cycle_color = "orange"

    results["economic_cycle"] = cycle
    results["cycle_color"] = cycle_color

    # Crisis probability estimation (simplified heuristic)
    crisis_score = 0
    if gdp < 0:
        crisis_score += 30
    elif gdp < 0.01:
        crisis_score += 15
    if unemployment > 0.07:
        crisis_score += 25
    elif unemployment > 0.055:
        crisis_score += 10
    if inflation > 0.05:
        crisis_score += 15
    if results["govt_debt_gdp"] > 1.0:
        crisis_score += 10
    if results["govt_debt_gdp"] > 1.2:
        crisis_score += 10

    results["crisis_probability"] = min(crisis_score, 100) / 100.0

    return results


def compute_portfolio_macro_sensitivity(portfolio_metrics: dict, macro_metrics: dict) -> dict:
    """Estimate portfolio sensitivity to macro factors."""

    npl_ratio = portfolio_metrics.get("npl_ratio", 0.02)
    gdp = macro_metrics.get("gdp_growth", 0.02)
    unemployment = macro_metrics.get("unemployment_rate", 0.05)

    # Simple beta estimates (these would come from a regression model in production)
    # NPL sensitivity to GDP: roughly -0.3 to -0.5 elasticity
    gdp_sensitivity = -0.35
    unemployment_sensitivity = 0.25

    gdp_impact_bps = gdp * gdp_sensitivity * 100
    unemployment_impact_bps = (unemployment - 0.05) * unemployment_sensitivity * 100

    return {
        "gdp_sensitivity": gdp_sensitivity,
        "unemployment_sensitivity": unemployment_sensitivity,
        "gdp_impact_bps": gdp_impact_bps,
        "unemployment_impact_bps": unemployment_impact_bps,
        "estimated_npl_shift": gdp_impact_bps + unemployment_impact_bps,
    }
