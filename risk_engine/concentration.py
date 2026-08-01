"""
Portfolio Concentration Risk Engine.
Computes HHI, single-borrower concentration, sector/geographic concentration,
and related-party exposure metrics.
"""
import numpy as np
import pandas as pd


def compute_concentration_metrics(portfolio: pd.DataFrame, total_capital: float = None) -> dict:
    """Compute all concentration risk metrics."""

    if total_capital is None:
        total_capital = portfolio["outstanding_balance"].sum() * 0.15  # rough estimate

    total_exposure = portfolio["outstanding_balance"].sum()

    # --- Herfindahl-Hirschman Index (HHI) by borrower ---
    borrower_exposure = portfolio.groupby("borrower_id")["outstanding_balance"].sum()
    exposure_shares = borrower_exposure / total_exposure
    hhi_borrower = (exposure_shares ** 2).sum()

    # Largest single borrower
    largest_exposure = borrower_exposure.max()
    single_borrower_ratio = largest_exposure / total_capital if total_capital > 0 else 0

    # Top-10 borrower concentration
    top_10_exposure = borrower_exposure.nlargest(10).sum()
    top_10_ratio = top_10_exposure / total_exposure if total_exposure > 0 else 0

    # Top-20 exposure share
    top_20_exposure = borrower_exposure.nlargest(20).sum()
    top_20_ratio = top_20_exposure / total_exposure if total_exposure > 0 else 0

    # --- Sector Concentration ---
    if "sector" in portfolio.columns:
        sector_exposure = portfolio.groupby("sector")["outstanding_balance"].sum()
        sector_shares = sector_exposure / total_exposure
        hhi_sector = (sector_shares ** 2).sum()
        sector_concentration = sector_shares.to_dict()
        largest_sector = sector_shares.idxmax()
        largest_sector_share = sector_shares.max()
    else:
        hhi_sector = 0
        sector_concentration = {}
        largest_sector = "N/A"
        largest_sector_share = 0

    # --- Geographic Concentration ---
    if "region" in portfolio.columns:
        region_exposure = portfolio.groupby("region")["outstanding_balance"].sum()
        region_shares = region_exposure / total_exposure
        hhi_region = (region_shares ** 2).sum()
        region_concentration = region_shares.to_dict()
    else:
        hhi_region = 0
        region_concentration = {}

    # --- Diversification Ratio ---
    # Ratio of actual portfolio risk to fully concentrated portfolio risk
    # Approx: sqrt(HHI) gives a diversification measure
    diversification_ratio = np.sqrt(hhi_borrower) if hhi_borrower > 0 else 1.0
    diversification_benefit = 1.0 - diversification_ratio

    # --- Related Party Exposure (simulated — would need actual related-party data) ---
    # Use top borrowers within same sector as proxy for related-party clusters
    if "sector" in portfolio.columns:
        top_borrowers = borrower_exposure.nlargest(5).index
        related_exposure = portfolio[portfolio["borrower_id"].isin(top_borrowers)]["outstanding_balance"].sum()
    else:
        related_exposure = top_5_exposure if (top_5_exposure := borrower_exposure.nlargest(5).sum()) else 0

    related_party_ratio = related_exposure / total_capital if total_capital > 0 else 0

    return {
        "hhi_borrower": hhi_borrower,
        "hhi_sector": hhi_sector,
        "hhi_region": hhi_region,
        "largest_exposure": largest_exposure,
        "single_borrower_ratio": single_borrower_ratio,
        "top_10_ratio": top_10_ratio,
        "top_20_ratio": top_20_ratio,
        "sector_concentration": sector_concentration,
        "largest_sector": largest_sector,
        "largest_sector_share": largest_sector_share,
        "region_concentration": region_concentration,
        "diversification_ratio": diversification_ratio,
        "diversification_benefit": diversification_benefit,
        "related_party_ratio": related_party_ratio,
        "total_capital": total_capital,
        "total_exposure": total_exposure,
    }


def compute_concentration_by_sector_over_time(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Compute sector exposure shares (useful for treemaps)."""
    if "sector" not in portfolio.columns:
        return pd.DataFrame()
    sector = portfolio.groupby("sector").agg(
        exposure=("outstanding_balance", "sum"),
        n_loans=("loan_id", "count"),
        avg_pd=("probability_of_default", "mean") if "probability_of_default" in portfolio.columns else ("outstanding_balance", lambda x: 0),
        npl_balance=("outstanding_balance", lambda x: x[portfolio.loc[x.index, "is_npl"]].sum()) if "is_npl" in portfolio.columns else ("outstanding_balance", lambda x: 0),
    ).reset_index()
    sector["exposure_share"] = sector["exposure"] / sector["exposure"].sum()
    sector["npl_ratio"] = sector["npl_balance"] / sector["exposure"]
    return sector.sort_values("exposure", ascending=False)
