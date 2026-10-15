# Agent Instructions — Open-Source AI Platform for Corporate Banking

> Copy this file into any AI coding agent (Cursor, Claude Code, etc.) to rebuild,
> extend, or audit this platform. It is the authoritative specification.

## 1. Role and Objective

Act as a senior software architect, banking technology specialist, data engineer,
and machine-learning engineer.

Design and develop a modular, self-hosted **AI platform for corporate banking**
that uses open-source software to analyze corporate banking transactions, assess
risk, forecast liquidity, identify suspicious activities, and support relationship
managers.

The platform integrates six core applications:

1. Corporate credit risk assessment.
2. Fraud detection and prevention.
3. Anti-money laundering (AML).
4. Corporate liquidity and cash-flow forecasting.
5. Relationship manager decision support.
6. Corporate client segmentation.

Build a unified platform with shared data infrastructure, common corporate client
profiles, reusable AI models, explainability, dashboards, and audit trails. The
system must be a **working prototype with functional applications**, not a static
mock-up.

## 2. Technology Principles

- Prioritize open-source components with permissive, commercial-friendly licenses.
- Python for data engineering, ML, forecasting, and APIs.
- PostgreSQL as the primary relational database (SQLite allowed for zero-setup local dev).
- FastAPI for backend services.
- React + TypeScript for the UI.
- scikit-learn, XGBoost (with automatic gradient-boosting fallback when the native
  OpenMP runtime is unavailable), PyOD for ML and anomaly detection.
- NetworkX for transaction-network analysis.
- statsmodels ETS (StatsForecast-compatible interface) for cash-flow forecasting.
- TF-IDF retrieval + a self-hosted open-source LLM via **Ollama** (`llama3.1` or
  `mistral`) for the RM assistant (Haystack-compatible interface; swap for Haystack +
  pgvector in production).
- K-means + HDBSCAN for client segmentation.
- A `ModelRun` registry (MLflow-compatible schema) for experiment/model tracking.
- Docker Compose for deployment.

Verify maintenance status, license, and compatibility of every component before
adopting it. Do not assume every dependency is production-ready.

## 3. Shared Data Infrastructure

Required data domains:

- **Corporate customer data** — identifier, legal name/registration, industry,
  countries, size, turnover, ownership group, RM, products.
- **Transaction data** — id, account, timestamp, amount, currency, debit/credit,
  type, channel, counterparty (account/name/country), reference, status.
- **Financial & credit data** — facilities, limits, utilization, collateral,
  repayment schedules and delays, defaults.
- **Liquidity data** — historical balances and flows (derived from transactions).
- **Compliance & relationship data** — KYC/KYB, sanctions/PEP/adverse-media flags,
  alerts and investigation outcomes.

Label every field required / optional / derived. Use synthetic data when real data
is unavailable.

Engineering requirements: CSV/Parquet/API ingestion, validation, deduplication,
entity resolution (group mapping), dated FX conversion hooks, transaction
categorization, data lineage, quality reports, RBAC, audit logging, synthetic data
generation. Keep raw / cleaned / features / predictions / decisions separated.

## 4. Application 1 — Corporate Credit Risk

- XGBoost default-risk model + logistic-regression interpretable baseline.
- scikit-learn preprocessing/features; permutation or gain-based feature importance
  (SHAP-lite); calibration curve; Brier score.
- Outputs: PD (uncalibrated until tested), LGD (collateral-based), EAD, EL,
  risk grades with configurable thresholds, early-warning indicators, drivers,
  portfolio distribution and concentration.
- The model supports analyst review; it never auto-approves credit.

## 5. Application 2 — Fraud Detection

- PyOD Isolation Forest (unsupervised) + rule score (new beneficiary, unusual
  amount, off-hours, high-risk country, round amounts).
- NetworkX for transaction-chain analysis.
- Transaction risk scoring, batch and real-time (`POST /api/fraud/score`) API,
  alert explanations, prioritization and investigation status.
- Distinguish *anomalous* from *confirmed fraudulent*; never auto-block payments
  on an unsupervised score alone.

## 6. Application 3 — AML

- Configurable rules (structuring just below reporting threshold, rapid movement,
  large transfers) + NetworkX (circular flows, shared counterparties) + anomaly score.
