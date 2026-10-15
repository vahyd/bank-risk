"""Customer search & 360° profiles."""
from __future__ import annotations

from sqlalchemy import func, or_, select

from ..db import (
    Account,
    Alert,
    CreditFacility,
    Customer,
    Repayment,
    SessionLocal,
    Transaction,
    as_dict,
)
from ..ml.models import store


def list_customers(q: str | None = None, limit: int = 50, offset: int = 0) -> dict:
    db = SessionLocal()
    try:
        query = db.query(Customer)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Customer.legal_name.ilike(like),
                                     Customer.registration_number.ilike(like),
                                     Customer.industry.ilike(like),
                                     Customer.rm_name.ilike(like)))
        total = query.count()
        rows = query.order_by(Customer.id).offset(offset).limit(limit).all()
        items = []
        for c in rows:
            d = as_dict(c)
            d["pd"] = store.credit.get("prob_all", {}).get(c.id)
            d["segment"] = store.segmentation.get("labels", {}).get(c.id)
            d["operating_countries"] = c.operating_countries or []
            d["products"] = c.products or []
            items.append(d)
        return {"total": total, "items": items, "limit": limit, "offset": offset}
    finally:
        db.close()


def customer_profile(customer_id: int) -> dict:
    db = SessionLocal()
    try:
        c = db.get(Customer, customer_id)
        if not c:
            return {}
        profile = as_dict(c)
        profile["operating_countries"] = c.operating_countries or []
        profile["products"] = c.products or []

        accounts = [as_dict(a) for a in db.query(Account).filter(Account.customer_id == customer_id).all()]
        facilities = []
        for f in db.query(CreditFacility).filter(CreditFacility.customer_id == customer_id).all():
            fd = as_dict(f)
            fd["repayments"] = db.query(Repayment).filter(Repayment.facility_id == f.id).count()
            fd["max_days_late"] = db.query(func.max(Repayment.days_late)).filter(Repayment.facility_id == f.id).scalar() or 0
            facilities.append(fd)

        alerts = [as_dict(a) for a in db.query(Alert).filter(Alert.customer_id == customer_id).order_by(Alert.created_at.desc()).limit(10)]
        tx_summary = db.query(
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0),
            func.max(Transaction.timestamp),
        ).filter(Transaction.customer_id == customer_id).one()

        profile["accounts"] = accounts
        profile["facilities"] = facilities
        profile["alerts"] = alerts
        profile["transaction_summary"] = {
            "count": int(tx_summary[0]),
            "total_value": round(float(tx_summary[1]), 2),
            "last_activity": tx_summary[2].isoformat() if tx_summary[2] else None,
        }
        profile["pd"] = store.credit.get("prob_all", {}).get(customer_id)
        profile["segment"] = store.segmentation.get("labels", {}).get(customer_id)
        profile["segment_profile"] = next(
            (p for p in store.segmentation.get("profiles", [])
             if p["segment_id"] == profile["segment"]), None)
        return profile
    finally:
        db.close()
