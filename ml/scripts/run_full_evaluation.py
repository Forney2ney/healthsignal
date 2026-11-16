"""Full mandatory evaluation for the Veritas Health track.

Produces, for every dataset, a single evaluation record containing:
  * model selection by stratified CV on the TRAIN split only,
  * two simple baselines (stratified-random and most-frequent) on the same split,
  * held-out test metrics with precision / recall / specificity / F1 / ROC-AUC /
    PR-AUC / Brier / confusion matrix, with false positives and false negatives
    reported SEPARATELY,
  * subgroup performance where the dataset carries a demographic attribute,
  * concrete failure cases (misclassified test records with their feature values),
  * dataset limitations, class imbalance and generalisability notes.

Deterministic: seed 42. Writes ml/artifacts/<key>/model_card.json.
"""
import joblib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap  # noqa: F401

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from healthsignal_ml.datasets import DATASETS, load_dataset

SEED = 42
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

SUBGROUPS = {
    "heart": {"column": "sex", "groups": {"male": "1", "female": "0"}},
    "ilpd": {"column": "gender", "groups": {"male": "Male", "female": "Female"}},
    "pima": {"column": "age", "groups": {"age<40": (0, 40), "age>=40": (40, 130)}},
    "ckd": {"column": "age", "groups": {"age<55": (0, 55), "age>=55": (55, 130)}},
}


def build_preprocessor(numeric_cols, categorical_cols):
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                              ("scale", StandardScaler())]), numeric_cols),
            ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                              ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]),
             categorical_cols),
        ],
        remainder="drop",
    )


def candidates(seed):
    models = {
        "logistic_regression": LogisticRegression(max_iter=5000, C=1.0),
        "random_forest": RandomForestClassifier(n_estimators=500, min_samples_leaf=3,
                                                random_state=seed, n_jobs=-1),
        "hist_gradient_boosting": HistGradientBoostingClassifier(random_state=seed),
    }
    try:
        from lightgbm import LGBMClassifier
        models["lightgbm"] = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                                            random_state=seed, verbosity=-1, n_jobs=-1)
    except Exception:
        pass
    return models


def spec_from_cm(cm):
    tn, fp, fn, tp = cm.ravel()
    return float(tn / (tn + fp)) if (tn + fp) else float("nan")


def metrics_block(y, proba, pred):
    cm = confusion_matrix(y, pred)
    tn, fp, fn, tp = cm.ravel()
    return {
        "n": int(len(y)),
        "accuracy": float((pred == y).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(y, pred, zero_division=0)),
        "specificity": float(spec_from_cm(cm)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, proba)),
        "pr_auc": float(average_precision_score(y, proba)),
        "brier": float(brier_score_loss(y, proba)),
        "confusion_matrix": {"true_negative": int(tn), "false_positive": int(fp),
                             "false_negative": int(fn), "true_positive": int(tp)},
        "false_positives": int(fp),
        "false_negatives": int(fn),
    }


