"""Database engine, session, and ORM models (SQLAlchemy 2.0).

Works with SQLite (default, zero-dependency local dev) and PostgreSQL
(set DATABASE_URL=postgresql+psycopg://... in production / Docker Compose).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(200), index=True)
    registration_number: Mapped[str] = mapped_column(String(80), unique=True)
    industry: Mapped[str] = mapped_column(String(120), index=True)
    country: Mapped[str] = mapped_column(String(80), index=True)
    operating_countries: Mapped[list] = mapped_column(JSON, default=list)
    size: Mapped[str] = mapped_column(String(20))            # SME | Mid | Large
    annual_turnover: Mapped[float] = mapped_column(Float)
    employees: Mapped[int] = mapped_column(Integer)
    group_id: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)
    rm_name: Mapped[str] = mapped_column(String(120))
    products: Mapped[list] = mapped_column(JSON, default=list)
    kyc_status: Mapped[str] = mapped_column(String(40), default="Passed")
    sanctioned: Mapped[bool] = mapped_column(Boolean, default=False)
    pep: Mapped[bool] = mapped_column(Boolean, default=False)
    adverse_media: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    iban: Mapped[str] = mapped_column(String(40), unique=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    account_type: Mapped[str] = mapped_column(String(30))    # operating | deposit | loan
    opened_at: Mapped[datetime] = mapped_column(DateTime)
    balance: Mapped[float] = mapped_column(Float, default=0.0)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    txn_ref: Mapped[str] = mapped_column(String(60), unique=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    direction: Mapped[str] = mapped_column(String(10))       # debit | credit
    txn_type: Mapped[str] = mapped_column(String(40))        # wire | card | bulk | trade | fee | salary
    channel: Mapped[str] = mapped_column(String(30))         # branch | online | api | swift
    counterparty_name: Mapped[str] = mapped_column(String(200))
    counterparty_account: Mapped[str] = mapped_column(String(60))
    counterparty_country: Mapped[str] = mapped_column(String(80))
    reference: Mapped[str | None] = mapped_column(String(240), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Completed")
    fraud_label: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0 clean, 1 fraud (null = unknown)
    aml_label: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 0 clean, 1 suspicious
    fraud_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    aml_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)


class CreditFacility(Base):
    __tablename__ = "credit_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    facility_type: Mapped[str] = mapped_column(String(40))   # revolver | term | trade | overdraft
    limit_amount: Mapped[float] = mapped_column(Float)
    utilization: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    start_date: Mapped[datetime] = mapped_column(DateTime)
    maturity_date: Mapped[datetime] = mapped_column(DateTime)
    interest_spread_bps: Mapped[int] = mapped_column(Integer)
    collateral_value: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="Performing")
    pd: Mapped[float | None] = mapped_column(Float, nullable=True)
    lgd: Mapped[float | None] = mapped_column(Float, nullable=True)
    ead: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_grade: Mapped[str | None] = mapped_column(String(12), nullable=True)


class Repayment(Base):
    __tablename__ = "repayments"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("credit_facilities.id"), index=True)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    amount_due: Mapped[float] = mapped_column(Float)
    amount_paid: Mapped[float] = mapped_column(Float)
    paid_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    days_late: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------------------
# Compliance, alerts & cases
# ---------------------------------------------------------------------------

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    app: Mapped[str] = mapped_column(String(20), index=True)  # fraud | aml
    severity: Mapped[str] = mapped_column(String(12))         # low | medium | high
    status: Mapped[str] = mapped_column(String(20), default="Open")  # open | investigating | closed
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    factors: Mapped[list] = mapped_column(JSON, default=list)
    score: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    app: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="Open")  # open | investigating | sar_filed | closed
    analyst: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(60), nullable=True)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Forecasts, segments, models, governance
# ---------------------------------------------------------------------------

class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=30)
    method: Mapped[str] = mapped_column(String(40))
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    payload: Mapped[dict] = mapped_column(JSON)


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    method: Mapped[str] = mapped_column(String(20))           # kmeans | hdbscan
    segment_id: Mapped[int] = mapped_column(Integer)
    segment_label: Mapped[str] = mapped_column(String(120))


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    version: Mapped[str] = mapped_column(String(40))
    metrics: Mapped[dict] = mapped_column(JSON)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="ok")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    user: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(120))
    resource: Mapped[str] = mapped_column(String(240))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    role: Mapped[str] = mapped_column(String(40))            # admin | analyst | rm | compliance | treasury
    display_name: Mapped[str] = mapped_column(String(120))


# ---------------------------------------------------------------------------
# Engine / session
# ---------------------------------------------------------------------------

def _make_engine(url: str):
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        # ensure the SQLite file's directory exists (e.g. ./data/app.db)
        path = url.split("///", 1)[-1]
        if path and path != ":memory:":
            import os
            directory = os.path.dirname(os.path.abspath(path))
            os.makedirs(directory, exist_ok=True)
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def as_dict(obj: Base) -> dict:
    """Convert an ORM instance to a JSON-safe dict."""
    out: dict = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        out[col.name] = val
    return out


def jsonable(value):
    return json.loads(json.dumps(value, default=str))
