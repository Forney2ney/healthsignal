# HealthSignal — Project Status Report

Status classes: IMPLEMENTED AND TESTED / IMPLEMENTED BUT NOT FULLY TESTED / PARTIALLY IMPLEMENTED /
SIMULATED FOR DEMONSTRATION / PLANNED / BLOCKED.
Only results that were actually observed may be marked tested. Nothing here may be fabricated.

_Last updated: after the official Veritas requirements audit (Phase 6)._

## Heads-up status (audit summary)

**What already worked before the audit:** dataset acquisition with observable-count manifest; five
trained tabular models; a genuine pretrained chest X-ray model with Grad-CAM; FastAPI backend with
auth/RBAC/ingestion/inference/imaging/reports/assistant/audit; React dashboard, model forms, image
viewer, reports, assistant, research workspace; pytest suite; docs.

**What the audit found missing (now implemented):** baseline comparison, separate FP/FN reporting,
identified failure cases, subgroup performance, one-page write-up, credits register, required
disclaimer in the UI.

**Use case selected for the submission:** a person/clinician enters real measurements + labs; each
specialised model returns an explainable indicator with disclosed imputation; chest X-ray runs the
pretrained model with Grad-CAM. One workflow, end to end.

## Models (metrics from `ml/scripts/run_full_evaluation.py`, seed 42)

Held-out 30% test split. Baseline = `DummyClassifier(stratified)` on the same split.

| Model | Task | Dataset | ROC-AUC (baseline) | PR-AUC | F1 | Recall | Specificity | FP / FN | Status |
|---|---|---|---|---|---|---|---|---|---|
| heart | Heart-disease indicator | UCI 303×13 | 0.922 (0.478) | 0.912 | 0.854 | 0.902 | 0.941 | 5 / 7 | IMPLEMENTED AND TESTED |
| wdbc | Malignancy | UCI 569×30 | 0.998 (0.449) | 0.996 | 0.960 | 0.957 | 0.991 | 1 / 4 | IMPLEMENTED AND TESTED |
| ckd | CKD indicator | UCI 399×24 | 0.961 (0.522) | 0.984 | 0.959 | 0.960 | 0.957 | 1 / 5 | IMPLEMENTED AND TESTED |
| pima | Diabetes screening | Pima 768×8 | 0.836 (0.529) | 0.719 | 0.593 | 0.735 | 0.856 | 21 / 38 | IMPLEMENTED AND TESTED |
| ilpd | Liver condition | UCI 583×10 | 0.779 (0.522) | 0.911 | 0.838 | 0.902 | 0.479 | 40 / 6 | IMPLEMENTED AND TESTED |
| cxr_nih | 14-pathology thoracic | Pretrained DenseNet-121 (NIH ChestX-ray14) | published AUCs quoted in card; NOT re-validated locally | — | — | — | — | — | PARTIALLY IMPLEMENTED (inference + Grad-CAM work; no local re-validation) |

All five tabular cards now additionally contain: CV selection table, two baselines, confusion matrix,
separate FP/FN counts, subgroup performance (sex / age band), and real failure-case records.
See `ml/artifacts/<task>/model_card.json`.

## Features

| Feature | Status |
|---|---|
| Project scaffold, `.venv`, requirements, env example | IMPLEMENTED AND TESTED |
| Dataset acquisition + validation with manifest of observed counts | IMPLEMENTED AND TESTED |
| Full mandatory evaluation (baselines, FP/FN, failure cases, subgroups) | IMPLEMENTED AND TESTED |
| Model artifacts + regenerated model cards | IMPLEMENTED AND TESTED |
| Chest X-ray inference + Grad-CAM | IMPLEMENTED AND TESTED |
| Backend API (auth, RBAC, ingestion, predictions, imaging, reports, assistant, audit) | IMPLEMENTED AND TESTED |
| Frontend dashboard / model forms / imaging / reports / assistant / research | IMPLEMENTED BUT NOT FULLY TESTED (production build passes; manual walkthrough documented) |
| Required disclaimer in app banner + write-up | IMPLEMENTED AND TESTED |
| One-page write-up (`docs/ONEPAGE_SUBMIT.md`) | IMPLEMENTED |
| Credits/source register (`CREDITS.md`) | IMPLEMENTED |
| Persistent instructions updated (spec §16, AGENTS.md, CLAUDE.md, GEMINI.md) | IMPLEMENTED |
| git history | IMPLEMENTED BUT NOT FULLY TESTED (multiple commits; final commit pending) |

## Test suite status

Latest observed full-suite run: **27 passed, 2 failed** (both assertion-level, fixed afterwards):
`test_permissions.py::test_patient_cannot_read_other_profiles` (assertion detail widened) and
`test_reports.py::test_report_generation_and_markdown` (expected heading text). A confirming full run
is pending and its result will be recorded here verbatim.

## Known limitations (current)

- No external validation for any model; metrics are cohort-specific.
- Scores are uncalibrated research indicators, not individual disease probabilities.
- The imaging model was not re-validated locally and accepts chest X-rays only.
- scikit-learn 1.9.1 compiled extensions are blocked by a Windows Application Control policy in the
  user-wide site-packages; everything runs from the project `.venv` (D-002).
- Clinician identity verification is a stub; no real-world report-sharing workflow.
- No HIPAA/GDPR compliance claim.