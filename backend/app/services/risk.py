"""Credit risk, fraud detection and AML service functions."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func

from ..config import settings
from ..db import (
    Account,
    Alert,
    CreditFacility,
    Customer,
    InvestigationCase,
    Repayment,
    SessionLocal,
    Transaction,
    as_dict,
)
from ..ml.features import aml_features, fraud_features, txn_features
from ..ml.models import store

# ---------------------------------------------------------------------------
# Credit risk
# ---------------------------------------------------------------------------

def _grade(pd_: float) -> str:
    if pd_ < 0.01:
        return "AAA-A"
    if pd_ < 0.03:
        return "BBB"
    if pd_ < 0.06:
        return "BB"
    if pd_ < 0.12:
        return "B"
    if pd_ < 0.22:
        return "CCC"
    return "D"


def credit_portfolio() -> dict:
    db = SessionLocal()
    try:
        rows = []
        probs = store.credit.get("prob_all", {})
        for f in db.query(CreditFacility).all():
            cust = db.get(Customer, f.customer_id)
            pd_ = probs.get(f.customer_id)
            grade = _grade(pd_) if pd_ is not None else f.risk_grade
            rows.append({
                "facility_id": f.id,
                "customer_id": f.customer_id,
                "customer": cust.legal_name if cust else "?",
                "industry": cust.industry if cust else "?",
                "facility_type": f.facility_type,
                "limit": f.limit_amount,
                "ead": f.ead,
                "pd": pd_,
                "lgd": f.lgd,
                "expected_loss": round((pd_ or 0) * (f.lgd or 0.45) * (f.ead or 0), 2),
                "grade": grade,
                "status": f.status,
                "collateral_value": f.collateral_value,
                "interest_spread_bps": f.interest_spread_bps,
            })
        total_ead = sum(r["ead"] or 0 for r in rows)
        total_el = sum(r["expected_loss"] or 0 for r in rows)
        by_grade: dict[str, dict] = {}
        for r in rows:
            g = r["grade"]
            by_grade.setdefault(g, {"count": 0, "ead": 0.0, "el": 0.0})
            by_grade[g]["count"] += 1
            by_grade[g]["ead"] += r["ead"] or 0
            by_grade[g]["el"] += r["expected_loss"] or 0

        return {
            "items": rows,
            "summary": {
                "total_exposure": round(total_ead, 2),
                "total_expected_loss": round(total_el, 2),
                "coverage_ratio": round(total_el / total_ead, 6) if total_ead else 0,
                "n_facilities": len(rows),
            },
            "by_grade": by_grade,
            "metrics": store.credit.get("metrics", {}),
            "calibration": store.credit.get("calibration", []),
            "importances": store.credit.get("importances", []),
            "thresholds": store.credit.get("thresholds", {}),
        }
    finally:
        db.close()


def credit_customer(customer_id: int) -> dict:
    db = SessionLocal()
    try:
        cust = db.get(Customer, customer_id)
        if not cust:
            return {}
        facs = db.query(CreditFacility).filter(CreditFacility.customer_id == customer_id).all()
        pd_ = store.credit.get("prob_all", {}).get(customer_id)
        drivers = _explain_credit(customer_id, cust, pd_)
        repay = db.query(func.max(Repayment.days_late)).join(
            CreditFacility, Repayment.facility_id == CreditFacility.id
        ).filter(CreditFacility.customer_id == customer_id).scalar() or 0

        return {
            "customer": as_dict(cust),
            "pd": pd_,
            "grade": _grade(pd_) if pd_ is not None else None,
            "lgd": round(float(min(f.lgd or 0.45 for f in facs)), 4) if facs else None,
            "ead": round(float(sum(f.ead or 0 for f in facs)), 2),
            "expected_loss": round(float((pd_ or 0) * sum((f.ead or 0) * (f.lgd or 0.45) for f in facs)), 2),
            "max_days_late": int(repay),
            "facilities": [as_dict(f) for f in facs],
            "drivers": drivers,
            "early_warning": _early_warning(customer_id, pd_, repay),
        }
    finally:
        db.close()


def _explain_credit(customer_id: int, cust: Customer, pd_: float | None) -> list[dict]:
    """Explain the principal factors behind a prediction using model importances
    and the customer's own feature values (SHAP-lite, deterministic)."""
    if pd_ is None:
        return []
    drivers = []
    risk_map = {"sanctioned": "Sanctioned entity", "pep": "PEP flag", "adverse_media": "Adverse media"}
    for key, label in risk_map.items():
        if getattr(cust, key):
            drivers.append({"factor": label, "direction": "increases risk"})
    # top global importances (XGBoost gain) used as principal factors
    for imp in store.credit.get("importances", [])[:5]:
        drivers.append({"factor": imp["feature"], "direction": "top model driver",
                        "importance": imp["importance"]})
    return drivers


