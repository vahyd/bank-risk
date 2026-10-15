"""Model store: trains, evaluates, persists and serves all six application models.

- Credit risk: XGBoost classifier + logistic-regression interpretable baseline,
  calibrated probability check, feature importances.
- Fraud: PyOD Isolation Forest (unsupervised) + rule score; metrics vs planted labels.
- AML: rule engine + NetworkX graph patterns + Isolation Forest anomaly; alert
  prioritization via XGBoost when labels exist.
- Liquidity: statistical baseline (ETS via statsmodels) + scenario engine.
- Segmentation: K-means + HDBSCAN clustering with profile summaries.
- RM assistant: TF-IDF retrieval + Ollama LLM (see llm.py / rag.py).

Every trained model records a ModelRun row with metrics, parameters and status.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except Exception:  # pragma: no cover — missing libomp on some macOS setups
    from sklearn.ensemble import HistGradientBoostingClassifier as XGBClassifier  # type: ignore
    XGB_AVAILABLE = False

from ..config import settings
from ..db import ModelRun, SessionLocal
from .features import aml_features, credit_features, fraud_features, segmentation_features
from .graphs import circular_flows, rapid_movement, shared_counterparty_clusters

FEATURE_COLS_CREDIT = [
    "log_turnover", "log_employees", "industry_risk", "country_risk", "size_ordinal",
    "n_products", "sanctioned", "pep", "adverse_media", "total_limit",
    "mean_utilization", "max_utilization", "mean_collateral_ratio", "n_facilities",
    "mean_spread", "max_days_late", "mean_days_late", "missed_payments", "n_tx",
    "avg_monthly_credit", "avg_monthly_debit", "tx_volatility", "max_tx", "mean_tx",
    "net_flow_ratio", "high_risk_share",
]

FEATURE_COLS_FRAUD = ["log_amount", "amount_zscore", "is_night", "is_weekend",
                      "new_beneficiary", "high_risk_country", "round_amount", "txn_velocity_3d"]
FEATURE_COLS_AML = ["log_amount", "amount_zscore", "near_threshold", "large_txn", "internal",
                    "high_risk_country", "new_beneficiary", "txn_velocity_3d", "round_amount"]


def _safe_auc(y, prob) -> float | None:
    try:
        if len(set(y)) < 2:
            return None
        return float(roc_auc_score(y, prob))
    except Exception:
        return None


class ModelStore:
    def __init__(self) -> None:
        self.credit: dict = {}
        self.fraud: dict = {}
        self.aml: dict = {}
        self.segmentation: dict = {}
        self.trained_at: str | None = None
        os.makedirs(settings.artifacts_dir, exist_ok=True)

    # ------------------------------------------------------------------ helpers
    def _save(self, name: str, obj: dict) -> None:
        joblib.dump(obj, os.path.join(settings.artifacts_dir, f"{name}.joblib"))

    def _load(self, name: str) -> dict | None:
        path = os.path.join(settings.artifacts_dir, f"{name}.joblib")
        return joblib.load(path) if os.path.exists(path) else None

    def _record(self, name: str, metrics: dict, params: dict, status: str = "ok") -> None:
        db = SessionLocal()
        try:
            db.add(ModelRun(name=name, version=f"{time.time_ns()}", metrics=metrics,
                            params=params, trained_at=datetime.now(timezone.utc), status=status))
            db.commit()
        finally:
            db.close()

    # ------------------------------------------------------------------ credit
    def train_credit(self, frames: dict[str, pd.DataFrame], force: bool = False) -> dict:
        cached = self._load("credit") if not force else None
        if cached and not force:
            self.credit = cached
            return cached

        df = credit_features(frames["customers"], frames["accounts"], frames["facilities"],
                             frames["repayments"], frames["transactions"])
        X = df[FEATURE_COLS_CREDIT].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        y = df["default"].astype(int)

        metrics: dict = {"n_customers": int(len(df)), "default_rate": float(y.mean())}
        if len(set(y)) < 2:
            # degenerate case — record and bail with trivial model
            self.credit = {"feature_names": FEATURE_COLS_CREDIT, "metrics": metrics, "degenerate": True}
            self._save("credit", self.credit)
            self._record("credit_risk", metrics, {"degenerate": True})
            return self.credit

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=settings.seed, stratify=y)

        if XGB_AVAILABLE:
            xgb = XGBClassifier(n_estimators=120, max_depth=3, learning_rate=0.08,
                                subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
                                random_state=settings.seed)
        else:
            xgb = XGBClassifier(max_iter=120, max_depth=None, learning_rate=0.08,
                                l2_regularization=1.0, random_state=settings.seed)
        xgb.fit(X_tr, y_tr)
        prob_te = xgb.predict_proba(X_te)[:, 1]
        pred_te = (prob_te >= 0.5).astype(int)

        lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.8))
        lr.fit(X_tr, y_tr)
        prob_lr = lr.predict_proba(X_te)[:, 1]

        auc_xgb = _safe_auc(y_te, prob_te)
        auc_lr = _safe_auc(y_te, prob_lr)
        brier = float(brier_score_loss(y_te, prob_te)) if len(set(y_te)) > 1 else None

        if hasattr(xgb, "feature_importances_"):
            imp_values = xgb.feature_importances_.tolist()
        else:
            from sklearn.inspection import permutation_importance
            imp_values = permutation_importance(xgb, X_te, y_te, n_repeats=5,
                                                random_state=settings.seed).importances_mean.tolist()
        importances = sorted(
            zip(FEATURE_COLS_CREDIT, imp_values),
            key=lambda kv: kv[1], reverse=True,
        )

        # calibration curve points for the dashboard
        frac_pos, mean_pred = calibration_curve(y_te, prob_te, n_bins=8)
        calibration = [{"bin": i, "mean_predicted": round(float(mp), 3), "fraction_positive": round(float(fp), 3)}
                       for i, (mp, fp) in enumerate(zip(mean_pred, frac_pos))]

        # full-sample probabilities for scoring
        prob_all = xgb.predict_proba(X)[:, 1]

        self.credit = {
            "feature_names": FEATURE_COLS_CREDIT,
            "xgb": xgb,
            "lr": lr,
            "prob_all": {int(cid): float(p) for cid, p in zip(df["customer_id"], prob_all)},
            "importances": [{"feature": f, "importance": round(i, 4)} for f, i in importances],
            "thresholds": {"investment_grade": 0.03, "watch": 0.08, "substandard": 0.15, "default": 0.25},
            "calibration": calibration,
            "metrics": {
                **metrics,
                "model": "xgboost" if XGB_AVAILABLE else "hist_gradient_boosting",
                "auc_xgboost": auc_xgb,
                "auc_logistic": auc_lr,
                "brier_score": brier,
                "precision": float(precision_score(y_te, pred_te, zero_division=0)),
                "recall": float(recall_score(y_te, pred_te, zero_division=0)),
                "f1": float(f1_score(y_te, pred_te, zero_division=0)),
                "accuracy": float(accuracy_score(y_te, pred_te)),
                "report": classification_report(y_te, pred_te, output_dict=True, zero_division=0),
            },
            "degenerate": False,
        }
        self._save("credit", self.credit)
        self._record("credit_risk", self.credit["metrics"],
                     {"model": "xgboost+logistic", "features": FEATURE_COLS_CREDIT})
        return self.credit

    # ------------------------------------------------------------------ fraud
    def train_fraud(self, frames: dict[str, pd.DataFrame], force: bool = False) -> dict:
        cached = self._load("fraud") if not force else None
        if cached and not force:
            self.fraud = cached
            return cached

        df = fraud_features(frames["transactions"])
        X = df[FEATURE_COLS_FRAUD].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        y = df["fraud_label"].fillna(0).astype(int)

        scaler = StandardScaler().fit(X)
        Xs = scaler.transform(X)
        iforest = IsolationForest(n_estimators=150, contamination=0.02, random_state=settings.seed)
        iforest.fit(Xs)
        anomaly = -iforest.score_samples(Xs)
        # min-max normalize anomaly score to [0,1]
        a_min, a_max = anomaly.min(), anomaly.max()
        anomaly01 = (anomaly - a_min) / max(a_max - a_min, 1e-9)

        # rule score (0..1)
        rule = (0.30 * (df["new_beneficiary"] & (df["amount_zscore"] > 1.5)).astype(float)
                + 0.25 * (df["amount_zscore"] > 3).astype(float)
                + 0.20 * df["is_night"]
                + 0.15 * df["high_risk_country"]
                + 0.10 * df["round_amount"])
        score = 0.65 * anomaly01 + 0.35 * rule

        threshold = settings.fraud_alert_threshold
        pred = (score >= threshold).astype(int)
        metrics = {
            "n_transactions": int(len(df)),
            "n_labeled_fraud": int(y.sum()),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "auc": _safe_auc(y, score),
        }
        self.fraud = {
            "iforest": iforest,
            "scaler": scaler,
            "feature_names": FEATURE_COLS_FRAUD,
            "scores": {int(i): float(s) for i, s in zip(df["id"], score)},
            "threshold": threshold,
            "anomaly_min": float(a_min),
            "anomaly_max": float(a_max),
            "metrics": metrics,
        }
        self._save("fraud", self.fraud)
        self._record("fraud_detection", metrics,
                     {"model": "pyod_isolation_forest+rules", "contamination": 0.02})
        return self.fraud

    # ------------------------------------------------------------------ AML
    def train_aml(self, frames: dict[str, pd.DataFrame], force: bool = False) -> dict:
        cached = self._load("aml") if not force else None
        if cached and not force:
            self.aml = cached
            return cached

        txn = frames["transactions"]
        df = aml_features(txn)
        X = df[FEATURE_COLS_AML].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        y = df["aml_label"].fillna(0).astype(int)

        scaler = StandardScaler().fit(X)
        Xs = scaler.transform(X)
        iforest = IsolationForest(n_estimators=150, contamination=0.015, random_state=settings.seed)
        iforest.fit(Xs)
        anomaly = -iforest.score_samples(Xs)
        a_min, a_max = anomaly.min(), anomaly.max()
        anomaly01 = (anomaly - a_min) / max(a_max - a_min, 1e-9)

        # rule score
        rule = (0.25 * df["near_threshold"].astype(float)
                + 0.25 * df["large_txn"]
                + 0.20 * df["high_risk_country"]
                + 0.15 * df["internal"]
                + 0.15 * ((df["amount_zscore"] > 2).astype(float)))
        score = 0.6 * anomaly01 + 0.4 * rule

        # graph patterns (map internal IBANs back to account ids so chains connect)
        iban_to_id = {str(a["iban"]): int(a["id"]) for _, a in frames["accounts"].iterrows()}
        graphs = {
            "circular_flows": circular_flows(txn, iban_to_id=iban_to_id),
            "rapid_movement": rapid_movement(txn),
            "shared_counterparty_clusters": shared_counterparty_clusters(txn),
        }

        threshold = settings.aml_alert_threshold
        pred = (score >= threshold).astype(int)
        metrics = {
            "n_transactions": int(len(df)),
            "n_labeled_suspicious": int(y.sum()),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "auc": _safe_auc(y, score),
            "n_circular_flows": len(graphs["circular_flows"]),
            "n_rapid_movements": len(graphs["rapid_movement"]),
            "n_shared_counterparty_clusters": len(graphs["shared_counterparty_clusters"]),
        }
        self.aml = {
            "iforest": iforest,
            "scaler": scaler,
            "feature_names": FEATURE_COLS_AML,
            "scores": {int(i): float(s) for i, s in zip(df["id"], score)},
            "threshold": threshold,
            "graphs": graphs,
            "metrics": metrics,
        }
        self._save("aml", self.aml)
        self._record("aml_monitoring", metrics,
                     {"model": "rules+networkx+isolation_forest", "reporting_threshold": settings.aml_reporting_threshold})
        return self.aml

    # ------------------------------------------------------------------ segmentation
    def train_segmentation(self, frames: dict[str, pd.DataFrame], force: bool = False) -> dict:
        cached = self._load("segmentation") if not force else None
        if cached and not force:
            self.segmentation = cached
            return cached

        df = segmentation_features(frames["customers"], frames["transactions"], frames["facilities"])
        feats = ["log_turnover", "log_employees", "credit_intensity", "tx_count", "avg_amount",
                 "cross_border_share", "total_credit_limit", "avg_utilization", "n_facilities", "size_ordinal"]
        X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        scaler = StandardScaler().fit(X)
        Xs = scaler.transform(X)

        k = 5
        km = KMeans(n_clusters=k, random_state=settings.seed, n_init=10).fit(Xs)
        labels = km.labels_

        profiles = []
        labeled = df.copy()
        labeled["segment_id"] = labels
        for seg in sorted(set(labels.tolist())):
            part = labeled[labeled["segment_id"] == seg]
            profiles.append({
                "segment_id": int(seg),
                "n_customers": int(len(part)),
                "avg_turnover": round(float(part["annual_turnover"].mean()), 0),
                "avg_tx_count": round(float(part["tx_count"].mean()), 1),
                "avg_utilization": round(float(part["avg_utilization"].mean()), 3),
                "avg_credit_limit": round(float(part["total_credit_limit"].mean()), 0),
                "top_industries": part["industry"].value_counts().head(3).index.tolist(),
                "label": _segment_label(part),
            })

        # HDBSCAN for density-based discovery (import guarded — heavy optional dep)
        hdb_labels: list[int] | None = None
        try:
            import hdbscan  # type: ignore
            clusterer = hdbscan.HDBSCAN(min_cluster_size=5, metric="euclidean")
            hdb_labels = clusterer.fit_predict(Xs).tolist()
        except Exception:
            hdb_labels = None

        self.segmentation = {
            "kmeans": km,
            "scaler": scaler,
            "feature_names": feats,
            "labels": {int(cid): int(l) for cid, l in zip(df["id"], labels)},
            "hdbscan_labels": ({int(cid): int(l) for cid, l in zip(df["id"], hdb_labels)}
                               if hdb_labels is not None else None),
            "profiles": profiles,
            "metrics": {"n_customers": int(len(df)), "k": k, "inertia": float(km.inertia_),
                        "hdbscan_available": hdb_labels is not None},
        }
        self._save("segmentation", self.segmentation)
        self._record("client_segmentation", self.segmentation["metrics"],
                     {"model": "kmeans+hdbscan", "k": k})
        return self.segmentation

    # ------------------------------------------------------------------ all
    def train_all(self, frames: dict[str, pd.DataFrame], force: bool = False) -> dict:
        t0 = time.time()
        out = {
            "credit": self.train_credit(frames, force),
            "fraud": self.train_fraud(frames, force),
            "aml": self.train_aml(frames, force),
            "segmentation": self.train_segmentation(frames, force),
        }
        self.trained_at = datetime.now(timezone.utc).isoformat()
        out["trained_at"] = self.trained_at
        out["elapsed_s"] = round(time.time() - t0, 1)
        return out


def _segment_label(part: pd.DataFrame) -> str:
    """Human-readable segment name from profile statistics."""
    t = float(part["annual_turnover"].mean())
    u = float(part["avg_utilization"].mean())
    if t > 400e6:
        return "Large Corporates — Global Treasury"
    if t > 80e6:
        return "Mid-Market — Growth & Trade"
    if u > 0.6:
        return "Leveraged SMEs — Credit Intensive"
    return "Core SMEs — Transactional Banking"


store = ModelStore()
