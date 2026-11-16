"""Model registry: loads tabular artifacts + model cards, exposes feature request schemas.

The registry derives a human-facing feature schema from each dataset's columns so
the UI can render accurate input forms and disclose which features are imputed
when the user leaves them blank (missing stays missing; we never fabricate).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"

# Domain shown in the UI: system, human label, unit and plausible range per raw
# dataset feature. Feature names match the loaders in datasets.py exactly.
FEATURE_META: dict[str, dict[str, dict[str, Any]]] = {
    "heart": {
        "age": {"label": "Age (years)", "unit": "years", "min": 20, "max": 100, "step": 1, "hint": "Age in years"},
        "sex": {"label": "Sex", "unit": "", "options": {"1": "Male", "0": "Female"}, "hint": "As recorded in the source dataset"},
        "cp": {"label": "Chest pain type", "unit": "", "options": {"1": "Typical angina", "2": "Atypical angina", "3": "Non-anginal pain", "4": "Asymptomatic"}, "hint": "Chest pain classification at examination"},
        "trestbps": {"label": "Resting blood pressure (mmHg)", "unit": "mmHg", "min": 80, "max": 220, "step": 1, "hint": "Resting systolic blood pressure on admission"},
        "chol": {"label": "Serum cholesterol (mg/dL)", "unit": "mg/dL", "min": 100, "max": 600, "step": 1, "hint": "Total serum cholesterol"},
        "fbs": {"label": "Fasting blood sugar > 120 mg/dL", "unit": "", "options": {"1": "Yes", "0": "No"}, "hint": "Whether fasting glucose exceeded 120 mg/dL"},
        "restecg": {"label": "Resting ECG result", "unit": "", "options": {"0": "Normal", "1": "ST-T wave abnormality", "2": "Probable left ventricular hypertrophy"}, "hint": "Resting electrocardiograph category"},
        "thalach": {"label": "Max heart rate achieved (bpm)", "unit": "bpm", "min": 60, "max": 220, "step": 1, "hint": "Maximum heart rate during exercise test"},
        "exang": {"label": "Exercise-induced angina", "unit": "", "options": {"1": "Yes", "0": "No"}, "hint": "Chest pain provoked by exercise"},
        "oldpeak": {"label": "ST depression vs rest", "unit": "mm", "min": 0, "max": 7, "step": 0.1, "hint": "Exercise-induced ST-segment depression"},
        "slope": {"label": "Exercise ST segment slope", "unit": "", "options": {"1": "Upsloping", "2": "Flat", "3": "Downsloping"}, "hint": "Slope of the peak exercise ST segment"},
        "ca": {"label": "Major vessels coloured (0-3)", "unit": "", "options": {"0": "0 vessels", "1": "1 vessel", "2": "2 vessels", "3": "3 vessels"}, "hint": "Fluoroscopy-detected major vessels"},
        "thal": {"label": "Thalassemia test result", "unit": "", "options": {"3": "Normal", "6": "Fixed defect", "7": "Reversible defect"}, "hint": "Thallium stress-test category"},
    },
    "wdbc": {
        f"{stat}_{feat.replace(' ', '_')}": {
            "label": f"{feat.title()} ({stat})", "unit": "value", "min": -10, "max": 10000, "step": 0.0001,
            "hint": "Fine-needle-aspirate image feature; paste from your lab/imaging report",
        }
        for stat, feats in {
            "mean": ["radius", "texture", "perimeter", "area", "smoothness", "compactness",
                     "concavity", "concave points", "symmetry", "fractal dimension"],
            "se": ["radius", "texture", "perimeter", "area", "smoothness", "compactness",
                   "concavity", "concave points", "symmetry", "fractal dimension"],
            "worst": ["radius", "texture", "perimeter", "area", "smoothness", "compactness",
                      "concavity", "concave points", "symmetry", "fractal dimension"],
        }.items()
        for feat in feats
    },
    "ckd": {
        "age": {"label": "Age (years)", "unit": "years", "min": 1, "max": 100, "step": 1, "hint": "Age in years"},
        "bp": {"label": "Blood pressure (mmHg)", "unit": "mmHg", "min": 40, "max": 220, "step": 1, "hint": "Resting blood pressure"},
        "sg": {"label": "Specific gravity", "unit": "", "options": {"1.005": "1.005", "1.010": "1.010", "1.015": "1.015", "1.020": "1.020", "1.025": "1.025"}, "hint": "Urine specific gravity category"},
        "al": {"label": "Albumin in urine", "unit": "", "options": {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}, "hint": "Urine albumin grade"},
        "su": {"label": "Sugar in urine", "unit": "", "options": {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}, "hint": "Urine sugar grade"},
        "rbc": {"label": "Red blood cells (urine)", "unit": "", "options": {"normal": "Normal", "abnormal": "Abnormal"}, "hint": "Urine microscopy"},
        "pc": {"label": "Pus cells (urine)", "unit": "", "options": {"normal": "Normal", "abnormal": "Abnormal"}, "hint": "Urine microscopy"},
        "pcc": {"label": "Pus cell clumps", "unit": "", "options": {"present": "Present", "notpresent": "Not present"}, "hint": "Urine microscopy"},
        "ba": {"label": "Bacteria in urine", "unit": "", "options": {"present": "Present", "notpresent": "Not present"}, "hint": "Urine microbiology"},
        "bgr": {"label": "Blood glucose (mg/dL)", "unit": "mg/dL", "min": 20, "max": 500, "step": 1, "hint": "Random blood glucose"},
        "bu": {"label": "Blood urea (mg/dL)", "unit": "mg/dL", "min": 5, "max": 300, "step": 1, "hint": "Serum urea"},
        "sc": {"label": "Serum creatinine (mg/dL)", "unit": "mg/dL", "min": 0.3, "max": 20, "step": 0.1, "hint": "Serum creatinine"},
        "sod": {"label": "Sodium (mEq/L)", "unit": "mEq/L", "min": 100, "max": 170, "step": 0.1, "hint": "Serum sodium"},
        "pot": {"label": "Potassium (mEq/L)", "unit": "mEq/L", "min": 2, "max": 40, "step": 0.1, "hint": "Serum potassium"},
        "hemo": {"label": "Haemoglobin (g/dL)", "unit": "g/dL", "min": 3, "max": 20, "step": 0.1, "hint": "Blood haemoglobin"},
        "pcv": {"label": "Packed cell volume", "unit": "", "min": 10, "max": 60, "step": 0.1, "hint": "Haematocrit"},
        "wbcc": {"label": "White cell count (cells/cmm)", "unit": "cells/cmm", "min": 1000, "max": 30000, "step": 100, "hint": "White blood cell count"},
        "rbcc": {"label": "Red cell count (millions/cmm)", "unit": "millions/cmm", "min": 2, "max": 8, "step": 0.1, "hint": "Red blood cell count"},
        "htn": {"label": "Hypertension", "unit": "", "options": {"yes": "Yes", "no": "No"}, "hint": "Known hypertension"},
        "dm": {"label": "Diabetes mellitus", "unit": "", "options": {"yes": "Yes", "no": "No"}, "hint": "Known diabetes"},
        "cad": {"label": "Coronary artery disease", "unit": "", "options": {"yes": "Yes", "no": "No"}, "hint": "Known coronary artery disease"},
        "appet": {"label": "Appetite", "unit": "", "options": {"good": "Good", "poor": "Poor"}, "hint": "Self-reported appetite"},
        "pe": {"label": "Pedal oedema", "unit": "", "options": {"yes": "Yes", "no": "No"}, "hint": "Swelling of the ankles"},
        "ane": {"label": "Anaemia", "unit": "", "options": {"yes": "Yes", "no": "No"}, "hint": "Clinician-recorded anaemia"},
    },
    "pima": {
        "pregnancies": {"label": "Pregnancies", "unit": "", "min": 0, "max": 20, "step": 1, "hint": "Number of pregnancies"},
        "glucose": {"label": "Plasma glucose (mg/dL, 2h OGTT)", "unit": "mg/dL", "min": 50, "max": 200, "step": 1, "hint": "Glucose concentration 2 hours into an oral glucose tolerance test"},
        "bloodpressure": {"label": "Diastolic blood pressure (mmHg)", "unit": "mmHg", "min": 30, "max": 130, "step": 1, "hint": "Diastolic blood pressure"},
        "skinfold": {"label": "Triceps skinfold thickness (mm)", "unit": "mm", "min": 5, "max": 100, "step": 0.5, "hint": "Triceps skin fold thickness"},
        "insulin": {"label": "2-hour serum insulin (mu U/mL)", "unit": "mu U/mL", "min": 10, "max": 900, "step": 1, "hint": "Serum insulin at 2 hours"},
        "bmi": {"label": "BMI (kg/m2)", "unit": "kg/m2", "min": 10, "max": 70, "step": 0.1, "hint": "Body mass index"},
        "pedigree": {"label": "Diabetes pedigree function", "unit": "", "min": 0.05, "max": 2.5, "step": 0.001, "hint": "Family-history pedigree score for diabetes"},
        "age": {"label": "Age (years)", "unit": "years", "min": 18, "max": 100, "step": 1, "hint": "Age in years"},
    },
    "ilpd": {
        "age": {"label": "Age (years)", "unit": "years", "min": 1, "max": 100, "step": 1, "hint": "Age in years"},
        "gender": {"label": "Sex", "unit": "", "options": {"Male": "Male", "Female": "Female"}, "hint": "As recorded in the source dataset"},
        "tb": {"label": "Total bilirubin (mg/dL)", "unit": "mg/dL", "min": 0.3, "max": 40, "step": 0.1, "hint": "Serum total bilirubin"},
        "db": {"label": "Direct bilirubin (mg/dL)", "unit": "mg/dL", "min": 0.1, "max": 20, "step": 0.1, "hint": "Serum direct bilirubin"},
        "alkphos": {"label": "Alkaline phosphatase (U/L)", "unit": "U/L", "min": 50, "max": 2000, "step": 1, "hint": "Alkaline phosphatase"},
        "sgpt": {"label": "ALT / SGPT (U/L)", "unit": "U/L", "min": 5, "max": 2000, "step": 1, "hint": "Alanine aminotransferase"},
        "sgot": {"label": "AST / SGOT (U/L)", "unit": "U/L", "min": 5, "max": 2000, "step": 1, "hint": "Aspartate aminotransferase"},
        "tp": {"label": "Total proteins (g/dL)", "unit": "g/dL", "min": 2, "max": 10, "step": 0.1, "hint": "Serum total protein"},
        "albumin": {"label": "Albumin (g/dL)", "unit": "g/dL", "min": 1, "max": 6, "step": 0.1, "hint": "Serum albumin"},
        "ag_ratio": {"label": "Albumin/Globulin ratio", "unit": "", "min": 0.3, "max": 3, "step": 0.01, "hint": "Albumin to globulin ratio"},
    },
}

DOMAIN_META = {
    "heart": {"system": "Cardiovascular", "human_task": "Indicator of heart disease"},
    "wdbc": {"system": "Oncology", "human_task": "Breast mass malignancy indicator"},
    "ckd": {"system": "Kidney", "human_task": "Chronic kidney disease indicator"},
    "pima": {"system": "Metabolic", "human_task": "Diabetes screening indicator"},
    "ilpd": {"system": "Liver", "human_task": "Liver condition indicator"},
}


class ModelHandle:
    def __init__(self, key: str):
        self.key = key
        self.dir = ARTIFACTS_DIR / key
        self.card_path = self.dir / "model_card.json"
        self.model_path = self.dir / "model.joblib"
        self._card = json.loads(self.card_path.read_text(encoding="utf-8"))
        self._model = None

    @property
    def card(self) -> dict:
        return self._card

    @property
    def model(self):
        if self._model is None:
            self._model = joblib.load(self.model_path)
        return self._model

    @property
    def feature_schema(self) -> list[dict]:
        meta = FEATURE_META[self.key]
        out = []
        for name, spec in meta.items():
            out.append({
                "feature": name,
                "label": spec["label"],
                "unit": spec.get("unit", ""),
                "options": spec.get("options"),
                "min": spec.get("min"),
                "max": spec.get("max"),
                "step": spec.get("step"),
                "hint": spec.get("hint", ""),
            })
        return out


def available_models() -> list[str]:
    return [c.parent.name for c in ARTIFACTS_DIR.glob("*/model_card.json") if (c.parent / "model.joblib").exists()]


@lru_cache
def load_model(key: str) -> ModelHandle:
    handle = ModelHandle(key)
    _ = handle.model
    return handle


def coerce_value(feature: str, raw: Any, key: str) -> Any:
    """Convert a form value to the feature's expected dtype without inventing data."""
    meta = FEATURE_META[key][feature]
    if raw is None or raw == "":
        return None
    if "options" in meta:
        options = meta["options"]
        if str(raw) in options:
            return str(raw)
        # tolerate numerically-encoded options arriving as floats (1.0 -> "1")
        try:
            f = float(raw)
            if f.is_integer() and str(int(f)) in options:
                return str(int(f))
        except (TypeError, ValueError):
            pass
        raise ValueError(f"value '{raw}' is not a valid option for {feature}")
    try:
        f = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"value '{raw}' must be numeric for {feature}")
    if meta.get("min") is not None and f < meta["min"]:
        raise ValueError(f"{feature}={f:g} below plausible minimum {meta['min']}")
    if meta.get("max") is not None and f > meta["max"]:
        raise ValueError(f"{feature}={f:g} above plausible maximum {meta['max']}")
    return f


