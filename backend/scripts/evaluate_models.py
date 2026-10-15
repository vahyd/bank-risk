"""Reproducible model evaluation report.

Run from backend/:
    .venv/bin/python scripts/evaluate_models.py

Writes evaluation metrics to data/evaluation_report.json and prints a summary.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.data.loader import run_pipeline  # noqa: E402
from app.ml.models import store  # noqa: E402


def main() -> None:
    frames = run_pipeline()
    store.train_all(frames, force=True)

    report = {
        "credit_risk": store.credit.get("metrics", {}),
        "fraud_detection": store.fraud.get("metrics", {}),
        "aml_monitoring": store.aml.get("metrics", {}),
        "client_segmentation": store.segmentation.get("metrics", {}),
        "trained_at": store.trained_at,
    }
    os.makedirs(settings.data_dir, exist_ok=True)
    out_path = os.path.join(settings.data_dir, "evaluation_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("=== MODEL EVALUATION REPORT ===")
    for name, metrics in report.items():
        if isinstance(metrics, dict):
            keep = {k: v for k, v in metrics.items() if k in
                    ("auc_xgboost", "auc_logistic", "brier_score", "precision", "recall", "f1",
                     "auc", "inertia", "default_rate", "n_labeled_fraud", "n_labeled_suspicious")}
            print(f"{name}: {keep}")
    print(f"report written to {out_path}")


if __name__ == "__main__":
    main()
