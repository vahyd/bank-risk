# API Reference

Base URL: `http://localhost:8000/api`
Interactive docs: `http://localhost:8000/docs`

All endpoints (except `/health`) accept demo RBAC headers:
`X-Role: admin|analyst|rm|compliance|treasury`, `X-User: name`. If no `X-Role`
header is sent, the API defaults to `admin`.

## Executive & customers

Scopes: `/dashboard/overview` → `dashboard:read` · `/customers*` → `customers:read` · `/health` is unauthenticated.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health, LLM mode, trained-model metrics |
| GET | `/dashboard/overview` | Executive KPIs + segment/industry mix |
| GET | `/customers?q=&limit=&offset=` | Customer search |
| GET | `/customers/{id}` | 360° profile (accounts, facilities, alerts, activity) |

## Credit risk

Scope: `credit:read`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/credit-risk/portfolio` | Exposure, EL, grades, calibration, importances, metrics |
| GET | `/credit-risk/customers/{id}` | PD/LGD/EAD/EL, drivers, early warning |

## Fraud

Scopes: reads → `fraud:read` · writes (`/fraud/score`, `/fraud/alerts/*`) → `fraud:write`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fraud/dashboard` | Alerts + model metrics |
| GET | `/fraud/transactions?limit=&min_score=` | Scored transactions |
| POST | `/fraud/score` | Real-time scoring of one transaction |
| POST | `/fraud/alerts/{id}` | Update alert status (investigation) |

Example:

```bash
curl -X POST http://localhost:8000/api/fraud/score \
  -H 'Content-Type: application/json' -H 'X-Role: analyst' \
  -d '{"customer_id": 7, "amount": 480000, "direction": "debit",
       "counterparty_country": "AE", "counterparty_account": "NEW-001",
       "counterparty_name": "New Beneficiary LLC"}'
```

## AML

Scopes: `/aml/dashboard` → `aml:read` · `/aml/cases/*` → `aml:write`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/aml/dashboard` | Alerts, cases, graph patterns, metrics |
| POST | `/aml/cases/{id}` | `{"action": "sar_filed"|"closed"|"investigating", "notes": ...}` |

## Liquidity

Scope: `liquidity:read`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/liquidity/forecast/{customer_id}?horizon_days=45&scenario=base` | Forecast + shortage alerts |
| GET | `/liquidity/history/{customer_id}` | Stored forecasts |

Scenarios: `base`, `delayed_receivables`, `sales_drop`, `unexpected_outflows`.

## RM assistant

Scope: `rm:read`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rm/chat` | `{"query": "...", "customer_id": optional}` → RAG answer + sources |
| GET | `/rm/brief/{customer_id}` | Meeting brief + next best actions |

## Segmentation, models, admin

Scopes: `/segmentation` → `segmentation:read` · `/models/*` → `models:read` · `/admin/*` → `audit:read`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/segmentation` | Segment profiles + customer assignments |
| GET | `/models/quality` | Data-quality report |
| GET | `/models/runs` | Model registry (training runs) |
| GET | `/admin/audit?limit=` | Audit trail |
| POST | `/admin/train` | Re-run pipeline + retrain all models |
