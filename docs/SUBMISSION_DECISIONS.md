# HealthSignal — Submission decisions (Veritas AI Hackathon 2026)

Append to (or read alongside) `DECISIONS.md`. These record the audit findings and the changes made
when the official competition requirements arrived.

## D-013 — Official Veritas requirements audited; mandatory evaluation implemented

**Observed (audit).** The project already had: 5 trained tabular models with held-out metrics, a working
pretrained chest X-ray pipeline with Grad-CAM, a FastAPI + React application, a pytest suite, dashboard /
model forms / imaging / reports / assistant / research pages, and documentation. What it did NOT have,
which the organisers require: a baseline comparison, false positives and false negatives reported
separately, identified failure cases, subgroup performance, one-page write-up, credits register.

**Decision.** Added `ml/scripts/run_full_evaluation.py`, which for every dataset produces, in one
deterministic run (seed 42):

- model selection by 5-fold stratified CV on the train split only,
- `DummyClassifier(stratified)` and `DummyClassifier(most_frequent)` baselines on the SAME held-out test
  split,
- accuracy, balanced accuracy, precision, recall/sensitivity, specificity, F1, ROC-AUC, PR-AUC, Brier and
  the confusion matrix, with `false_positives` and `false_negatives` as separate top-level numbers,
- subgroup performance where a demographic column exists (age band for pima/ckd, sex for ILPD;
  heart and WDBC have no usable demographic attribute in their processed features),
  with an explicit "this is not a fairness claim" note,
- the actual misclassified test records with raw feature values.

Model cards were regenerated with this script. No metric in the submission is hand-transcribed.

**Rationale.** The organisers make baseline + FP/FN + failure analysis mandatory. Producing them from a
script keeps the numbers reproducible and honest.

## D-014 — Required disclaimer promoted to a first-class UI element

The exact sentence **"This project is a prototype and is not medical advice."** now appears in the
global application banner (`frontend/src/App.tsx`) and verbatim in `docs/ONEPAGE_SUBMIT.md`.

## D-015 — Focus of the submission

The submission demonstrates ONE end-to-end workflow rather than the full platform breadth: a user
(clinician-adjacent individual or researcher) enters real clinical measurements and labs, each
specialised model returns an indicator with per-feature SHAP explanation, disclosed imputation and its
own dataset/metrics/caveats; chest X-ray runs the genuine pretrained model with Grad-CAM. Additional
models are available but are not load-bearing for the demo.