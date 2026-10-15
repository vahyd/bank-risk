"""Ingestion pipeline: validation, deduplication, entity resolution, persistence.

Raw synthetic data -> cleaned/validated DataFrames -> SQLAlchemy ORM rows.
Maintains a clear separation between raw, cleaned, and engineered data.
"""
from __future__ import annotations

import os

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import (
    Account,
    CreditFacility,
    Customer,
    Repayment,
    Transaction,
    User,
)
from .generator import compute_balances, generate

RAW_DIR = os.path.join(settings.data_dir, "raw")
CLEAN_DIR = os.path.join(settings.data_dir, "cleaned")


def _save(df: pd.DataFrame, name: str, raw: bool = False) -> None:
    directory = RAW_DIR if raw else CLEAN_DIR
    os.makedirs(directory, exist_ok=True)
    df.to_csv(os.path.join(directory, f"{name}.csv"), index=False)


def _dedupe(df: pd.DataFrame, subset: str) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    if len(df) < before:
        print(f"[data] deduplicated {before - len(df)} rows on {subset}")
    return df


def _resolve_entities(customers: pd.DataFrame) -> pd.DataFrame:
    """Entity resolution: multiple legal entities share a group_id; keep group map."""
    # In this synthetic dataset entity resolution is explicit (group_id).
    # A real deployment would fuzzy-match names/registration numbers here.
    return customers


def run_pipeline(force: bool = False) -> dict[str, pd.DataFrame]:
    """Generate (or load cached) data, validate/dedupe, and return cleaned frames."""
    clean_marker = os.path.join(CLEAN_DIR, "customers.csv")
    if os.path.exists(clean_marker) and not force:
        print("[data] loading cached cleaned data")
        return {
            "customers": pd.read_csv(os.path.join(CLEAN_DIR, "customers.csv")),
            "accounts": pd.read_csv(os.path.join(CLEAN_DIR, "accounts.csv"), parse_dates=["opened_at"]),
            "facilities": pd.read_csv(os.path.join(CLEAN_DIR, "facilities.csv"), parse_dates=["start_date", "maturity_date"]),
            "transactions": pd.read_csv(os.path.join(CLEAN_DIR, "transactions.csv"), parse_dates=["timestamp"]),
            "repayments": pd.read_csv(os.path.join(CLEAN_DIR, "repayments.csv"), parse_dates=["due_date", "paid_date"]),
        }

    frames = generate()
    for name, df in frames.items():
        _save(df, name, raw=True)

    # Validation
    assert frames["customers"]["id"].is_unique
    assert frames["transactions"]["amount"].notna().all() and (frames["transactions"]["amount"] > 0).all()
    assert frames["transactions"]["direction"].isin(["debit", "credit"]).all()
    assert frames["transactions"]["fraud_label"].isin([0, 1, None]).all()
    assert frames["transactions"]["aml_label"].isin([0, 1, None]).all()

    # Deduplication + entity resolution
    frames["customers"] = _resolve_entities(_dedupe(frames["customers"], "registration_number"))
    frames["accounts"] = _dedupe(frames["accounts"], "iban")
    frames["transactions"] = _dedupe(frames["transactions"], "txn_ref")
    frames["facilities"] = _dedupe(frames["facilities"], "id")
    frames["repayments"] = _dedupe(frames["repayments"], "id")

    frames["accounts"] = compute_balances(frames["accounts"], frames["transactions"])

    for name, df in frames.items():
        _save(df, name)

    print("[data] pipeline complete "
          f"(customers={len(frames['customers'])}, transactions={len(frames['transactions'])})")
    return frames


def _row_iter(df: pd.DataFrame):
    for _, row in df.iterrows():
        out = {}
        for k, v in row.to_dict().items():
            if isinstance(v, (list, tuple)):
                out[k] = v
            elif pd.isna(v):
                out[k] = None
            else:
                out[k] = v
        yield out


def seed_db(db: Session, frames: dict[str, pd.DataFrame], force: bool = False) -> None:
    """Insert cleaned data into the database unless it already contains data."""
    existing = db.scalar(select(Customer.id).limit(1))
    if existing and not force:
        print("[data] database already seeded — skipping")
        return

    if force:
        for model in (Repayment, Transaction, CreditFacility, Account, Customer):
            db.execute(model.__table__.delete())

    for row in _row_iter(frames["customers"]):
        row["operating_countries"] = eval(row["operating_countries"]) if isinstance(row["operating_countries"], str) else row["operating_countries"]
        row["products"] = eval(row["products"]) if isinstance(row["products"], str) else row["products"]
        db.add(Customer(**row))
    db.flush()

    for row in _row_iter(frames["accounts"]):
        db.add(Account(**row))
    db.flush()

    for row in _row_iter(frames["facilities"]):
        db.add(CreditFacility(**row))
    db.flush()

    for row in _row_iter(frames["transactions"]):
        row.pop("fraud_score", None)
        row.pop("aml_score", None)
        db.add(Transaction(**row))
    db.flush()

    for row in _row_iter(frames["repayments"]):
        db.add(Repayment(**row))

    # Default users for RBAC demo
    for username, role, display in [
        ("admin", "admin", "Platform Administrator"),
        ("analyst", "analyst", "Credit Analyst"),
        ("rm", "rm", "Relationship Manager"),
        ("compliance", "compliance", "Compliance Officer"),
        ("treasury", "treasury", "Treasury Analyst"),
    ]:
        if not db.scalar(select(User.id).where(User.username == username)):
            db.add(User(username=username, role=role, display_name=display))

    db.commit()
    print("[data] database seeded")