def _early_warning(customer_id: int, pd_: float | None, max_days_late: int) -> dict:
    level = "Green"
    reasons = []
    if pd_ is not None and pd_ >= 0.15:
        level = "Red"
        reasons.append(f"High default probability ({pd_:.1%})")
    elif pd_ is not None and pd_ >= 0.08:
        level = "Amber"
        reasons.append(f"Elevated default probability ({pd_:.1%})")
    if max_days_late > 30:
        level = "Red" if level == "Amber" else level
        reasons.append(f"Payments {max_days_late} days late")
    if not reasons:
        reasons.append("No deterioration signals")
    return {"level": level, "reasons": reasons}


# ---------------------------------------------------------------------------
# Fraud
# ---------------------------------------------------------------------------

def fraud_dashboard() -> dict:
    db = SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.app == "fraud").order_by(Alert.score.desc()).limit(200).all()
        return {
            "alerts": [as_dict(a) for a in alerts],
            "metrics": store.fraud.get("metrics", {}),
            "threshold": store.fraud.get("threshold", settings.fraud_alert_threshold),
            "scores": store.fraud.get("scores", {}),
        }
    finally:
        db.close()


def fraud_transactions(limit: int = 100, min_score: float = 0.0) -> list[dict]:
    db = SessionLocal()
    try:
        scores = store.fraud.get("scores", {})
        txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit * 5).all()
        out = []
        for t in txs:
            s = scores.get(t.id, 0.0)
            if s >= min_score:
                out.append({**as_dict(t), "fraud_score": round(s, 4)})
        out.sort(key=lambda r: r["fraud_score"], reverse=True)
        return out[:limit]
    finally:
        db.close()


def score_transaction(txn: dict) -> dict:
    """Real-time scoring of a single incoming transaction."""
    db = SessionLocal()
    try:
        df = fraud_features_from_dict(db, txn)
        if store.fraud.get("iforest") is None:
            return {"score": None, "alert": False, "message": "model not trained"}
        X = df[store.fraud["feature_names"]].fillna(0.0)
        Xs = store.fraud["scaler"].transform(X)
        anomaly = -store.fraud["iforest"].score_samples(Xs)
        # normalize with the training distribution's min/max (stable for single samples)
        a_min = store.fraud.get("anomaly_min", float(anomaly.min()))
        a_max = store.fraud.get("anomaly_max", float(anomaly.max()))
        anomaly01 = (anomaly - a_min) / max(a_max - a_min, 1e-9)
        score = float(anomaly01[0])
        return {
            "score": round(score, 4),
            "alert": bool(score >= store.fraud.get("threshold", 0.75)),
            "threshold": store.fraud.get("threshold", 0.75),
        }
    finally:
        db.close()


def fraud_features_from_dict(db, txn: dict):
    import pandas as pd
    row = {
        "id": 0, "customer_id": txn.get("customer_id"), "amount": float(txn.get("amount", 0)),
        "timestamp": pd.Timestamp(txn.get("timestamp") or datetime.now(timezone.utc)),
        "direction": txn.get("direction", "debit"),
        "counterparty_country": txn.get("counterparty_country", "US"),
        "counterparty_account": txn.get("counterparty_account", "NEW"),
        "is_internal": bool(txn.get("is_internal", False)),
        "fraud_label": None,
    }
    hist = db.query(Transaction).filter(Transaction.customer_id == row["customer_id"]).all()
    # customer mean/std from history
    import numpy as np
    amounts = [t.amount for t in hist] or [row["amount"]]
    mean = float(np.mean(amounts)); std = float(np.std(amounts)) or 1e-6
    z = (row["amount"] - mean) / std
    row["log_amount"] = float(np.log10(max(row["amount"], 1)))
    row["amount_zscore"] = z
    row["is_night"] = 1 if row["timestamp"].hour >= 22 or row["timestamp"].hour <= 5 else 0
    row["is_weekend"] = 1 if row["timestamp"].dayofweek >= 5 else 0
    seen = any(t.counterparty_account == row["counterparty_account"] for t in hist)
    row["new_beneficiary"] = 0 if seen else 1
    row["high_risk_country"] = 1 if row["counterparty_country"] in {"BR", "MX", "IN", "AE"} else 0
    row["round_amount"] = 1 if row["amount"] % 1000 == 0 else 0
    row["txn_velocity_3d"] = 1.0
    return pd.DataFrame([row])[store.fraud["feature_names"]]


