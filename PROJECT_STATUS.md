# HealthSignal — Project Status Report

Status classes: IMPLEMENTED AND TESTED / IMPLEMENTED BUT NOT FULLY TESTED / PARTIALLY IMPLEMENTED /
SIMULATED FOR DEMONSTRATION / PLANNED / BLOCKED.
Only results that were actually observed may be marked tested. Nothing here may be fabricated.

_Last updated: 2026-11-16 — final reconciliation (heart subgroup fix, evaluation artifacts, docs, UI refresh, test suite)._

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
separate FP/FN counts, subgroup performance where the source carries a demographic column (recorded sex for
heart and ILPD, age bands for Pima and CKD; WDBC has none), and real failure-case records with exact linear-SHAP
contributions for each miss. See `ml/artifacts/<task>/model_card.json`.

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
| UI refresh: icon navigation, dashboard completeness charts, model ROC-AUC/baseline tiles, sample-case row loading, X-ray thumbnail gallery, interactive Grad-CAM reveal slider | IMPLEMENTED AND TESTED (manual headless-browser walkthrough; production build passes) |
| Session restoration on page reload (JWT from localStorage) | IMPLEMENTED AND TESTED (manual browser walkthrough) |
| Required disclaimer in app banner + write-up | IMPLEMENTED AND TESTED |
| One-page write-up (`docs/ONEPAGE_SUBMIT.md`) | IMPLEMENTED (team names filled in by the owner) |
| Credits/source register (`CREDITS.md`) | IMPLEMENTED |
| Persistent instructions updated (spec §16, AGENTS.md, CLAUDE.md, GEMINI.md) | IMPLEMENTED |
| git history | IMPLEMENTED AND TESTED (evaluation and UI commits pushed to `origin/main`; clean clone verified) |

## Test suite status

Latest observed full-suite run (2026-11-16, project `.venv`, `pytest tests -q`): **31 passed, 0 failed**
in 22.79 s, exit code 0. Two new tests cover the deployment liveness path and the sample-case asset
(`backend/tests/test_health.py`): `/health` must agree with `/api/health`, and the asset served by the
backend must match both `ml/artifacts/sample_cases.json` and the frontend's static copy. Two previously
failing tests were fixed:
`test_reports.py::test_report_generation_and_markdown` (expected heading text) and
`test_permissions.py::test_patient_cannot_read_other_profiles`, whose duplicate import of
`tests.conftest` reset `app.dependency_overrides[get_db]` to the fallback database and produced a 401.
The test now creates its helper user locally instead of re-importing conftest.

Frontend production build (`npm run build`, TypeScript + Vite 6.4.6): **succeeded** on 2026-11-16
(2524 modules, 8.43 s; one non-blocking chunk-size warning).

## UI refresh verification (2026-11-16)

Manual walkthrough in headless Chrome (CDP), against the live backend and seeded synthetic profile:

- Dashboard, models, imaging, reports, assistant and research pages render with the refreshed icon
  navigation, gradient shell and charts.
- "Load positive example row" populated all 13 heart-model inputs from a real de-identified dataset
  record; "Run prediction" returned a genuine score with linear-SHAP contributions.
- Clearing one field (`chol`) before inference produced an imputation disclosure naming exactly `chol`,
  confirming the UI does not silently invent values.
- Chest X-ray sample ran through the pretrained model; the Grad-CAM overlay loaded and the reveal slider
  changed the original/overlay comparison.
- Fixed two real bugs found during this walkthrough: a reload silently signed the user out even though the
  JWT was stored (session restoration added), and the example-row buttons did nothing because
  `sample_cases.json` was missing from `frontend/public/` (Vite's SPA fallback returned `index.html` with
  HTTP 200, masking the 404). `ml/scripts/make_sample_cases.py` now writes both copies to keep them in sync.

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

## Clean-clone verification (2026-11-16, final head `1fecbc5`)

A fresh `git clone --depth 1` of the public repository at the final pushed head (tracked files only, including
the committed model pipelines, model cards, sample cases and the 28.4 MB pretrained X-ray weights) was verified
in a temporary directory using the project `.venv` and Node 24:

- `pytest tests -q` from `backend/`: **31 passed** (24.28 s), exit 0.
- `npm ci` then `npm run build` from `frontend/`: exit 0, build 9.18 s; `dist/sample_cases.json` present.

An earlier end-to-end smoke at `896fc14` (unchanged by the later liveness/documentation commits) additionally
confirmed: `seed_demo.py` created the four demo users and the labelled SYNTHETIC profile; the backend returned
`/api/health`, login, `/api/models` (5 tabular models; heart baseline 0.4779, FP 5 / FN 7, subgroups
male+female), a real heart prediction (0.9951) and the clinician report markdown; the built bundle contains
the required disclaimer sentence.

Training is therefore NOT required to run the demo from a clean clone; `download_data.py` / `train_all.py`
remain available for reproduction (measured 52.2 s).

## Publication (2026-11-16)

- Public repository: https://github.com/Forney2ney/healthsignal — visibility confirmed as PUBLIC via `gh repo view`.
- Clean-clone verification performed at the final head `1fecbc5` (31 tests, `npm ci` + build).
- Public accessibility confirmed with an unauthenticated HTTP fetch: the repository page returns 200, the raw
  `docs/ONEPAGE_SUBMIT.md` returns 200 with the team names and the exact disclaimer sentence, and the README
  renders correctly (UTF-8, no mojibake).
- No `.env`, credentials or private keys are tracked.
- Remaining before submission: none inside the repository — team names are filled in
  `docs/ONEPAGE_SUBMIT.md`. If the submission portal also asks for emails or schools, enter them there;
  then submit the write-up link and repo link.