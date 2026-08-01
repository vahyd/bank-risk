"""
Capital Adequacy Risk Engine.
Computes CET1, Tier 1, Total CAR, Leverage Ratio, and Capital Buffer metrics.
"""
from config.settings import bank


def compute_capital_metrics(portfolio_metrics: dict, bank_cfg=None) -> dict:
    """Compute all capital adequacy metrics."""

    if bank_cfg is None:
        bank_cfg = bank

    core_capital = bank_cfg.core_capital
    additional_tier1 = bank_cfg.additional_tier1
    tier2 = bank_cfg.tier2_capital
    rwa = bank_cfg.risk_weighted_assets
    total_assets = bank_cfg.total_assets
    total_exposure = portfolio_metrics.get("total_ead", total_assets * 0.7)

    tier1_capital = core_capital + additional_tier1
    total_capital = tier1_capital + tier2

    # CET1 Ratio
    cet1_ratio = core_capital / rwa if rwa > 0 else 0

    # Tier 1 Ratio
    tier1_ratio = tier1_capital / rwa if rwa > 0 else 0

    # Total CAR
    car = total_capital / rwa if rwa > 0 else 0

    # Leverage Ratio
    leverage_ratio = tier1_capital / total_exposure if total_exposure > 0 else 0

    # Capital Conservation Buffer
    cc_buffer = bank_cfg.capital_conservation_buffer
    combined_buffer = cet1_ratio - bank_cfg.regulatory_min_cet1

    # Buffer headroom to regulatory minimums
    cet1_headroom = cet1_ratio - (bank_cfg.regulatory_min_cet1 + cc_buffer)
    tier1_headroom = tier1_ratio - bank_cfg.regulatory_min_tier1
    car_headroom = car - bank_cfg.regulatory_min_car

    # RWA density
    rwa_density = rwa / total_assets if total_assets > 0 else 0

    # Capital shortfall/surplus
    required_cet1 = rwa * (bank_cfg.regulatory_min_cet1 + cc_buffer)
    cet1_surplus = core_capital - required_cet1

    return {
        "core_capital": core_capital,
        "additional_tier1": additional_tier1,
        "tier1_capital": tier1_capital,
        "tier2_capital": tier2,
        "total_capital": total_capital,
        "risk_weighted_assets": rwa,
        "cet1_ratio": cet1_ratio,
        "tier1_ratio": tier1_ratio,
        "total_car": car,
        "leverage_ratio": leverage_ratio,
        "cet1_headroom": cet1_headroom,
        "tier1_headroom": tier1_headroom,
        "car_headroom": car_headroom,
        "cet1_surplus": cet1_surplus,
        "rwa_density": rwa_density,
        "regulatory_min_cet1": bank_cfg.regulatory_min_cet1,
        "regulatory_min_car": bank_cfg.regulatory_min_car,
        "capital_conservation_buffer": cc_buffer,
        "required_ccb": rwa * cc_buffer,
        "regulatory_cet1_minimum": rwa * bank_cfg.regulatory_min_cet1,
    }
