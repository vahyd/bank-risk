"""Synthetic corporate-banking data generator.

Creates a realistic, fully synthetic dataset for development and testing:
corporate customers (with group structure), accounts, credit facilities,
repayment history, and ~2 years of transactions containing planted
credit-default, fraud, and AML patterns used to train and evaluate the models.

Everything is deterministic for a given seed. No real customer data.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ..config import settings

# ---------------------------------------------------------------------------
# Static dictionaries
# ---------------------------------------------------------------------------

INDUSTRIES = {
    "Manufacturing": {"risk": 0.10, "volatility": 0.9},
    "Wholesale Trade": {"risk": 0.14, "volatility": 1.0},
    "Construction": {"risk": 0.20, "volatility": 1.3},
    "Real Estate": {"risk": 0.22, "volatility": 1.2},
    "Transport & Logistics": {"risk": 0.16, "volatility": 1.1},
    "Technology": {"risk": 0.08, "volatility": 0.8},
    "Retail": {"risk": 0.15, "volatility": 1.2},
    "Energy & Utilities": {"risk": 0.12, "volatility": 1.0},
    "Agriculture": {"risk": 0.18, "volatility": 1.0},
    "Professional Services": {"risk": 0.09, "volatility": 0.7},
    "Healthcare": {"risk": 0.07, "volatility": 0.6},
    "Food & Beverage": {"risk": 0.13, "volatility": 1.0},
}

COUNTRIES = {
    "DE": 0.08, "FR": 0.09, "NL": 0.07, "ES": 0.10, "IT": 0.10, "PL": 0.09,
    "US": 0.06, "GB": 0.07, "CH": 0.05, "SE": 0.06, "AE": 0.04, "SG": 0.04,
    "BR": 0.06, "MX": 0.05, "IN": 0.04,
}
HIGH_RISK_COUNTRIES = {"BR", "MX", "IN", "AE"}
SIZES = ["SME", "SME", "Mid", "Mid", "Mid", "Large", "Large"]
RMS = ["A. Weber", "L. Chen", "M. Rossi", "S. Novak", "J. Silva", "K. Okafor", "T. Berg", "E. Haddad"]
PRODUCTS = ["Current Account", "Trade Finance", "Term Loan", "Revolver", "FX", "Treasury", "Cards"]
CHANNELS = ["online", "online", "online", "branch", "api", "swift"]
TXN_TYPES = ["wire", "wire", "wire", "bulk", "trade", "card", "fee", "salary", "tax"]
PAYMENT_REF = ["INV-", "PO-", "SAL-", "TAX-", "FEE-", "REF-", "TRD-"]


def _rng() -> np.random.Generator:
    return np.random.default_rng(settings.seed)


# ---------------------------------------------------------------------------
# Customers, accounts, facilities
# ---------------------------------------------------------------------------

def gen_customers(n: int | None = None) -> pd.DataFrame:
    n = n or settings.n_customers
    rng = _rng()
    rows = []
    groups = [f"GRP-{i:03d}" for i in range(1, 1 + max(1, n // 4))]
    industries = list(INDUSTRIES)
    countries = list(COUNTRIES)
    country_weights = np.array([COUNTRIES[c] for c in countries])

    for i in range(1, n + 1):
        industry = industries[i % len(industries)]
        country = countries[int(rng.choice(len(countries), p=country_weights / country_weights.sum()))]
        size = SIZES[i % len(SIZES)]
        if size == "SME":
            turnover = float(rng.uniform(2e6, 25e6))
            employees = int(rng.integers(10, 120))
        elif size == "Mid":
            turnover = float(rng.uniform(25e6, 250e6))
            employees = int(rng.integers(120, 1200))
        else:
            turnover = float(rng.uniform(250e6, 2.5e9))
            employees = int(rng.integers(1200, 15000))

        # operating countries: mostly home country, sometimes 2-4
        n_ops = int(rng.choice([1, 1, 1, 2, 2, 3, 4], p=[0.5, 0.2, 0.1, 0.08, 0.06, 0.04, 0.02]))
        ops = [country] + [countries[int(rng.integers(len(countries)))] for _ in range(n_ops - 1)]

        rows.append({
            "id": i,
            "legal_name": f"{industry.split()[0]} {['Alpha', 'Beta', 'Gamma', 'Delta', 'Omega', 'Nova', 'Prime', 'Vertex'][i % 8]} "
                          f"{['GmbH', 'Sarl', 'BV', 'SL', 'SpA', 'Ltd', 'Inc'][i % 7]}",
            "registration_number": f"REG-{country}-{100000 + i}",
            "industry": industry,
            "country": country,
            "operating_countries": ops,
            "size": size,
            "annual_turnover": turnover,
            "employees": employees,
            "group_id": groups[i % len(groups)],
            "rm_name": RMS[i % len(RMS)],
            "products": [p for p in PRODUCTS[: int(rng.integers(2, 6))]],
            "kyc_status": "Passed" if rng.random() > 0.04 else "Under Review",
            "sanctioned": bool(rng.random() < 0.005),
            "pep": bool(rng.random() < 0.015),
            "adverse_media": bool(rng.random() < 0.03),
        })
    return pd.DataFrame(rows)


def gen_accounts(customers: pd.DataFrame) -> pd.DataFrame:
    n = settings.n_accounts
    rng = _rng()
    rows = []
    used_ibans: set[str] = set()
    cids = customers["id"].tolist()
    for i in range(1, n + 1):
        cid = int(cids[i % len(cids)])
        iban = f"SYN{np.base_repr(100000 + i, 36).upper()}BANK{i:04d}"
        used_ibans.add(iban)
        rows.append({
            "id": i,
            "customer_id": cid,
            "iban": iban,
            "currency": rng.choice(["USD", "EUR", "EUR", "GBP"], p=[0.55, 0.25, 0.1, 0.1]),
            "account_type": rng.choice(["operating", "operating", "operating", "deposit", "loan"], p=[0.6, 0.2, 0.05, 0.08, 0.07]),
            "opened_at": datetime(2023, 1, 1, tzinfo=timezone.utc) + timedelta(days=int(rng.integers(0, 400))),
            "balance": 0.0,
        })
    return pd.DataFrame(rows)


def gen_facilities(customers: pd.DataFrame) -> pd.DataFrame:
    n = settings.n_facilities
    rng = _rng()
    rows = []
    cids = customers.set_index("id")
    for i in range(1, n + 1):
        cid = int(customers["id"].iloc[i % len(customers)])
        cust = cids.loc[cid]
        turnover = float(cust["annual_turnover"])
        industry_risk = INDUSTRIES[cust["industry"]]["risk"]
        country_risk = 0.06 if cust["country"] in HIGH_RISK_COUNTRIES else 0.02
        leverage = float(rng.uniform(0.2, 1.4))
        delay = float(rng.uniform(0, 45))
        # planted hazard: higher leverage + risky industry + payment delay -> higher default prob
        z = -1.4 + 1.5 * leverage + 4.0 * industry_risk + 2.5 * country_risk + 0.012 * delay + float(rng.normal(0, 0.95))
        pd_ = 1.0 / (1.0 + math.exp(-z))
        defaulting = bool(rng.random() < pd_)
        limit = float(turnover * rng.uniform(0.15, 0.6))
        utilization = float(min(1.0, rng.uniform(0.2, 1.0))) if not defaulting else float(rng.uniform(0.85, 1.05))
        collateral = float(limit * rng.uniform(0.0, 1.4))
        lgd = max(0.15, 1.0 - min(1.0, collateral / max(limit * utilization, 1.0))) * float(rng.uniform(0.9, 1.1))
        rows.append({
            "id": i,
            "customer_id": cid,
            "facility_type": rng.choice(["revolver", "term", "trade", "overdraft"], p=[0.4, 0.3, 0.2, 0.1]),
            "limit_amount": round(limit, 2),
            "utilization": round(utilization, 3),
            "currency": rng.choice(["USD", "EUR"], p=[0.6, 0.4]),
            "start_date": datetime(2023, 6, 1, tzinfo=timezone.utc) + timedelta(days=int(rng.integers(0, 300))),
            "maturity_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "interest_spread_bps": int(180 + pd_ * 450 + rng.integers(0, 80)),
            "collateral_value": round(collateral, 2),
            "status": "Defaulted" if defaulting else "Performing",
            "pd": round(min(pd_, 0.35), 4),
            "lgd": round(min(lgd, 1.0), 4),
            "ead": round(limit * utilization, 2),
            "expected_loss": round(pd_ * lgd * limit * utilization, 2),
            "risk_grade": _grade(pd_),
        })
    return pd.DataFrame(rows)


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


# ---------------------------------------------------------------------------
# Transactions with planted fraud & AML patterns
# ---------------------------------------------------------------------------

def gen_transactions(customers: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    """Generate ~2 years of transactions, including labeled fraud and AML events."""
    n = settings.n_transactions
    rng = _rng()
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 12, 31, tzinfo=timezone.utc)
    total_days = (end - t0).days
    # Reserve ~3.5% of the transaction budget for planted fraud/AML patterns
    # so the labeled events are always present.
    normal_target = int(n * 0.965)

    cust = customers.set_index("id")
    acct_by_cust: dict[int, list[int]] = {}
    for _, a in accounts.iterrows():
        acct_by_cust.setdefault(int(a["customer_id"]), []).append(int(a["id"]))
    iban_by_acct = {int(a["id"]): a["iban"] for _, a in accounts.iterrows()}
    cust_by_acct = {int(a["id"]): int(a["customer_id"]) for _, a in accounts.iterrows()}

    rows: list[dict] = []
    ref_counter = 1000000

    # Choose fraud customers (~6% of customers) and AML customers (~6%)
    cids = customers["id"].tolist()
    fraud_cust = set(rng.choice(cids, size=max(2, int(len(cids) * 0.06)), replace=False).tolist())
    aml_cust = set(rng.choice(cids, size=max(2, int(len(cids) * 0.06)), replace=False).tolist())

    # Pre-generate counterparty pool (other corporates + external names)
    ext_names = ["Global Parts Ltd", "Meridian Trading FZCO", "Atlas Commodities SA", "Helix Logistics BV",
                 "Nordic Steel AB", "Pacific Imports Inc", "Cedar Holdings LLC", "Brightline Services Ltd",
                 "Orion Energy GmbH", "Summit Capital Partners", "Redwood Textiles", "Kestrel Aerospace"]
    ext_countries = list(COUNTRIES)

    def mk_txn(i: int, acct_id: int, ts: datetime, amount: float, direction: str, txn_type: str,
               channel: str, cp_name: str, cp_acct: str, cp_country: str, ref: str,
               fraud_label: int | None = None, aml_label: int | None = None, internal: bool = False) -> dict:
        return {
            "id": i, "txn_ref": f"TXN-{ref}", "account_id": acct_id,
            "customer_id": cust_by_acct[acct_id], "timestamp": ts, "amount": round(float(amount), 2),
            "currency": "USD", "direction": direction, "txn_type": txn_type, "channel": channel,
            "counterparty_name": cp_name, "counterparty_account": cp_acct, "counterparty_country": cp_country,
            "reference": ref, "status": "Completed", "fraud_label": fraud_label, "aml_label": aml_label,
            "fraud_score": None, "aml_score": None, "is_internal": internal,
        }

    i = 1
    # --- Normal business transactions -------------------------------------------------
    for cid in cids:
        c = cust.loc[cid]
        accts = acct_by_cust.get(cid, [])
        if not accts:
            continue
        turnover = float(c["annual_turnover"])
        monthly = turnover / 12.0
        for month in range(0, total_days // 30):
            season = 1.0 + 0.18 * math.sin(2 * math.pi * (month % 12) / 12.0)
            n_tx = int(rng.integers(14, 40))
            for _ in range(n_tx):
                if i > normal_target:
                    break
                acct_id = int(rng.choice(accts))
                base = monthly / 22.0
                amount = abs(float(rng.lognormal(mean=math.log(max(base, 100.0)), sigma=0.9))) * season
                amount = min(amount, 3.0e6)
                day_off = int(rng.integers(0, 30))
                ts = t0 + timedelta(days=month * 30 + day_off, hours=int(rng.integers(0, 24)),
                                    minutes=int(rng.integers(0, 60)))
                direction = rng.choice(["debit", "credit"], p=[0.52, 0.48])
                txn_type = str(rng.choice(TXN_TYPES))
                channel = str(rng.choice(CHANNELS))
                cp_name = str(rng.choice(ext_names))
                cp_country = str(rng.choice(ext_countries))
                cp_acct = f"EXT{int(rng.integers(100000, 999999))}"
                ref = f"{rng.choice(PAYMENT_REF)}{ref_counter}"
                rows.append(mk_txn(i, acct_id, ts, amount, direction, txn_type, channel,
                                   cp_name, cp_acct, cp_country, ref, fraud_label=0, aml_label=0))
                ref_counter += 1
                i += 1
            if i > normal_target:
                break
        if i > normal_target:
            break

    # --- Planted FRAUD events ---------------------------------------------------------
    for cid in list(fraud_cust):
        if i > n - 6:
            break
        accts = acct_by_cust.get(cid, [])
        if not accts:
            continue
        c = cust.loc[cid]
        acct_id = int(rng.choice(accts))
        usual = float(c["annual_turnover"]) / 12.0 / 20.0
        for k in range(4):
            ts = t0 + timedelta(days=int(rng.integers(100, total_days - 50)),
                                hours=int(rng.choice([1, 2, 3, 23])), minutes=int(rng.integers(0, 60)))
            amount = float(usual * rng.uniform(3.5, 9.0))
            cp_country = str(rng.choice(list(HIGH_RISK_COUNTRIES)))
            rows.append(mk_txn(i, acct_id, ts, amount, "debit", "wire", "online",
                               "New Beneficiary LLC", f"NEW{int(rng.integers(100000, 999999))}",
                               cp_country, f"FRD-{ref_counter}", fraud_label=1, aml_label=0))
            ref_counter += 1
            i += 1
        # clean contrast txns for the same customer
        for _ in range(3):
            ts = t0 + timedelta(days=int(rng.integers(0, total_days)), hours=int(rng.integers(6, 20)))
            rows.append(mk_txn(i, acct_id, ts, float(usual * rng.uniform(0.3, 1.2)), "debit", "wire", "online",
                               str(rng.choice(ext_names)), f"EXT{int(rng.integers(100000, 999999))}",
                               c["country"], f"CLN-{ref_counter}", fraud_label=0, aml_label=0))
            ref_counter += 1
            i += 1

    # --- Planted AML events -----------------------------------------------------------
    for cid in list(aml_cust):
        if i > n - 12:
            break
        accts = acct_by_cust.get(cid, [])
        if not accts:
            continue
        c = cust.loc[cid]
        acct_id = int(rng.choice(accts))
        base_ts = t0 + timedelta(days=int(rng.integers(60, total_days - 120)))

        # structuring: multiple payments just below reporting threshold
        for k in range(5):
            ts = base_ts + timedelta(days=k, hours=14)
            amount = float(settings.aml_reporting_threshold * rng.uniform(0.92, 0.995))
            rows.append(mk_txn(i, acct_id, ts, amount, "debit", "wire", "branch",
                               "Cash Depot Ltd", f"CD{int(rng.integers(100000, 999999))}",
                               str(rng.choice(list(HIGH_RISK_COUNTRIES))), f"STR-{ref_counter}", aml_label=1, fraud_label=0))
            ref_counter += 1
            i += 1

        # rapid movement: large inflow then immediate outflow to high-risk country
        big = float(c["annual_turnover"] * rng.uniform(0.02, 0.05))
        ts_in = base_ts + timedelta(days=10, hours=9)
        rows.append(mk_txn(i, acct_id, ts_in, big, "credit", "wire", "swift",
                           str(rng.choice(ext_names)), f"EXT{int(rng.integers(100000, 999999))}",
                           "AE", f"RAP-{ref_counter}-IN", aml_label=1, fraud_label=0))
        ref_counter += 1
        i += 1
        ts_out = ts_in + timedelta(hours=7)
        rows.append(mk_txn(i, acct_id, ts_out, big * 0.97, "debit", "wire", "swift",
                           "Rapid Flow FZCO", f"RF{int(rng.integers(100000, 999999))}",
                           "AE", f"RAP-{ref_counter}-OUT", aml_label=1, fraud_label=0))
        ref_counter += 1
        i += 1

    # --- Circular transfers (3 accounts in a loop within a week) ----------------------
    loop_cust = rng.choice(cids, size=3, replace=False).tolist()
    loop_accts = []
    for cid in loop_cust:
        a = acct_by_cust.get(cid, [])
        if a:
            loop_accts.append(int(a[0]))
    if len(loop_accts) >= 3 and i < n - 3:
        ts = t0 + timedelta(days=int(rng.integers(30, 200)), hours=10)
        amt = float(rng.uniform(80_000, 400_000))
        for k in range(3):
            src = loop_accts[k]
            dst = loop_accts[(k + 1) % 3]
            rows.append(mk_txn(i, src, ts + timedelta(days=k * 2), amt, "debit", "wire", "online",
                               cust.loc[cust_by_acct[dst]]["legal_name"], iban_by_acct[dst],
                               cust.loc[cust_by_acct[dst]]["country"], f"CIR-{ref_counter}",
                               aml_label=1, fraud_label=0, internal=True))
            ref_counter += 1
            i += 1

    # Trim to target count if overshot (keep every planted event by trimming from start of normal txns)
    df = pd.DataFrame(rows)
    if len(df) > n:
        keep_last = df[df["fraud_label"] == 1].index.min() if (df["fraud_label"] == 1).any() else n
        drop_n = len(df) - n
        normal_idx = df[(df["fraud_label"] == 0) & (df["aml_label"] == 0)].index[:drop_n]
        df = df.drop(normal_idx)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["id"] = range(1, len(df) + 1)
    df["txn_ref"] = [f"TXN-{1000000 + k}" for k in range(len(df))]
    return df


def gen_repayments(facilities: pd.DataFrame) -> pd.DataFrame:
    rng = _rng()
    rows = []
    i = 1
    for _, f in facilities.iterrows():
        n_pmts = int(rng.integers(8, 24))
        defaulting = f["status"] == "Defaulted"
        due = f["start_date"]
        for k in range(n_pmts):
            due = due + timedelta(days=30)
            amount_due = round(float(f["limit_amount"]) * float(f["utilization"]) / max(n_pmts, 1), 2)
            if defaulting and k >= max(2, n_pmts - int(rng.integers(2, 6))):
                days_late = int(rng.integers(31, 120))
                paid = amount_due * float(rng.uniform(0.0, 0.6))
                paid_date = due + timedelta(days=days_late)
            else:
                days_late = max(0, int(rng.normal(2, 4)))
                paid = amount_due
                paid_date = due + timedelta(days=days_late)
            rows.append({
                "id": i, "facility_id": int(f["id"]), "due_date": due, "amount_due": amount_due,
                "amount_paid": round(paid, 2), "paid_date": paid_date, "days_late": days_late,
            })
            i += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Top-level generation + persistence
# ---------------------------------------------------------------------------

def generate() -> dict[str, pd.DataFrame]:
    customers = gen_customers()
    accounts = gen_accounts(customers)
    facilities = gen_facilities(customers)
    transactions = gen_transactions(customers, accounts)
    repayments = gen_repayments(facilities)
    return {
        "customers": customers,
        "accounts": accounts,
        "facilities": facilities,
        "transactions": transactions,
        "repayments": repayments,
    }


def compute_balances(accounts: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """Derive each account's current balance from its transaction history + opening float."""
    net = transactions.groupby("account_id").apply(
        lambda g: float((g.loc[g["direction"] == "credit", "amount"].sum()
                         - g.loc[g["direction"] == "debit", "amount"].sum())),
        include_groups=False,
    )
    rng = _rng()
    accounts = accounts.copy()
    accounts["balance"] = accounts["id"].map(net).fillna(0.0) + rng.uniform(1e4, 2e6, size=len(accounts))
    return accounts
