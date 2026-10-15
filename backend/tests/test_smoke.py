"""Smoke tests for the corporate banking platform API."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs lifespan: seed data + train models once
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_overview(client):
    r = client.get("/api/dashboard/overview", headers={"X-Role": "admin"})
    assert r.status_code == 200
    data = r.json()
    assert data["total_customers"] > 0
    assert data["total_transaction_volume"] > 0


def test_customers_list_and_profile(client):
    r = client.get("/api/customers", headers={"X-Role": "admin"})
    assert r.status_code == 200
    assert r.json()["total"] > 0
    cid = r.json()["items"][0]["id"]
    p = client.get(f"/api/customers/{cid}", headers={"X-Role": "admin"})
    assert p.status_code == 200
    assert p.json()["legal_name"]


def test_credit_portfolio(client):
    r = client.get("/api/credit-risk/portfolio", headers={"X-Role": "analyst"})
    assert r.status_code == 200
    assert r.json()["summary"]["n_facilities"] > 0


def test_fraud_and_aml_dashboards(client):
    r = client.get("/api/fraud/dashboard", headers={"X-Role": "analyst"})
    assert r.status_code == 200
    assert "metrics" in r.json()
    r = client.get("/api/aml/dashboard", headers={"X-Role": "compliance"})
    assert r.status_code == 200
    assert "metrics" in r.json()


def test_liquidity_forecast(client):
    customers = client.get("/api/customers", headers={"X-Role": "admin"}).json()["items"]
    cid = customers[0]["id"]
    r = client.get(f"/api/liquidity/forecast/{cid}", headers={"X-Role": "treasury"})
    assert r.status_code == 200
    assert "closing_balance" in r.json()


def test_rm_chat(client):
    r = client.post("/api/rm/chat", json={"query": "What is the AML reporting threshold?"},
                    headers={"X-Role": "rm"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_segmentation(client):
    r = client.get("/api/segmentation", headers={"X-Role": "admin"})
    assert r.status_code == 200
    assert len(r.json()["profiles"]) >= 2


def test_rbac_denied(client):
    r = client.get("/api/admin/audit", headers={"X-Role": "rm"})
    assert r.status_code == 403
