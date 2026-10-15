"""Administration: audit logs, model registry, retraining, data quality."""
from __future__ import annotations

from sqlalchemy import func, select

from ..db import AuditLog, ModelRun, SessionLocal, as_dict
from ..ml.models import store


def audit_logs(limit: int = 100) -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(AuditLog).order_by(AuditLog.ts.desc()).limit(limit).all()
        return [as_dict(a) for a in rows]
    finally:
        db.close()


def model_runs() -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(ModelRun).order_by(ModelRun.trained_at.desc()).limit(30).all()
        return [as_dict(m) for m in rows]
    finally:
        db.close()


def data_quality() -> dict:
    db = SessionLocal()
    try:
        from ..db import Account, Customer, Transaction
        n_tx = db.scalar(select(func.count(Transaction.id))) or 0
        n_null_ref = db.scalar(select(func.count(Transaction.id)).where(Transaction.reference.is_(None))) or 0
        n_null_cp = db.scalar(select(func.count(Transaction.id)).where(Transaction.counterparty_name.is_(None))) or 0
        dupes = db.scalar(select(func.count(Transaction.txn_ref))) - db.scalar(select(func.count(func.distinct(Transaction.txn_ref)))) or 0
        return {
            "transactions": int(n_tx),
            "customers": int(db.scalar(select(func.count(Customer.id))) or 0),
            "accounts": int(db.scalar(select(func.count(Account.id))) or 0),
            "missing_reference_pct": round(100 * n_null_ref / max(n_tx, 1), 2),
            "missing_counterparty_pct": round(100 * n_null_cp / max(n_tx, 1), 2),
            "duplicate_txn_refs": int(dupes),
            "models_trained": store.trained_at is not None,
        }
    finally:
        db.close()


def retrain(force: bool = False) -> dict:
    from ..data.loader import run_pipeline, seed_db
    from ..db import init_db, SessionLocal
    from ..services.risk import generate_alerts

    frames = run_pipeline(force=True)
    db = SessionLocal()
    try:
        seed_db(db, frames, force=True)
    finally:
        db.close()
    result = store.train_all(frames, force=True)
    generated = generate_alerts(clear=True)
    return {"training": result, "alerts_created": generated}
