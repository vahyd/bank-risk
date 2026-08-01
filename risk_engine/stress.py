"""
Stress Testing & Scenario Analysis Engine.
Implements adverse scenarios and computes portfolio impact.
Based on market-risk-dashboard (TR-3N) crisis/scenario modules.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Scenario:
    """A stress test scenario with macro variable shocks."""
    name: str
    gdp_shock: float       # percentage point change
    rate_shock: float      # bps change
    inflation_shock: float  # percentage point change
    fx_shock: float        # percentage depreciation
    commodity_shock: float  # percentage change
    housing_shock: float    # percentage change
    unemployment_shock: float  # percentage point change


# Predefined scenarios based on the proposal
SCENARIOS: Dict[str, Scenario] = {
    "Baseline": Scenario(
        name="Baseline",
        gdp_shock=0.0, rate_shock=0.0, inflation_shock=0.0,
        fx_shock=0.0, commodity_shock=0.0, housing_shock=0.0,
        unemployment_shock=0.0,
    ),
    "Economic Recession": Scenario(
        name="Economic Recession",
        gdp_shock=-0.04, rate_shock=-1.50, inflation_shock=-0.01,
        fx_shock=0.10, commodity_shock=-0.15, housing_shock=-0.12,
        unemployment_shock=0.04,
    ),
    "Interest Rate Shock": Scenario(
        name="Interest Rate Shock",
        gdp_shock=-0.015, rate_shock=+3.00, inflation_shock=+0.02,
        fx_shock=0.05, commodity_shock=-0.05, housing_shock=-0.15,
        unemployment_shock=0.02,
    ),
    "Inflation Shock": Scenario(
        name="Inflation Shock",
        gdp_shock=-0.02, rate_shock=+2.00, inflation_shock=+0.05,
        fx_shock=0.08, commodity_shock=+0.20, housing_shock=-0.05,
        unemployment_shock=0.015,
    ),
    "Currency Crisis": Scenario(
        name="Currency Crisis",
        gdp_shock=-0.03, rate_shock=+4.00, inflation_shock=+0.04,
        fx_shock=0.30, commodity_shock=+0.10, housing_shock=-0.08,
        unemployment_shock=0.03,
    ),
    "Commodity Price Collapse": Scenario(
        name="Commodity Price Collapse",
        gdp_shock=-0.025, rate_shock=-0.50, inflation_shock=-0.02,
        fx_shock=0.15, commodity_shock=-0.40, housing_shock=-0.06,
        unemployment_shock=0.025,
    ),
    "Housing Market Crisis": Scenario(
        name="Housing Market Crisis",
        gdp_shock=-0.035, rate_shock=-1.00, inflation_shock=-0.01,
        fx_shock=0.05, commodity_shock=-0.10, housing_shock=-0.30,
        unemployment_shock=0.035,
    ),
    "Severe Combined Shock": Scenario(
        name="Severe Combined Shock",
        gdp_shock=-0.06, rate_shock=+3.50, inflation_shock=+0.06,
        fx_shock=0.25, commodity_shock=-0.25, housing_shock=-0.25,
        unemployment_shock=0.06,
    ),
}


def apply_scenario(portfolio: pd.DataFrame, scenario: Scenario,
                    base_metrics: dict) -> dict:
    """Apply a stress scenario to the portfolio and compute impact."""

    base_npl = base_metrics.get("npl_ratio", 0.03)
    base_ecl = base_metrics.get("total_ecl", 100_000_000)
    base_car = base_metrics.get("total_car", 0.14)
    total_loans = base_metrics.get("total_portfolio", 35_000_000_000)

    # NPL sensitivity factors (from empirical studies)
    gdp_npl_elasticity = -2.0      # 1% GDP decline → ~2% NPL increase
    rate_npl_elasticity = 0.08     # 100bps rate hike → ~8% NPL increase
    unemployment_elasticity = 1.5  # 1pp unemployment → ~150% NPL increase

    # Compute stressed NPL
    gdp_effect = scenario.gdp_shock * gdp_npl_elasticity * base_npl
    rate_effect = (scenario.rate_shock / 100) * rate_npl_elasticity * base_npl
    unemp_effect = scenario.unemployment_shock * unemployment_elasticity * base_npl
    housing_effect = scenario.housing_shock * 0.3 * base_npl  # housing has ~0.3 elasticity

    npl_change = gdp_effect + rate_effect + unemp_effect + housing_effect
    stressed_npl = max(base_npl + npl_change, 0.005)

    # Stressed ECL (roughly proportional to NPL increase)
    npl_multiplier = stressed_npl / base_npl if base_npl > 0 else 1.0
    stressed_ecl = base_ecl * npl_multiplier * 1.2  # 1.2x buffer for LGD worsening
    ecl_impact = stressed_ecl - base_ecl

    # Stressed CAR
    # ECL impact directly reduces capital
    capital_impact_ecl = ecl_impact
    capital_impact_other = total_loans * abs(scenario.housing_shock) * 0.05  # collateral erosion

    # RWA increase from rating migrations
    rwa_increase_pct = abs(scenario.gdp_shock) * 3.0 + scenario.unemployment_shock * 2.0
    stressed_rwa_multiplier = 1 + rwa_increase_pct

    # New CAR estimate
    total_equity = 5_000_000_000  # from bank config
    original_rwa = 30_000_000_000
    stressed_equity = total_equity - capital_impact_ecl - capital_impact_other
    stressed_rwa = original_rwa * stressed_rwa_multiplier
    stressed_car = stressed_equity / stressed_rwa if stressed_rwa > 0 else 0

    # Capital shortfall
    regulatory_min_car = 0.08
    capital_shortfall = max(0, stressed_rwa * regulatory_min_car - stressed_equity)

    return {
        "scenario": scenario.name,
        "stressed_npl_ratio": stressed_npl,
        "npl_increase_bps": (stressed_npl - base_npl) * 10000,
        "stressed_ecl": stressed_ecl,
        "ecl_impact": ecl_impact,
        "stressed_car": stressed_car,
        "car_impact_bps": (stressed_car - base_car) * 10000 if base_car else 0,
        "capital_shortfall": capital_shortfall,
        "capital_impact_total": capital_impact_ecl + capital_impact_other,
        "rwa_multiplier": stressed_rwa_multiplier,
    }


def run_all_scenarios(portfolio: pd.DataFrame, base_metrics: dict) -> pd.DataFrame:
    """Run all predefined scenarios and return comparison table."""
    results = []
    for name, scenario in SCENARIOS.items():
        result = apply_scenario(portfolio, scenario, base_metrics)
        results.append(result)
    return pd.DataFrame(results)


def compute_reverse_stress_test(portfolio: pd.DataFrame, base_metrics: dict) -> dict:
    """Find the shock magnitude that would deplete capital below regulatory minimum."""
    base_car = base_metrics.get("total_car", 0.14)
    regulatory_min = 0.08
    car_buffer = base_car - regulatory_min

    # NPL that would cause CAR to drop to regulatory minimum
    total_loans = base_metrics.get("total_portfolio", 35_000_000_000)
    total_equity = 5_000_000_000
    rwa = 30_000_000_000

    # Each 1% NPL increase roughly consumes equity by total_loans * lgd * ead_ratio
    avg_lgd = base_metrics.get("weighted_lgd", 0.55)
    ead_ratio = base_metrics.get("total_ead", total_loans) / total_loans if total_loans > 0 else 1.0
    equity_consumed_per_npl = total_loans * 0.01 * avg_lgd * ead_ratio

    car_decline_needed = car_buffer
    equity_needed_decline = car_decline_needed * rwa
    npl_increase_needed = equity_needed_decline / equity_consumed_per_npl if equity_consumed_per_npl > 0 else float("inf")

    # GDP decline needed to cause that NPL increase
    gdp_decline_needed = npl_increase_needed / 2.0  # using elasticity of ~2

    return {
        "break_npl_ratio": base_metrics.get("npl_ratio", 0.03) + npl_increase_needed,
        "break_gdp_decline": gdp_decline_needed,
        "break_unemployment": gdp_decline_needed * 0.5 + 0.05,  # rough Okun's law
        "equity_consumed_per_npl_pct": equity_consumed_per_npl,
        "current_car_buffer_bps": car_buffer * 10000,
    }
