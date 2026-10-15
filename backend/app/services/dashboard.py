"""Executive dashboard aggregations."""
from __future__ import annotations

from sqlalchemy import func, select

from ..db import Alert, CreditFacility, Customer, InvestigationCase, SessionLocal, Transaction
from ..ml.models import store


def overview() -> dict:
    db = SessionLocal()
    try:
        n_customers = db.scalar(select(func.count(Customer.id))) or 0
        tx = db.query(
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0),
        ).one()
        n_tx, total_amount = int(tx[0]), float(tx[1])

        exposure = db.scalar(select(func.coalesce(func.sum(CreditFacility.ead), 0))) or 0.0
        defaulted = db.scalar(
            select(func.count(func.distinct(CreditFacility.customer_id)))
            .where(CreditFacility.status == "Defaulted")
        ) or 0

        fraud_open = db.scalar(select(func.count(Alert.id)).where(Alert.app == "fraud", Alert.status == "Open")) or 0
        aml_open = db.scalar(select(func.count(Alert.id)).where(Alert.app == "aml", Alert.status == "Open")) or 0
        cases_open = db.scalar(select(func.count(InvestigationCase.id)).where(InvestigationCase.status != "closed")) or 0

        # segment distribution from trained model
        seg_dist: dict[str, int] = {}
        if store.segmentation.get("labels"):
            from collections import Counter
            seg_dist = Counter(store.segmentation["labels"].values())
            seg_dist = {f"Segment {k}": v for k, v in sorted(seg_dist.items())}

        high_risk = defaulted
        if store.credit.get("prob_all"):
            high_risk += sum(1 for p in store.credit["prob_all"].values() if p >= 0.15)
            high_risk = min(high_risk, n_customers)

        industries = db.execute(
            select(Customer.industry, func.count(Customer.id)).group_by(Customer.industry)
        ).all()
        industry_mix = [{"industry": i, "count": c} for i, c in industries]

        return {
            "total_customers": n_customers,
            "total_transaction_value": round(total_amount, 2),
            "total_transaction_volume": n_tx,
            "credit_exposure": round(exposure, 2),
            "high_risk_customers": int(high_risk),
            "fraud_alerts_open": int(fraud_open),
            "aml_alerts_open": int(aml_open),
            "investigation_cases_open": int(cases_open),
            "segment_distribution": seg_dist,
            "industry_mix": industry_mix,
            "models_trained_at": store.trained_at,
            "synthetic_data": True,
        }
    finally:
        db.close()


def health() -> dict:
    from ..ml.llm import ollama_available
    return {
        "status": "ok",
        "mode": "ollama" if ollama_available() else "fallback",
        "models_trained": store.trained_at is not None,
        "credit_metrics": store.credit.get("metrics", {}),
        "fraud_metrics": store.fraud.get("metrics", {}),
        "aml_metrics": store.aml.get("metrics", {}),
    }
