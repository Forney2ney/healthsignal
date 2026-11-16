"""Legacy training pipeline for HealthSignal tabular models.

DEPRECATED for submission artifacts. This module is retained for reference and
for its original baseline-free evaluation. The canonical path is
``ml/scripts/train_all.py``, which delegates to ``ml/scripts/run_full_evaluation.py``
and produces the mandatory baseline comparison, separate FP/FN counts, subgroup
figures and failure records. Cards written by this module alone are incomplete
for the hackathon requirements.

Methodology (documented in every generated model card):
  1. Stratified 70/30 train/test split, seed 42.
  2. Model selection on the TRAIN split only: 5-fold stratified CV, scored by
     ROC-AUC (primary) and PR-AUC (secondary). The test split is never touched
     during selection.
  3. The selected pipeline is refitted on the full train split and evaluated
     once on the held-out test split: accuracy, balanced accuracy, precision,
     recall (sensitivity), specificity, F1, ROC-AUC, PR-AUC, Brier score and
     the full confusion matrix.
  4. All preprocessing (imputation, encoding, scaling) happens inside sklearn
     Pipelines so it is refitted inside every CV fold (no leakage).
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .datasets import DATASETS, DatasetSpec, load_dataset

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"
SEED = 42

# LightGBM is an optional candidate: some environments cannot load it.
try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover
    LGBMClassifier = None


def _candidate_models(seed: int) -> dict:
    models: dict = {
        "logistic_regression": LogisticRegression(max_iter=5000, C=1.0),
        "random_forest": RandomForestClassifier(
            n_estimators=500, min_samples_leaf=3, random_state=seed, n_jobs=-1
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(random_state=seed),
    }
    if LGBMClassifier is not None:
        models["lightgbm"] = LGBMClassifier(
            n_estimators=400, learning_rate=0.05, num_leaves=31,
            random_state=seed, verbosity=-1, n_jobs=-1,
        )
    return models


def _build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                ]),
                numeric_cols,
            ),
            (
                "cat",
                Pipeline([
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                categorical_cols,
            ),
        ],
        remainder="drop",
    )


def _specificity(cm: np.ndarray) -> float:
    tn, fp, fn, tp = cm.ravel()
    return float(tn / (tn + fp)) if (tn + fp) else float("nan")


def evaluate(name: str, df: pd.DataFrame, target: str, spec: DatasetSpec) -> dict:
    y = df[target].astype(int).to_numpy()
    X = df.drop(columns=[target])
    numeric_cols = list(X.select_dtypes(include=["number"]).columns)
    categorical_cols = [c for c in spec.categorical_columns if c in X.columns]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=SEED
    )

    pre = _build_preprocessor(numeric_cols, categorical_cols)
    candidates = _candidate_models(SEED)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    selection_rows = []
    fitted: dict = {}
    for name_m, model in candidates.items():
        pipe = Pipeline([("preprocess", pre), ("model", model)])
        cvres = cross_validate(
            pipe, X_train, y_train, cv=cv,
            scoring=["roc_auc", "average_precision"], n_jobs=1,
        )
        row = {
            "model": name_m,
            "cv_roc_auc_mean": float(np.mean(cvres["test_roc_auc"])),
            "cv_roc_auc_std": float(np.std(cvres["test_roc_auc"])),
            "cv_pr_auc_mean": float(np.mean(cvres["test_average_precision"])),
        }
        selection_rows.append(row)
        fitted[name_m] = pipe

    best = max(selection_rows, key=lambda r: r["cv_roc_auc_mean"])["model"]
    best_pipe = fitted[best]
    best_pipe.fit(X_train, y_train)
    proba = best_pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    cm = confusion_matrix(y_test, pred)
    metrics = {
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "accuracy": float((pred == y_test).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(y_test, pred, zero_division=0)),
        "specificity": _specificity(cm),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "pr_auc": float(average_precision_score(y_test, proba)),
        "brier": float(brier_score_loss(y_test, proba)),
        "confusion_matrix": cm.tolist(),
        "positive_class_prevalence_train": float(y_train.mean()),
        "positive_class_prevalence_test": float(y_test.mean()),
        "decision_threshold": 0.5,
    }

    feature_names = list(best_pipe.named_steps["preprocess"].get_feature_names_out())
    # Baseline for linear explanations: transformed-feature means over the TRAIN split only
    # (never the test split), needed to compute exact linear SHAP contributions at serve time.
    X_train_t = best_pipe.named_steps["preprocess"].transform(X_train)
    try:
        feature_means = [float(v) for v in np.asarray(X_train_t.mean(axis=0)).ravel()]
    except Exception:
        feature_means = [0.0] * len(feature_names)
    card = {
        "model_name": f"healthsignal-{name}-v1",
        "model_type": f"sklearn Pipeline[{best}]",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prediction_task": spec.purpose,
        "dataset": {
            "name": spec.name,
            "source_url": spec.source_url,
            "documented_records": spec.n_records,
            "licence": spec.licence,
            "download_requirement": spec.download_requirement,
            "known_limitations": spec.known_limitations,
        },
        "target": spec.target_column,
        "features_provided": {"numeric": numeric_cols, "categorical": categorical_cols},
        "engineered_features": feature_names,
        "methodology": {
            "split": "stratified 70/30, seed 42",
            "model_selection": "5-fold stratified CV on the train split; primary metric ROC-AUC, secondary PR-AUC; test split unused during selection",
            "candidates": [r["model"] for r in selection_rows],
            "selection_table": selection_rows,
            "preprocessing": "median imputation + standard scaling for numeric; most-frequent imputation + one-hot encoding for categorical; all inside the CV fold",
            "linear_explanation_baseline": {
                "note": "train-split means of transformed features, used for exact linear SHAP contributions",
                "feature_names": feature_names,
                "feature_means": feature_means,
            },
            "final_metrics_on_held_out_test": metrics,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "intended_use": (
            "Research and educational risk-indicator prototype. Output is a dataset-specific "
            "statistical indicator, NOT a validated individual probability of disease and NOT a diagnosis."
        ),
        "limitations": spec.known_limitations + [
            "No external validation was performed; metrics apply to this cohort only.",
            "Small datasets make confidence intervals wide.",
        ],
    }

    out_dir = ARTIFACTS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipe, out_dir / "model.joblib")
    (out_dir / "model_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card


def run_all(keys: list[str] | None = None) -> dict:
    keys = keys or list(DATASETS)
    summaries = {}
    for key in keys:
        df, target, spec = load_dataset(key)
        card = evaluate(key, df, target, spec)
        m = card["methodology"]["final_metrics_on_held_out_test"]
        summaries[key] = {
            "model": card["model_type"],
            "roc_auc": round(m["roc_auc"], 4),
            "pr_auc": round(m["pr_auc"], 4),
            "f1": round(m["f1"], 4),
            "recall": round(m["recall_sensitivity"], 4),
            "brier": round(m["brier"], 4),
        }
        print(f"[{key}] {card['model_type']} roc_auc={m['roc_auc']:.4f} pr_auc={m['pr_auc']:.4f} f1={m['f1']:.4f}")
    return summaries