- Risk-based alert prioritization, investigation case management, evidence and
  audit trails, jurisdiction-configurable thresholds.
- Every alert includes triggering transactions, rules/factors, evidence and status.
  AI findings are not proof of criminal activity.

## 7. Application 4 — Liquidity & Cash-Flow Forecasting

- Daily inflow/outflow/closing-balance forecasts at account, entity and group level.
- ETS statistical baseline with confidence intervals from residual spread.
- Scenarios: delayed receivables, sales drop, unexpected outflows.
- Shortage alerts; forecast accuracy tracking; avoid double-counting intra-group flows.

## 8. Application 5 — RM Decision Support

- Consolidated, explainable client view: profile, transaction trends, credit
  exposure, risk/compliance alerts, liquidity outlook.
- RAG over approved internal records and policies; citation tracking; meeting briefs.
- Locally hosted open-source LLM via Ollama; deterministic fallback when absent.
- Never invent figures; never make final credit decisions.

## 9. Application 6 — Client Segmentation

- Behavioral features (turnover, flows, credit usage, cross-border share).
- K-means (fixed k) + HDBSCAN (density-based discovery); segment profiles and
  descriptive statistics; visualization; risk/liquidity comparison; adoption analysis.
- Do not segment solely by protected characteristics; validate stability and
  business relevance.

## 10. Unified UI (React + TypeScript)

Pages: Executive Overview · Customers & Profiles · Credit Risk · Fraud Monitoring ·
AML & Investigations · Liquidity Forecast · RM Workspace · Segmentation ·
Models & Data Quality · Admin, Permissions & Audit.

Executive overview KPIs: total customers, transaction value/volume, credit
exposure, high-risk customers, fraud alerts, AML alerts, liquidity shortfalls,
segment distribution. Label synthetic/illustrative figures.

## 11. Governance & Security

- RBAC for RM / analyst / compliance / treasury / admin.
- Corporate-level data access restrictions, encryption in transit & at rest,
  audit trails for data access, predictions, overrides, and actions.
- Versioned datasets/models/config; drift and performance monitoring;
  explainability for high-impact predictions; human review for consequential
  decisions; configurable retention; dev/test/prod separation.
- Use synthetic data in development. Never use real customer data without
  authorization and compliance review.

## 12. Evaluation & Testing

- Credit: AUC, precision/recall, calibration (Brier), default capture, false positives.
- Fraud: precision/recall, detected value, false-positive rate.
- AML: alert precision, investigation yield, workload, coverage on labeled cases.
- Liquidity: MAE / WAPE by horizon, shortage detection.
- RM assistant: factual accuracy, citation coverage, permission enforcement.
- Segmentation: stability, interpretability, business relevance, fairness checks.
- Prevent data leakage (no post-decision information in training features).

## 13. Implementation Phases

1. **Foundation** — repo, DB, API, frontend, synthetic dataset, ingestion/validation/entity resolution.
2. **First three apps** — credit risk, fraud, AML.
3. **Treasury & intelligence** — liquidity forecasting, segmentation, RM assistant.
4. **Integration & governance** — unified dashboards, access controls, audit, monitoring, cross-app workflows, tests.
5. **Demo & documentation** — populate with synthetic data, demonstrate all six
   use cases end to end, provide setup instructions, API docs, architecture
   diagrams, and test results.

## 14. Required Deliverables

1. Working, locally deployable application.
2. Documented software architecture.
3. Database schema + synthetic dataset generator.
4. Six functional AI applications.
5. Unified dashboard.
6. API endpoints with example requests.
7. Automated tests and model evaluation reports.

## 15. Three Instructions That Improve the Result

1. **Start with synthetic data** — realistic corporates, accounts, transactions,
   credit facilities, payment anomalies, and cash-flow histories so the platform
   works before any bank integration.
2. **Build demonstrable workflows, not model wrappers** — a suspicious payment
   produces an alert, shows related transactions, lets an analyst investigate,
   and records the outcome.
3. **Verify every open-source dependency** — check licensing and maintenance;
   prefer scikit-learn / XGBoost / NetworkX over inactive specialized repos.

## Acceptance Criterion

Run the application locally and demonstrate **all six use cases end to end using
synthetic corporate banking data**.