def predict(key: str, values: dict[str, Any]) -> dict:
    """Run inference on raw feature values; missing features are imputed by the
    trained pipeline and reported back (never silently)."""
    handle = load_model(key)
    meta = FEATURE_META[key]
    coerced: dict[str, Any] = {}
    for name, spec in meta.items():
        coerced[name] = coerce_value(name, values.get(name), key)
    X = pd.DataFrame([coerced])[list(meta.keys())]
    proba = float(handle.model.predict_proba(X)[:, 1][0])
    imputed = [k for k, v in coerced.items() if v is None]
    pred = int(proba >= 0.5)

    explanation = None
    try:
        explanation = explain(key, handle, X)
    except Exception as exc:  # explanations must never break predictions
        explanation = None
        print(f"[explain] {key} explanation failed: {exc}")

    card = handle.card
    card_m = card.get("methodology", {})
    metrics = card_m.get("held_out_test_metrics") or card_m.get("final_metrics_on_held_out_test", {})
    # Regenerated cards (run_full_evaluation.py) store class_balance at the top
    # level; older cards stored prevalence inside the metrics block. Support both.
    balance = card.get("class_balance") or card_m.get("class_balance") or {}
    test_prevalence = balance.get(
        "positive_rate_test", metrics.get("positive_class_prevalence_test", 0.0)
    )
    n_test = metrics.get("n_test") or metrics.get("n")
    return {
        "model_key": key,
        "model_name": handle.card["model_name"],
        "prediction_task": handle.card["prediction_task"],
        "probability": proba,
        "prediction": pred,
        "threshold": 0.5,
        "provided_features": {k: v for k, v in coerced.items() if v is not None},
        "missing_features": [k for k, v in coerced.items() if v is None],
        "imputed_features": imputed,
        "explanation": explanation,
        "performance": {
            "roc_auc": metrics["roc_auc"],
            "pr_auc": metrics["pr_auc"],
            "recall": metrics["recall_sensitivity"],
            "specificity": metrics["specificity"],
            "f1": metrics["f1"],
            "brier": metrics["brier"],
            "confusion_matrix": metrics["confusion_matrix"],
            "n_test": n_test,
            "test_prevalence": test_prevalence,
        },
        "interpretation": (
            f"Model score {proba:.1%} on a cohort where {test_prevalence:.1%} "
            "of test cases were positive. This is a statistical indicator from a research model, "
            "NOT a clinically validated probability and NOT a diagnosis."
        ),
        "limitations": handle.card["limitations"],
        "intended_use": handle.card["intended_use"],
    }


