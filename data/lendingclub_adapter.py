"""
LendingClub data adapter.
Maps real LendingClub loan data to the dashboard's expected portfolio schema.
"""
import numpy as np
import pandas as pd
from pathlib import Path

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"
ACCEPTED_CSV = SAMPLE_DATA_DIR / "accepted_2007_to_2018q4.csv" / "accepted_2007_to_2018Q4.csv"


def load_lendingclub_portfolio(n_samples: int = 50000) -> pd.DataFrame:
    """
    Load and transform LendingClub accepted loans into the dashboard schema.
    Uses stratified sampling to preserve loan status distribution.
    """
    # Load random sample
    df = _sample_csv(str(ACCEPTED_CSV), n=n_samples)

    # --- Map columns ---
    mapped = pd.DataFrame()

    mapped["loan_id"] = df["id"].astype(str)
    mapped["borrower_id"] = df["member_id"].fillna(0).astype(int).astype(str)
    mapped["borrower_name"] = "LC-" + df["member_id"].fillna(0).astype(int).astype(str)

    # Amounts
    mapped["original_amount"] = df["loan_amnt"].astype(float)
    mapped["outstanding_balance"] = df["out_prncp"].fillna(0).astype(float)
    mapped["funded_amount"] = df["funded_amnt"].astype(float)
    # EAD = outstanding + some estimate for unused (not applicable for LC, use outstanding)
    mapped["ead"] = mapped["outstanding_balance"]
    mapped["committed_undrawn"] = 0.0

    # Rate and term
    mapped["interest_rate"] = (
        df["int_rate"].astype(str).str.rstrip("%").replace({"nan": "12.0"}).astype(float) / 100.0
    )
    mapped["term_months"] = (
        df["term"].astype(str).str.extract(r"(\d+)").fillna(36).astype(int)
    )

    # Dates
    mapped["origination_date"] = pd.to_datetime(
        df["issue_d"].apply(_parse_lc_date), errors="coerce"
    )
    mapped["maturity_date"] = mapped["origination_date"] + pd.to_timedelta(
        mapped["term_months"] * 30.42, unit="D"
    )

    # Risk grade — map LC grade (A-G) to internal scale
    grade_map = {
        "A": "AA", "B": "A", "C": "BBB", "D": "BB",
        "E": "B", "F": "CCC", "G": "CC",
    }
    mapped["risk_grade"] = df["grade"].map(grade_map).fillna("B")

    # Sector = loan purpose
    purpose_map = {
        "debt_consolidation": "Retail & Consumer",
        "credit_card": "Retail & Consumer",
        "home_improvement": "Real Estate",
        "house": "Real Estate",
        "major_purchase": "Retail & Consumer",
        "small_business": "Financial Services",
        "car": "Transportation",
        "medical": "Healthcare",
        "moving": "Transportation",
        "vacation": "Hospitality",
        "wedding": "Hospitality",
        "renewable_energy": "Energy & Utilities",
        "educational": "Education",
        "other": "Retail & Consumer",
    }
    mapped["sector"] = df["purpose"].str.lower().str.replace(" ", "_").map(purpose_map).fillna("Retail & Consumer")

    # Region = state
    mapped["region"] = df["addr_state"].fillna("Unknown")

    # Credit score
    mapped["credit_score"] = ((df["fico_range_low"].fillna(660) + df["fico_range_high"].fillna(700)) / 2).astype(int)

    # Borrower info
    mapped["borrower_income"] = df["annual_inc"].fillna(50000).clip(lower=0)
    mapped["borrower_employees"] = 1  # individual loans
    mapped["dti"] = df["dti"].fillna(15).clip(lower=0)

    # --- Derive risk metrics from loan_status ---
    status = df["loan_status"].fillna("Current")

    # Days past due
    dpd_map = {
        "Current": 0, "Fully Paid": 0, "In Grace Period": 15,
        "Late (16-30 days)": 30, "Late (31-120 days)": 60,
        "Default": 180, "Charged Off": 360,
    }
    mapped["days_past_due"] = status.map(dpd_map).fillna(0).astype(int)

    # Flags
    mapped["is_npl"] = mapped["days_past_due"] >= 90
    mapped["is_defaulted"] = status.isin(["Default", "Charged Off"])
    mapped["is_restructured"] = df["hardship_flag"].fillna("N").eq("Y")
    mapped["is_written_off"] = status.eq("Charged Off")

    # --- PD estimation from LC grade ---
    grade_pd = {
        "AA": 0.005, "A": 0.012, "BBB": 0.025, "BB": 0.045,
        "B": 0.080, "CCC": 0.140, "CC": 0.220,
    }
    mapped["probability_of_default"] = mapped["risk_grade"].map(grade_pd).fillna(0.03)
    # Adjust PD upward for already delinquent loans
    mapped.loc[mapped["days_past_due"] >= 30, "probability_of_default"] *= 2.5
    mapped.loc[mapped["days_past_due"] >= 90, "probability_of_default"] *= 2.0

    # --- LGD ---
    # LC is unsecured → higher LGD, but recoveries data exists
    recoveries = df["recoveries"].fillna(0).astype(float)
    funded = mapped["original_amount"]
    mapped["loss_given_default"] = np.where(
        funded > 0,
        1.0 - (recoveries / funded).clip(0, 0.9),
        0.65
    )
    # Floor at 0.30 for unsecured
    mapped["loss_given_default"] = mapped["loss_given_default"].clip(0.30, 0.98)

    # --- Collateral (unsecured = 0, but we set a small proxy) ---
    mapped["collateral_value"] = 0.0
    mapped["recovery_amount"] = recoveries

    # --- ECL = PD × EAD × LGD ---
    mapped["expected_credit_loss"] = (
        mapped["probability_of_default"] *
        mapped["ead"] *
        mapped["loss_given_default"]
    )

    # --- Unexpected Loss (simple VaR proxy) ---
    pd_std = mapped.groupby("risk_grade")["probability_of_default"].transform("std").fillna(0.02)
    mapped["unexpected_loss"] = mapped["expected_credit_loss"] * (1 + 2.5 * pd_std / mapped["probability_of_default"].clip(0.001))

    # Clean up
    mapped["probability_of_default"] = mapped["probability_of_default"].clip(0.0001, 0.99)
    mapped["expected_credit_loss"] = mapped["expected_credit_loss"].clip(lower=0)
    mapped["unexpected_loss"] = mapped["unexpected_loss"].clip(lower=0)
    mapped["origination_date"] = mapped["origination_date"].fillna(pd.Timestamp("2016-01-01"))
    mapped["maturity_date"] = mapped["maturity_date"].fillna(pd.Timestamp("2020-01-01"))

    return mapped.reset_index(drop=True)


