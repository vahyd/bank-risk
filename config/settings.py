"""
Configurable settings for the Bank Risk Dashboard.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class BankSettings:
    """Bank-level configuration."""
    bank_name: str = "Enterprise Bank"
    total_assets: float = 50_000_000_000  # $50B
    total_equity: float = 5_000_000_000   # $5B
    total_loans: float = 35_000_000_000   # $35B
    total_deposits: float = 40_000_000_000
    core_capital: float = 4_500_000_000   # CET1
    additional_tier1: float = 1_000_000_000
    tier2_capital: float = 1_500_000_000
    risk_weighted_assets: float = 30_000_000_000
    high_quality_liquid_assets: float = 8_000_000_000
    net_cash_outflows_30d: float = 6_500_000_000
    available_stable_funding: float = 38_000_000_000
    required_stable_funding: float = 32_000_000_000
    interest_income: float = 1_800_000_000
    interest_expense: float = 800_000_000
    operating_cost: float = 600_000_000
    credit_losses: float = 150_000_000
    net_income: float = 400_000_000
    regulatory_min_cet1: float = 0.045
    regulatory_min_tier1: float = 0.060
    regulatory_min_car: float = 0.080
    regulatory_min_leverage: float = 0.030
    capital_conservation_buffer: float = 0.025

@dataclass
class SectorConfig:
    """Industry sectors for portfolio classification."""
    sectors: List[str] = field(default_factory=lambda: [
        "Real Estate", "Manufacturing", "Retail & Consumer",
        "Energy & Utilities", "Technology", "Healthcare",
        "Agriculture", "Financial Services", "Construction",
        "Transportation", "Hospitality", "Education"
    ])

@dataclass
class RegionConfig:
    """Geographic regions for diversification analysis."""
    regions: List[str] = field(default_factory=lambda: [
        "North", "South", "East", "West", "Central", "Overseas"
    ])

@dataclass
class RiskRatingConfig:
    """Internal risk rating buckets."""
    grades: List[str] = field(default_factory=lambda: [
        "AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"
    ])
    grade_pd_map: dict = field(default_factory=lambda: {
        "AAA": 0.0001, "AA": 0.0003, "A": 0.0010,
        "BBB": 0.0030, "BB": 0.0100, "B": 0.0300,
        "CCC": 0.0800, "CC": 0.1500, "C": 0.3000, "D": 1.0000
    })

# Global config instances
bank = BankSettings()
sectors_cfg = SectorConfig()
regions_cfg = RegionConfig()
ratings_cfg = RiskRatingConfig()