def evaluate(key):
    df, target, dspec = load_dataset(key)
    y = df[target].astype(int).to_numpy()
    X = df.drop(columns=[target])
    numeric_cols = list(X.select_dtypes(include=["number"]).columns)
    categorical_cols = [c for c in dspec.categorical_columns if c in X.columns]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=SEED)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    selection, fitted = [], {}
    for name, model in candidates(SEED).items():
        pipe = Pipeline([("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
                         ("model", model)])
        res = cross_validate(pipe, X_train, y_train, cv=cv,
                             scoring=["roc_auc", "average_precision"], n_jobs=1)
        selection.append({"model": name,
                          "cv_roc_auc_mean": float(np.mean(res["test_roc_auc"])),
                          "cv_roc_auc_std": float(np.std(res["test_roc_auc"])),
                          "cv_pr_auc_mean": float(np.mean(res["test_average_precision"]))})
        fitted[name] = pipe

    best = max(selection, key=lambda r: r["cv_roc_auc_mean"])["model"]
    best_pipe = fitted[best]
    best_pipe.fit(X_train, y_train)
    proba = best_pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    baselines = {}
    for bname, bmodel in {
        "baseline_stratified_random": DummyClassifier(strategy="stratified", random_state=SEED),
        "baseline_most_frequent": DummyClassifier(strategy="most_frequent"),
    }.items():
        bpipe = Pipeline([("preprocess", build_preprocessor(numeric_cols, categorical_cols)),
                          ("model", bmodel)])
        bpipe.fit(X_train, y_train)
        bproba = bpipe.predict_proba(X_test)[:, 1]
        bpred = (bproba >= 0.5).astype(int)
        bm = metrics_block(y_test, bproba, bpred)
        baselines[bname] = {"roc_auc": bm["roc_auc"], "pr_auc": bm["pr_auc"], "f1": bm["f1"],
                            "recall": bm["recall_sensitivity"], "specificity": bm["specificity"],
                            "false_positives": bm["false_positives"],
                            "false_negatives": bm["false_negatives"],
                            "note": "DummyClassifier: no learning from features, only class rates"}

    main = metrics_block(y_test, proba, pred)

    subgroup = {}
    ss = SUBGROUPS.get(key)
    if ss and ss["column"] in X_test.columns:
        col = X_test[ss["column"]]
        for gname, rule in ss["groups"].items():
            if isinstance(rule, tuple):
                numeric = pd.to_numeric(col, errors="coerce")
                mask = ((numeric >= rule[0]) & (numeric < rule[1])).to_numpy()
            else:
                # Numeric group keys (e.g. heart `sex` = 1/0) must be compared
                # numerically: pandas stores them as floats (1.0), so a plain
                # string comparison against "1" silently matched nothing.
                try:
                    target_value = float(rule)
                except (TypeError, ValueError):
                    mask = (col.astype(str) == rule).to_numpy()
                else:
                    mask = (pd.to_numeric(col, errors="coerce") == target_value).to_numpy()
            if mask.sum() == 0 or len(set(y_test[mask].tolist())) < 2:
                continue
            proba_g, y_g = proba[mask], y_test[mask]
            pred_g = (proba_g >= 0.5).astype(int)
            gm = metrics_block(y_g, proba_g, pred_g)
            subgroup[gname] = {"n": gm["n"], "roc_auc": gm["roc_auc"],
                               "recall_sensitivity": gm["recall_sensitivity"],
                               "specificity": gm["specificity"],
                               "false_negatives": gm["false_negatives"],
                               "false_positives": gm["false_positives"],
                               "positive_rate": float(y_g.mean())}
        if subgroup:
            subgroup["_interpretation_note"] = (
                "Small subgroup sizes mean wide uncertainty; these figures are reported for "
                "transparency and MUST NOT be used to claim the model is fair.")

    feature_names = list(best_pipe.named_steps["preprocess"].get_feature_names_out())
    X_train_t = best_pipe.named_steps["preprocess"].transform(X_train)
    try:
        feature_means = [float(v) for v in np.asarray(X_train_t.mean(axis=0)).ravel()]
    except Exception:
        feature_means = [0.0] * len(feature_names)

    # For linear models the exact per-feature attribution is
    # coef_j * (x_j - train_mean_j) (same formula used at serve time).
    linear_model = best_pipe.named_steps["model"]
    coefficients = (np.asarray(linear_model.coef_).ravel()
                    if hasattr(linear_model, "coef_") else None)

    test_rows = X_test.reset_index(drop=True)
    failures = {"false_negatives": [], "false_positives": []}
    for i in range(len(y_test)):
        bucket = None
        if y_test[i] == 1 and pred[i] == 0 and len(failures["false_negatives"]) < 5:
            bucket = "false_negatives"
        elif y_test[i] == 0 and pred[i] == 1 and len(failures["false_positives"]) < 5:
            bucket = "false_positives"
        if bucket is None:
            continue
        row = test_rows.iloc[i]
        record = {
            "model_probability": round(float(proba[i]), 4),
            "true_label": int(y_test[i]),
            "features": {c: (None if pd.isna(row[c]) else
                             (row[c].item() if hasattr(row[c], "item") else row[c]))
                         for c in X.columns},
        }
        if coefficients is not None:
            row_t = best_pipe.named_steps["preprocess"].transform(test_rows.iloc[[i]])
            contributions = coefficients * (np.asarray(row_t).ravel() - np.asarray(feature_means))
            order = np.argsort(-np.abs(contributions))[:5]
            record["top_contributions"] = [
                {"feature": feature_names[j], "contribution": round(float(contributions[j]), 4)}
                for j in order
            ]
            mass = float(np.abs(contributions).sum())
            if mass > 0:
                record["top5_share_of_absolute_contribution"] = round(
                    float(np.abs(contributions[order]).sum() / mass), 4)
        failures[bucket].append(record)
    failures["_note"] = (
        "Held-out test records the selected model got wrong, with the raw dataset feature "
        "values (null = genuinely missing in the source). `top_contributions` are exact linear "
        "SHAP values (coefficient x deviation from the train-split mean, in transformed feature "
        "space); a positive value pushes the model toward the positive class. They describe model "
        "behaviour, not causal effects.")

    card = {
        "model_name": f"healthsignal-{key}-v1",
        "model_type": f"sklearn Pipeline[{best}]",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prediction_task": dspec.purpose,
        "dataset": {
            "name": dspec.name,
            "source_url": dspec.source_url,
            "documented_records": dspec.n_records,
            "loaded_rows": int(len(df)),
            "licence": dspec.licence,
            "download_requirement": dspec.download_requirement,
            "known_limitations": dspec.known_limitations,
        },
        "target": target,
        "class_balance": {
            "positive_rate_all_data": round(float(y.mean()), 4),
            "positive_rate_train": round(float(y_train.mean()), 4),
            "positive_rate_test": round(float(y_test.mean()), 4),
            "note": "Stratified split keeps proportions comparable; imbalance is reported, not fixed.",
        },
        "features_provided": {"numeric": numeric_cols, "categorical": categorical_cols},
        "engineered_features": feature_names,
        "methodology": {
            "split": "stratified 70/30, seed 42; test split touched once, after model selection",
            "model_selection": selection,
            "selected_model": best,
            "selection_rule": "highest mean ROC-AUC in 5-fold stratified CV on the train split",
            "preprocessing": ("median imputation + standard scaling for numeric columns; most-frequent "
                              "imputation + one-hot encoding for categorical columns; all inside the "
                              "pipeline, refitted inside every CV fold (no leakage)"),
            "held_out_test_metrics": main,
            "baselines_on_same_test_split": baselines,
            "subgroup_performance": subgroup,
            "failure_cases": failures,
            "linear_explanation_baseline": {
                "note": "train-split means of transformed features, for exact linear SHAP",
                "feature_names": feature_names,
                "feature_means": feature_means,
            },
        },
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "numpy": np.__version__, "pandas": pd.__version__},
        "intended_use": ("Research and educational risk-indicator prototype. Output is a dataset-specific "
                         "statistical indicator, NOT a validated individual probability of disease and "
                         "NOT a diagnosis. This project is a prototype and is not medical advice."),
        "limitations": dspec.known_limitations + [
            "No external validation: all metrics apply to this cohort only.",
            "Small datasets make confidence intervals wide.",
            "Baseline comparison uses the same split; a stratified-random baseline already obtains "
            "non-trivial scores, so ROC-AUC must be read against it.",
        ],
    }
    out_dir = ARTIFACTS / key
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipe, out_dir / "model.joblib")
    return card, main, selection, best, baselines


