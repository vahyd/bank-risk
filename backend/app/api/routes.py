"""Unified REST API for the corporate banking platform."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .. import audit
from ..auth import require
from ..services import admin as admin_svc
from ..services import dashboard as dash_svc
from ..services import customers as cust_svc
from ..services import intelligence as intel_svc
from ..services import risk as risk_svc

router = APIRouter()

Identity = tuple[str, str]


# ---------------------------------------------------------------------------
# Health & executive overview
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    return dash_svc.health()


@router.get("/dashboard/overview")
def overview(identity: Identity = Depends(require("dashboard:read"))):
    return dash_svc.overview()


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@router.get("/customers")
def list_customers(q: str | None = None, limit: int = 50, offset: int = 0,
                   identity: Identity = Depends(require("customers:read"))):
    return cust_svc.list_customers(q=q, limit=min(limit, 200), offset=offset)


@router.get("/customers/{customer_id}")
def customer_profile(customer_id: int, identity: Identity = Depends(require("customers:read"))):
    profile = cust_svc.customer_profile(customer_id)
    if not profile:
        raise HTTPException(404, "Customer not found")
    return profile


# ---------------------------------------------------------------------------
# Application 1: Credit risk
# ---------------------------------------------------------------------------

@router.get("/credit-risk/portfolio")
def credit_portfolio(identity: Identity = Depends(require("credit:read"))):
    return risk_svc.credit_portfolio()


@router.get("/credit-risk/customers/{customer_id}")
def credit_customer(customer_id: int, identity: Identity = Depends(require("credit:read"))):
    out = risk_svc.credit_customer(customer_id)
    if not out:
        raise HTTPException(404, "Customer not found")
    return out


# ---------------------------------------------------------------------------
# Application 2: Fraud detection
# ---------------------------------------------------------------------------

@router.get("/fraud/dashboard")
def fraud_dashboard(identity: Identity = Depends(require("fraud:read"))):
    return risk_svc.fraud_dashboard()


@router.get("/fraud/transactions")
def fraud_transactions(limit: int = 100, min_score: float = 0.0,
                       identity: Identity = Depends(require("fraud:read"))):
    return risk_svc.fraud_transactions(limit=limit, min_score=min_score)


@router.post("/fraud/score")
def fraud_score(payload: dict, identity: Identity = Depends(require("fraud:write"))):
    user, role = identity
    result = risk_svc.score_transaction(payload)
    audit.log(user, role, "fraud.score", "transaction", {"payload": payload, "result": result})
    return result


@router.post("/fraud/alerts/{alert_id}")
def fraud_alert_update(alert_id: int, payload: dict,
                       identity: Identity = Depends(require("fraud:write"))):
    user, role = identity
    out = risk_svc.update_fraud_alert(alert_id, payload.get("status", "investigating"),
                                      payload.get("analyst", user), payload.get("notes"))
    audit.log(user, role, "fraud.alert.update", f"alert:{alert_id}", {"status": payload.get("status")})
    return out


# ---------------------------------------------------------------------------
# Application 3: AML
# ---------------------------------------------------------------------------

@router.get("/aml/dashboard")
def aml_dashboard(identity: Identity = Depends(require("aml:read"))):
    return risk_svc.aml_dashboard()


@router.post("/aml/cases/{case_id}")
def aml_case_action(case_id: int, payload: dict, identity: Identity = Depends(require("aml:write"))):
    user, role = identity
    out = risk_svc.aml_case_action(case_id, payload.get("action", "investigating"),
                                   payload.get("analyst", user), payload.get("notes"))
    audit.log(user, role, "aml.case.update", f"case:{case_id}", {"action": payload.get("action")})
    return out


# ---------------------------------------------------------------------------
# Application 4: Liquidity & cash-flow forecasting
# ---------------------------------------------------------------------------

@router.get("/liquidity/forecast/{customer_id}")
def liquidity_forecast(customer_id: int, horizon_days: int = Query(30, ge=1, le=180),
                       scenario: str = Query("base", pattern="^(base|delayed_receivables|sales_drop|unexpected_outflows)$"),
                       identity: Identity = Depends(require("liquidity:read"))):
    return intel_svc.forecast(customer_id, horizon_days, scenario)


@router.get("/liquidity/history/{customer_id}")
def liquidity_history(customer_id: int, identity: Identity = Depends(require("liquidity:read"))):
    return intel_svc.forecast_history(customer_id)


# ---------------------------------------------------------------------------
# Application 5: RM decision support (RAG + open-source LLM)
# ---------------------------------------------------------------------------

@router.post("/rm/chat")
def rm_chat(payload: dict, identity: Identity = Depends(require("rm:read"))):
    user, role = identity
    query = payload.get("query", "")
    customer_id = payload.get("customer_id")
    result = intel_svc.rm_chat(query, customer_id)
    audit.log(user, role, "rm.chat", "assistant", {"query": query[:200], "customer_id": customer_id})
    return result


@router.get("/rm/brief/{customer_id}")
def rm_brief(customer_id: int, identity: Identity = Depends(require("rm:read"))):
    brief = intel_svc.rm_brief(customer_id)
    if not brief:
        raise HTTPException(404, "Customer not found")
    return brief


# ---------------------------------------------------------------------------
# Application 6: Client segmentation
# ---------------------------------------------------------------------------

@router.get("/segmentation")
def segmentation(identity: Identity = Depends(require("segmentation:read"))):
    return intel_svc.segmentation_summary()


# ---------------------------------------------------------------------------
# Models, data quality & administration
# ---------------------------------------------------------------------------

@router.get("/models/quality")
def models_quality(identity: Identity = Depends(require("models:read"))):
    return admin_svc.data_quality()


@router.get("/models/runs")
def model_runs(identity: Identity = Depends(require("models:read"))):
    return admin_svc.model_runs()


@router.get("/admin/audit")
def audit_logs(limit: int = 100, identity: Identity = Depends(require("audit:read"))):
    return admin_svc.audit_logs(limit=min(limit, 500))


@router.post("/admin/train")
def retrain(identity: Identity = Depends(require("audit:read"))):
    user, role = identity
    audit.log(user, role, "admin.train", "models", {})
    return admin_svc.retrain(force=True)
