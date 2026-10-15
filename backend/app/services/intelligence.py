"""Liquidity forecasting, RM assistant, and segmentation services."""
from __future__ import annotations

from sqlalchemy import func

from ..db import Customer, Forecast, SessionLocal, as_dict
from ..ml import liquidity as liq
from ..ml.models import store
from ..ml.rag import answer_rm_question


def forecast(customer_id: int, horizon_days: int = 30, scenario: str = "base") -> dict:
    return liq.forecast_customer(customer_id, horizon_days, scenario)


def forecast_history(customer_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(Forecast).filter(Forecast.customer_id == customer_id).order_by(Forecast.generated_at.desc()).limit(10).all()
        return [{"id": f.id, "horizon_days": f.horizon_days, "method": f.method,
                 "generated_at": f.generated_at.isoformat(), "payload": f.payload} for f in rows]
    finally:
        db.close()


def rm_chat(query: str, customer_id: int | None = None) -> dict:
    return answer_rm_question(query, customer_id)


def rm_brief(customer_id: int) -> dict:
    """Meeting brief: consolidated client summary + next best actions."""
    db = SessionLocal()
    try:
        c = db.get(Customer, customer_id)
        if not c:
            return {}
        from .customers import customer_profile
        prof = customer_profile(customer_id)
        pd_ = prof.get("pd")
        actions = []
        if pd_ is not None and pd_ >= 0.08:
            actions.append("Review credit exposure and covenant headroom")
        if prof.get("alerts"):
            actions.append(f"{len(prof['alerts'])} open risk/compliance alerts need attention")
        if prof.get("segment_profile"):
            actions.append(f"Client sits in '{prof['segment_profile']['label']}' — discuss matching products")
        actions.append("Confirm annual KYC refresh and beneficial-ownership records")
        return {
            "customer": {**prof, "facilities": None, "accounts": None, "alerts": None},
            "meeting_brief": {
                "profile": f"{c.legal_name} — {c.industry}, {c.country}, turnover {c.annual_turnover:,.0f}",
                "risk_snapshot": f"PD {pd_:.1%}" if pd_ is not None else "PD unavailable",
                "recommended_actions": actions[:5],
                "transaction_summary": prof.get("transaction_summary"),
            },
        }
    finally:
        db.close()


def segmentation_summary() -> dict:
    db = SessionLocal()
    try:
        labels = store.segmentation.get("labels", {})
        profiles = store.segmentation.get("profiles", [])
        customers = db.query(Customer).all()
        items = []
        for c in customers:
            items.append({
                "customer_id": c.id,
                "legal_name": c.legal_name,
                "industry": c.industry,
                "size": c.size,
                "segment": labels.get(c.id),
                "annual_turnover": c.annual_turnover,
            })
        return {
            "profiles": profiles,
            "customers": items,
            "metrics": store.segmentation.get("metrics", {}),
            "feature_names": store.segmentation.get("feature_names", []),
        }
    finally:
        db.close()