def run(keys=None):
    """Train, save and write an enriched card for each requested dataset."""
    keys = list(keys) if keys else list(DATASETS)
    summary = {}
    for key in keys:
        card, main, selection, best, baselines = evaluate(key)
        out = ARTIFACTS / key
        out.mkdir(parents=True, exist_ok=True)
        (out / "model_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
        base_roc = baselines["baseline_stratified_random"]["roc_auc"]
        subgroup_names = sorted(k for k in card["methodology"]["subgroup_performance"]
                                if not k.startswith("_"))
        print(f"[{key}] {best} test ROC-AUC {main['roc_auc']:.4f} "
              f"(baseline {base_roc:.4f}) PR-AUC {main['pr_auc']:.4f} "
              f"FP {main['false_positives']} FN {main['false_negatives']} "
              f"subgroups={subgroup_names or 'none'}")
        summary[key] = {"model": best, "roc_auc": main["roc_auc"], "pr_auc": main["pr_auc"],
                        "f1": main["f1"], "recall": main["recall_sensitivity"],
                        "specificity": main["specificity"], "fp": main["false_positives"],
                        "fn": main["false_negatives"], "baseline_roc_auc": base_roc,
                        "n_test": main["n"], "subgroups": subgroup_names}
    (ARTIFACTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("summary ->", ARTIFACTS / "summary.json")
    return summary


if __name__ == "__main__":
    run(sys.argv[1:] or None)