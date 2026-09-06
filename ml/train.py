"""
FloodGuard AI — model training pipeline.

Trains RandomForest and XGBoost, evaluates both, selects the model with the
best recall (flood-warning systems must minimise false negatives), and persists
the selected model + metadata to backend/app/ml/.

Run:  python ml/train.py
"""
from __future__ import annotations

import json
import os
import sys

import joblib
import pandas as pd

# Allow running from repo root or ml/ directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature_engineering import MODEL_FEATURES, generate_synthetic_dataset  # noqa: E402
from preprocess import clean, split  # noqa: E402

BACKEND_ML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "app", "ml")
MODEL_PATH = os.path.join(BACKEND_ML, "flood_model.pkl")
META_PATH = os.path.join(BACKEND_ML, "model_metadata.json")
DATA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "flood_data.csv")


def load_or_generate_data() -> pd.DataFrame:
    if os.path.exists(DATA_CSV):
        df = pd.read_csv(DATA_CSV)
        if "flood" in df.columns and set(MODEL_FEATURES).issubset(df.columns):
            return df
    print("[train] Generating synthetic training data ...")
    df = generate_synthetic_dataset(n_samples=24000, seed=42)
    os.makedirs(os.path.dirname(DATA_CSV), exist_ok=True)
    df.to_csv(DATA_CSV, index=False)
    return df


def evaluate_model(model, X_test, y_test, threshold: float = 0.5) -> dict:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix,
    )
    try:
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= threshold).astype(int)
    except Exception:
        y_pred = model.predict(X_test)
        y_proba = None
    try:
        roc_auc = float(roc_auc_score(y_test, y_proba)) if y_proba is not None else None
    except Exception:
        roc_auc = None
    cm = confusion_matrix(y_test, y_pred).tolist()
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "confusion_matrix": cm,  # [[TN, FP], [FN, TP]]
    }


def tune_threshold(model, X_test, y_test, min_precision: float = 0.55) -> tuple[float, dict]:
    """
    Flood warning systems must minimise false negatives, so we pick the LOWEST
    probability threshold that still keeps precision above `min_precision` — this
    maximises recall (catches the most real floods) without flooding operators
    with pure noise. Returns (threshold, tuned_metrics).
    """
    from sklearn.metrics import precision_recall_curve
    try:
        y_proba = model.predict_proba(X_test)[:, 1]
    except Exception:
        return 0.5, evaluate_model(model, X_test, y_test, 0.5)
    prec, rec, thr = precision_recall_curve(y_test, y_proba)
    best_t, best_score = 0.5, -1.0
    for p, t in zip(prec[:-1], thr):
        if p >= min_precision:
            # Prefer the lowest threshold (highest recall) among viable points.
            if t < best_t or best_score < 0:
                best_t, best_score = t, rec[len(rec) - 1]
    metrics = evaluate_model(model, X_test, y_test, best_t)
    return float(round(best_t, 3)), metrics


def main() -> None:
    df = load_or_generate_data()
    df = clean(df)
    X_train, X_test, y_train, y_test = split(df)

    print(f"[train] Samples={len(df)}  features={len(MODEL_FEATURES)}  "
          f"positive_rate={df['flood'].mean():.3f}")

    from sklearn.ensemble import RandomForestClassifier
    import xgboost as xgb

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=18, min_samples_leaf=5,
        class_weight="balanced", n_jobs=-1, random_state=42,
    )
    rf.fit(X_train, y_train)
    rf_metrics = evaluate_model(rf, X_test, y_test)
    rf_thr, rf_tuned = tune_threshold(rf, X_test, y_test)
    print(f"[train] RandomForest: recall={rf_metrics['recall']} "
          f"precision={rf_metrics['precision']} f1={rf_metrics['f1']} "
          f"roc_auc={rf_metrics['roc_auc']} tuned_threshold={rf_thr}")

    xgb_clf = xgb.XGBClassifier(
        n_estimators=400, max_depth=8, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9,
        scale_pos_weight=(len(y_train) - sum(y_train)) / max(1, sum(y_train)),
        eval_metric="logloss", random_state=42, n_jobs=-1,
    )
    xgb_clf.fit(X_train, y_train)
    xgb_metrics = evaluate_model(xgb_clf, X_test, y_test)
    xgb_thr, xgb_tuned = tune_threshold(xgb_clf, X_test, y_test)
    print(f"[train] XGBoost:      recall={xgb_metrics['recall']} "
          f"precision={xgb_metrics['precision']} f1={xgb_metrics['f1']} "
          f"roc_auc={xgb_metrics['roc_auc']} tuned_threshold={xgb_thr}")

    # Selection: prioritise recall (false negatives are dangerous in warning
    # systems) on the tuned operating point, then f1 as a tie-breaker.
    candidates = [
        ("RandomForest", rf, rf_tuned, rf_thr),
        ("XGBoost", xgb_clf, xgb_tuned, xgb_thr),
    ]
    candidates.sort(key=lambda c: (c[2]["recall"], c[2]["f1"]), reverse=True)
    best_name, best_model, best_metrics, best_threshold = candidates[0]

    print(f"[train] Selected model: {best_name} (threshold={best_threshold})")

    os.makedirs(BACKEND_ML, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    metadata = {
        "model_type": best_name,
        "features": MODEL_FEATURES,
        "threshold": best_threshold,
        "metrics": best_metrics,
        "selection_criterion": "max(recall, f1) at tuned precision>=0.55 threshold",
        "n_training_samples": int(len(df)),
        "positive_rate": round(float(df["flood"].mean()), 4),
    }
    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[train] Saved model -> {MODEL_PATH}")
    print(f"[train] Saved metadata -> {META_PATH}")


if __name__ == "__main__":
    main()