def explain(key: str, handle: ModelHandle | None = None, X: pd.DataFrame | None = None) -> dict | None:
    """Local explanation from the fitted model.

    - Tree ensembles: SHAP TreeExplainer (exact).
    - Logistic regression: exact linear SHAP contributions computed as
      coef_j * (x_j - baseline_mean_j); the baseline means are stored in the
      model card from the TRAIN split only.
    """
    import numpy as np

    handle = handle or load_model(key)
    model = handle.model.named_steps["model"]
    pre = handle.model.named_steps["preprocess"]
    Xt = np.asarray(pre.transform(X))
    names = [str(n) for n in pre.get_feature_names_out()]
    mtype = type(model).__name__

    if "TreeEnsemble" in mtype or "RandomForest" in mtype or "GradientBoosting" in mtype or "LGBM" in mtype:
        import shap

        sv = shap.TreeExplainer(model)(Xt)
        vals = sv.values[:, 1] if sv.values.ndim == 3 else sv.values
        row = np.asarray(vals)[0]
        method = f"SHAP TreeExplainer ({mtype})"
    elif "LogisticRegression" in mtype:
        baseline = handle.card["methodology"]["linear_explanation_baseline"]
        means = np.asarray(baseline["feature_means"], dtype=float)
        coef = np.asarray(model.coef_)[0]
        row = coef * (Xt[0] - means)  # contribution to the positive-class logit
        method = f"linear SHAP ({mtype} coeff x feature-minus-train-mean)"
    else:
        return None

    order = sorted(range(len(row)), key=lambda i: abs(row[i]), reverse=True)[:8]
    top = [
        {
            "feature": names[i].replace("num__", "").replace("cat__", ""),
            "contribution": float(row[i]),
            "direction": "increases" if row[i] > 0 else "decreases",
            "value": float(Xt[0, i]) if i < Xt.shape[1] else None,
        }
        for i in order if abs(row[i]) > 1e-9
    ]
    return {
        "method": method,
        "top_features": top,
        "note": "SHAP values describe this model's internal behaviour on this input. "
                "Feature importance is not proof of causation.",
    }