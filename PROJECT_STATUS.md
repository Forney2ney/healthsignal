# HealthSignal — Project Status Report

Status classes: IMPLEMENTED AND TESTED / IMPLEMENTED BUT NOT FULLY TESTED / PARTIALLY IMPLEMENTED /
SIMULATED FOR DEMONSTRATION / PLANNED / BLOCKED.
Only results that were actually observed may be marked tested. Nothing here may be fabricated.

_Last updated: 2026-11-16 — submission-readiness pass (test fixes, metric reconciliation, clean-clone reproducibility)._

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
| heart | Heart-disease indicator | UCI 303×13 | 0.922 (0.478) | 0.912 | 0.854 | 0.833 | 0.898 | 5 / 7 | IMPLEMENTED AND TESTED |
| wdbc | Malignancy | UCI 569×30 | 0.998 (0.449) | 0.996 | 0.960 | 0.938 | 0.991 | 1 / 4 | IMPLEMENTED AND TESTED |
| ckd | CKD indicator | UCI 399×24 | 0.961 (0.522) | 0.984 | 0.959 | 0.933 | 0.978 | 1 / 5 | IMPLEMENTED AND TESTED |
| pima | Diabetes screening | Pima 768×8 | 0.836 (0.529) | 0.719 | 0.593 | 0.531 | 0.860 | 21 / 38 | IMPLEMENTED AND TESTED |
| ilpd | Liver condition | UCI 583×10 | 0.779 (0.522) | 0.911 | 0.838 | 0.952 | 0.200 | 40 / 6 | IMPLEMENTED AND TESTED |
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

Latest observed full-suite run (2026-11-16, project `.venv`, `pytest tests -q`): **29 passed, 0 failed**,
exit code 0. Both previously failing tests were fixed:
`test_reports.py::test_report_generation_and_markdown` (expected heading text) and
`test_permissions.py::test_patient_cannot_read_other_profiles`, whose duplicate import of
`tests.conftest` reset `app.dependency_overrides[get_db]` to the fallback database and produced a 401.
The test now creates its helper user locally instead of re-importing conftest.

## Known limitations (current)

- No external validation for any model; metrics are cohort-specific.
- Scores are uncalibrated research indicators, not individual disease probabilities.
- The imaging model was not re-validated locally and accepts chest X-rays only.
- scikit-learn 1.9.1 compiled extensions are blocked by a Windows Application Control policy in the
  user-wide site-packages; everything runs from the project `.venv` (D-002).
- Clinician identity verification is a stub; no real-world report-sharing workflow.
- No HIPAA/GDPR compliance claim.
- `npm audit` reports 2 moderate advisories in `react-router-dom` 6.x (SSR-hydration error deserialisation).
  This SPA does not use SSR hydration; fixing requires a breaking major upgrade to v7, deferred past the
  submission deadline and documented rather than hidden.

## Clean-clone verification (2026-11-16)

A fresh `git clone` of `main` (tracked files only, ~28 MB including the committed pretrained X-ray weights)
was verified in a temporary directory using the project `.venv` and Node 24:

- `pytest tests -q` from `backend/`: **29 passed**, exit 0.
- `npm ci` then `npm run build` from `frontend/`: build succeeded (one non-blocking chunk-size warning).
- Backend started with `uvicorn app.main:app`; `/api/health`, `/docs` and `/openapi.json` (31 paths) returned 200.
- Live end-to-end smoke: register → create profile → `POST /api/predictions/tabular` returned a genuine
  heart-model score with explanation, and the interpretation quoted the correct cohort prevalence (46.2%).
  This caught and fixed a bug where the prevalence was read from the wrong level of the model card (0.0%);
  a regression test now asserts it matches the card.

Training is therefore NOT required to run the demo from a clean clone; `download_data.py` / `train_all.py`
remain available for reproduction.

## Publication (2026-11-16)

- Public repository: https://github.com/Forney2ney/healthsignal — visibility confirmed as PUBLIC via `gh repo view`.
- Public accessibility confirmed with an unauthenticated HTTP fetch of the repository page; the README
  renders correctly (UTF-8, no mojibake) and all required files are present.
- No `.env`, credentials or private keys are tracked.
- Remaining before submission: fill in team names, emails and schools in `docs/ONEPAGE_SUBMIT.md`
  (placeholder deliberately left by the project owner), then submit the write-up link and repo link.