def update_fraud_alert(alert_id: int, status: str, analyst: str, notes: str | None = None) -> dict:
    db = SessionLocal()
    try:
        a = db.get(Alert, alert_id)
        if not a:
            return {}
        a.status = status
        db.add(InvestigationCase(alert_id=alert_id, app="fraud", status="investigating" if status == "investigating" else "closed",
                                 analyst=analyst, notes=notes, outcome=status))
        db.commit()
        return as_dict(a)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# AML
# ---------------------------------------------------------------------------

def aml_dashboard() -> dict:
    db = SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.app == "aml").order_by(Alert.score.desc()).limit(200).all()
        cases = db.query(InvestigationCase).filter(InvestigationCase.app == "aml").all()
        return {
            "alerts": [as_dict(a) for a in alerts],
            "cases": [as_dict(c) for c in cases],
            "metrics": store.aml.get("metrics", {}),
            "threshold": store.aml.get("threshold", settings.aml_alert_threshold),
            "graph_patterns": store.aml.get("graphs", {}),
            "reporting_threshold": settings.aml_reporting_threshold,
        }
    finally:
        db.close()


def aml_case_action(case_id: int, action: str, analyst: str, notes: str | None = None) -> dict:
    db = SessionLocal()
    try:
        case = db.get(InvestigationCase, case_id)
        if not case:
            return {}
        if action in ("sar_filed", "closed", "investigating"):
            case.status = action
            case.outcome = action
            case.analyst = analyst
            case.notes = notes
            case.closed_at = datetime.now(timezone.utc) if action in ("sar_filed", "closed") else None
            if case.alert_id:
                alert = db.get(Alert, case.alert_id)
                if alert:
                    alert.status = "closed" if action in ("sar_filed", "closed") else "investigating"
        db.commit()
        return as_dict(case)
    finally:
        db.close()


def generate_alerts(clear: bool = False) -> dict:
    """Generate fraud & AML alerts from model scores (idempotent).

    With clear=True, existing alerts/cases are removed first (used on retraining).
    """
    db = SessionLocal()
    try:
        if clear:
            db.query(InvestigationCase).delete()
            db.query(Alert).delete()
        existing = { (a.app, a.transaction_id) for a in db.query(Alert).all() if a.transaction_id }
        created = {"fraud": 0, "aml": 0}
        fraud_scores = store.fraud.get("scores", {})
        aml_scores = store.aml.get("scores", {})
        fraud_threshold = store.fraud.get("threshold", 0.75)
        aml_threshold = store.aml.get("threshold", 0.70)

        # load all transactions once, score from the in-memory model store
        txs = db.query(Transaction).all()
        for t in txs:
            fs = fraud_scores.get(t.id)
            if fs is not None and fs >= fraud_threshold and ("fraud", t.id) not in existing:
                db.add(Alert(app="fraud", severity=_severity(fs), status="Open",
                             customer_id=t.customer_id, transaction_id=t.id,
                             title=f"Unusual payment {t.amount:,.0f} to {t.counterparty_name}",
                             description="Anomalous transaction pattern detected by Isolation Forest + rules.",
                             factors=["amount_zscore", "new_beneficiary", "high_risk_country"],
                             score=round(fs, 4), amount=t.amount))
                created["fraud"] += 1
            aml = aml_scores.get(t.id)
            if aml is not None and aml >= aml_threshold and ("aml", t.id) not in existing:
                db.add(Alert(app="aml", severity=_severity(aml), status="Open",
                             customer_id=t.customer_id, transaction_id=t.id,
                             title=f"Suspicious activity {t.amount:,.0f} via {t.txn_type}",
                             description="Potential structuring / layering pattern flagged for investigation.",
                             factors=["near_threshold", "rapid_movement", "high_risk_country"],
                             score=round(aml, 4), amount=t.amount))
                created["aml"] += 1
        db.commit()
        return created
    finally:
        db.close()


def _severity(score: float) -> str:
    if score >= 0.9:
        return "high"
    if score >= 0.8:
        return "medium"
    return "low"
