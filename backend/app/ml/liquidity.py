"""Cash-flow & liquidity forecasting.

Statistical baseline: ETS (exponential smoothing) via statsmodels on daily
balance / inflow / outflow series, with confidence intervals from residual
spread and a scenario engine (delayed receivables, sales drop, unexpected
outflows). Falls back to a rolling-window baseline if statsmodels is missing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ..db import SessionLocal, as_dict, jsonable
from ..db import Account, Customer, Forecast, Transaction


def _daily_series(transactions: pd.DataFrame, account_id: int | None = None) -> pd.DataFrame:
    t = transactions.copy()
    if account_id is not None:
        t = t[t["account_id"] == account_id]
    t["date"] = t["timestamp"].dt.date
    t["inflow"] = np.where(t["direction"] == "credit", t["amount"], 0.0)
    t["outflow"] = np.where(t["direction"] == "debit", t["amount"], 0.0)
    daily = t.groupby("date").agg(inflow=("inflow", "sum"), outflow=("outflow", "sum")).reset_index()
    daily["net"] = daily["inflow"] - daily["outflow"]
    return daily.sort_values("date")


def _ets_forecast(series: pd.Series, horizon: int) -> dict | None:
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        model = ExponentialSmoothing(series.astype(float), trend="add", seasonal=None,
                                     damped_trend=True).fit()
        fc = model.forecast(horizon)
        resid = model.resid.dropna()
        sigma = float(resid.std()) if len(resid) else float(series.std())
        return {"mean": fc.tolist(), "sigma": sigma, "method": "ets"}
    except Exception:
        return None


def _rolling_forecast(series: pd.Series, horizon: int) -> dict:
    window = max(3, min(14, len(series)))
    base = float(series.tail(window).mean())
    sigma = float(series.tail(window).std()) if len(series) > 1 else base * 0.1
    return {"mean": [base] * horizon, "sigma": sigma, "method": "rolling_mean"}


def forecast_customer(customer_id: int, horizon_days: int = 30,
                      scenario: str = "base", persist: bool = True) -> dict:
    db = SessionLocal()
    try:
        customer = db.get(Customer, customer_id)
        if not customer:
            return {"error": "customer not found"}
        accts = db.query(Account).filter(Account.customer_id == customer_id).all()
        acct_ids = [a.id for a in accts]
        txns = pd.read_sql(
            db.query(Transaction).filter(Transaction.customer_id == customer_id).statement,
            db.bind, parse_dates=["timestamp"],
        )
        if txns.empty:
            return {"error": "no transaction history"}

        daily = _daily_series(txns)
        inflow_series = daily.set_index("date")["inflow"].asfreq("D").fillna(0.0)
        outflow_series = daily.set_index("date")["outflow"].asfreq("D").fillna(0.0)
        net_series = daily.set_index("date")["net"].asfreq("D").fillna(0.0)

        # scenario adjustments on expected flows
        inflow_fc = _ets_forecast(inflow_series, horizon_days) or _rolling_forecast(inflow_series, horizon_days)
        outflow_fc = _ets_forecast(outflow_series, horizon_days) or _rolling_forecast(outflow_series, horizon_days)
        if scenario == "delayed_receivables":
            inflow_fc["mean"] = [v * 0.7 for v in inflow_fc["mean"]]
        elif scenario == "sales_drop":
            inflow_fc["mean"] = [v * 0.85 for v in inflow_fc["mean"]]
            outflow_fc["mean"] = [v * 1.05 for v in outflow_fc["mean"]]
        elif scenario == "unexpected_outflows":
            outflow_fc["mean"] = [v * 1.25 for v in outflow_fc["mean"]]

        balance = sum(a.balance for a in accts)
        dates = [(datetime.now(timezone.utc) + timedelta(days=i)).date().isoformat() for i in range(1, horizon_days + 1)]
        closing = []
        cum = balance
        for inf, outf in zip(inflow_fc["mean"], outflow_fc["mean"]):
            cum += inf - outf
            closing.append(round(float(cum), 2))

        min_close = min(closing) if closing else balance
        shortage_days = [d for d, c in zip(dates, closing) if c < 0.15 * balance]
        payload = {
            "customer_id": customer_id,
            "horizon_days": horizon_days,
            "scenario": scenario,
            "method": f"in:{inflow_fc['method']} / out:{outflow_fc['method']}",
            "current_balance": round(float(balance), 2),
            "dates": dates,
            "inflow_forecast": [round(v, 2) for v in inflow_fc["mean"]],
            "outflow_forecast": [round(v, 2) for v in outflow_fc["mean"]],
            "closing_balance": closing,
            "min_closing_balance": round(float(min_close), 2),
            "shortage_days": shortage_days,
            "shortage_alert": len(shortage_days) > 0,
            "confidence_interval": [
                [round(max(0, v - 1.64 * inflow_fc["sigma"]), 2), round(v + 1.64 * inflow_fc["sigma"], 2)]
                for v in inflow_fc["mean"]
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if persist:
            db.add(Forecast(customer_id=customer_id, horizon_days=horizon_days,
                            method=payload["method"], payload=jsonable(payload)))
            db.commit()
        return payload
    finally:
        db.close()