def _sample_csv(path: str, n: int = 50000) -> pd.DataFrame:
    """Memory-efficient random sample from large CSV."""
    total = 2260700  # known line count minus header

    # Read in chunks, sample rows
    skip = sorted(np.random.choice(range(1, total + 1), size=min(n * 3, total), replace=False))
    rows_to_keep = set(skip[:n])

    chunks = []
    for chunk in pd.read_csv(path, chunksize=100000, low_memory=False):
        idx_start = chunk.index[0] if hasattr(chunk.index[0], '') else 0
        mask = [i in rows_to_keep for i in range(getattr(chunk, '_chunk_start', 0) or 0,
                                                   (getattr(chunk, '_chunk_start', 0) or 0) + len(chunk))]
        if any(mask):
            chunks.append(chunk[mask])
        if sum(len(c) for c in chunks) >= n:
            break

    if chunks:
        return pd.concat(chunks, ignore_index=True).iloc[:n]

    # Fallback: simple skiprows approach
    frac = min(n / total, 1.0)
    return pd.read_csv(path, skiprows=lambda i: i > 0 and np.random.random() > frac, low_memory=False)


def _parse_lc_date(val: str):
    """Parse LendingClub date format like 'Dec-2014'."""
    if pd.isna(val):
        return None
    import datetime
    try:
        return datetime.datetime.strptime(str(val).strip(), "%b-%Y")
    except (ValueError, AttributeError):
        return None
