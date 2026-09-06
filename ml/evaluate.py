"""
FloodGuard AI — standalone evaluation / model analysis entrypoint.

Loads the persisted model, recomputes held-out metrics, prints a per-feature
importance table, and (if installed) dumps a SHAP summary. Used for the
analytics "ML performance" panel and the model_analysis notebook skeleton.
"""
from __future__ import annotations

import json
import os
import sys

import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature_engineering import MODEL_FEATURES  # noqa: E402
from preprocess import clean, split  # noqa: E402

BACKEND_ML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "app", "ml")


def main() -> None:
    model_path = os.path.join(BACKEND_ML, "flood_model.pkl")
    if not os.path.exists(model_path):
        raise SystemExit("Model not found. Run `python ml/train.py` first.")

    model = joblib.load(model_path)
    df = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "flood_data.csv"))
    df = clean(df)
    _, X_test, _, y_test = split(df)

    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                f1_score, roc_auc_score, confusion_matrix)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    print("=== Held-out evaluation ===")
    print(json.dumps(metrics, indent=2))

    try:
        importances = model.feature_importances_
        table = sorted(zip(MODEL_FEATURES, importances), key=lambda x: -x[1])
        print("\n=== Feature importance (top 10) ===")
        for name, imp in table[:10]:
            print(f"  {name:24s} {imp:.4f}")
    except Exception as e:  # pragma: no cover
        print("feature_importances_ unavailable:", e)


if __name__ == "__main__":
    main()
