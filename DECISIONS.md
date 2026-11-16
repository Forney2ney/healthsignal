# HealthSignal — Technical Decision Log

Append-only record of major technical decisions. Newest last.

## D-001 (Phase 0) — Project root and repository layout
**Decision:** Repo root = current workspace. Monorepo layout: `ml/` (training, artifacts, model cards), `backend/` (FastAPI), `frontend/` (Vite React TS), `docs/` (report, diagrams, demo script). Guidance files from `healthsignal_project_guidance/` copied to root per their README.
**Rationale:** Single hackathon demo; one repo is easiest to submit and review.

## D-002 (Phase 0) — Python environment: project-local venv replaces user-site install
**Observed problem:** scikit-learn 1.9.1 compiled extension `_middle_term_computer` fails to import under the user site-packages path (`C:\Users\User\AppData\Roaming\Python\...`): "An Application Control policy has blocked this file" (Windows code-integrity policy).
**Decision:** Create project-local `.venv` and install all dependencies there. `lightgbm` and `torch` import fine in user-site, but the venv gives one reproducible environment for ml + backend.
**Status:** venv created; full dependency install in progress. If scikit-learn is also blocked by hash inside the venv, fallback: use LightGBM only for gradient boosting and implement logistic regression via numpy (documented in PROJECT_STATUS.md).

## D-003 (Phase 0) — Prediction tasks selected from verified public datasets
**Decision:** Initial implemented models, all verified downloadable without registration:
1. Heart disease (UCI Heart Disease, id 45, 303×13, direct zip) — binary target (>0 disease).
2. Breast cancer (UCI WDBC, id 17, 569×30) — malignant/benign.
3. Chronic kidney disease (UCI, id 336, 400×24, contains missing values) — ckd/notckd; also demonstrates honest missing-data handling.
4. Type-2 diabetes screening (Pima Indians Diabetes, 768×8, public mirror of the original NIDDK dataset) — positive/negative.
5. Liver condition risk (UCI ILPD, id 225, 583×10) — liver patient / not.
**Rationale:** small, well-documented, no-auth, reproducible; cover cardiovascular, metabolic, oncology, kidney and liver domains to match P1 breadth. UILB/ICU datasets with credentialing (e.g., PhysioNet Diabetes 130-US) deliberately excluded.

## D-004 (Phase 0) — Medical imaging via torchxrayvision pretrained DenseNet-121
**Decision:** Use `torchxrayvision.models.DenseNet(weights="nih")` (14 thoracic pathologies, trained on NIH ChestX-ray14, published AUCs in the allus 2019 paper) and `weights="pc"` (pediatric pneumonia, Kaggle CXR). Weights are 28.4 MB each, hosted on the torchxrayvision GitHub release `v1` (verified reachable, 200). Inference + Grad-CAM on CPU.
**Rationale:** genuine published pretrained medical model, small enough for CPU, no dataset registration required. Demo images: two public-domain NIH ChestX-ray14 sample images shipped in the torchxrayvision repo (verified reachable).
**Limitations to document in model cards:** images must be chest X-rays; NIH-trained adult frontal view; probabilities are dataset prevalence-dependent, not validated individual risk.

## D-005 (Phase 0) — Evaluation methodology (mandatory)
**Decision:** For each tabular dataset: 70/30 stratified train/test split with fixed seed (42), model selection by 5-fold stratified CV on the TRAIN split only (ROC-AUC primary, PR-AUC secondary), final held-out test metrics reported once per selected model: accuracy, balanced accuracy, precision, recall/sensitivity, specificity, F1, ROC-AUC, PR-AUC, Brier, confusion matrix. Preprocessing (imputation, encoding, scaling) inside the CV folds via sklearn Pipelines to prevent leakage.

## D-006 (Phase 0) — Stack: FastAPI + SQLite + Vite React TS; JWT auth; RBAC
**Decision:** Backend FastAPI + Pydantic v2 + SQLAlchemy 2 (SQLite default, env-switchable). Auth: PyJWT access tokens + passlib bcrypt. Roles: patient, clinician, researcher, admin. Frontend: Vite + React + TypeScript + Tailwind + Recharts. No Next.js (SPA is faster to build and adequate).
**Rationale:** spec-endorsed stack, fast iteration, no cloud dependency.

## D-007 (Phase 0) — AI assistant is retrieval/evidence-grounded, not an LLM
**Decision:** No LLM API key detected in the environment. The assistant answers strictly from (a) the user's own stored inputs/results, (b) curated static disease-domain knowledge snippets with citations. No generative clinical advice, no invented chat content. Documented as "evidence-grounded retrieval assistant".
**Rationale:** spec forbids fabricated intelligence; no credentials available.

## D-008 (Phase 1) — CKD dataset extracted via installed WinRAR; 1 malformed source row excluded
**Observed:** the UCI CKD zip wraps `Chronic_Kidney_Disease.rar`; 3 rows in the extracted ARFF have 26 comma-separated fields (misplaced commas) while 25 are expected.
**Decision:** extract the .rar with the installed WinRAR CLI (verified present on this machine); exclude the malformed row and disclose the exclusion (399 rows loaded instead of the documented 400). No attempt is made to reconstruct or silently repair the malformed row.
**Rationale:** preserving data integrity over row count; the exclusion is printed by the loader and recorded in the manifest.

## D-009 (Phase 1) — Auth uses bcrypt directly; passlib removed
**Observed:** passlib 1.7.4 is incompatible with bcrypt 5.0.0 (`module 'bcrypt' has no attribute '__about__'`) and hash calls surface a misleading "password cannot be longer than 72 bytes" ValueError.
**Decision:** use the `bcrypt` library directly (`hashpw`/`checkpw`) and cap registration passwords at 72 bytes in the schema (clean 422 instead of a 500). `passlib` removed from requirements.
**Rationale:** fewer dependencies, version-stable API.

## D-010 (Phase 1) — WDBC loader column names fixed to canonical order
**Observed bug:** the initial WDBC loader assigned feature names in `feature-major` order (mean_radius, se_radius, worst_radius, ...) while the source file's layout is `stat-major` (all 10 mean features, then se, then worst). Model maths were unaffected (names are applied consistently at train and serve time) but every SHAP explanation and every user-facing label would have described the WRONG measurement.
**Fix:** names follow the documented dataset layout; models retrained (metrics identical - the data matrix is unchanged, only labels were corrected); sample-case rows regenerated.

## D-011 (Phase 1) — Explanation implementation: exact linear SHAP with train-split baseline
**Observed bug:** the first explainer passed the query row as its own SHAP background, producing all-zero contributions (a silent no-op).
**Fix:** for the selected logistic-regression models, contributions are computed exactly as
`coef_j * (x_j - train_split_mean_j)`; the train-split feature means are stored in each model card
(`methodology.linear_explanation_baseline`). Tree models (had they won selection) use `shap.TreeExplainer`.
**Rationale:** exact, deterministic, no leakage (baseline from the train split only), and fast at serve time.

## D-012 (Phase 1) — Offline end-to-end verification before frontend wiring; parent-dir audit
**Observed:** several backend path calculations used `parents[3]` from `backend/app/*`, resolving one directory too high on this machine (`C:\Users\User\Projects`).
**Fix:** all repo-relative paths now use `parents[2]` from `backend/app/*.py`; audited with grep (only the tests file, since fixed).

## D-013 (Phase 2) — Official Veritas requirements audited; mandatory evaluation implemented
**Observed (audit).** The project already had: five trained tabular models with held-out metrics, a working pretrained chest X-ray pipeline with Grad-CAM, a FastAPI + React application, a pytest suite, dashboard / model forms / imaging / reports / assistant / research pages, and documentation. What it did NOT have, which the organisers require: a baseline comparison, false positives and false negatives reported separately, identified failure cases, subgroup performance, one-page write-up, credits register.

**Decision.** Added `ml/scripts/run_full_evaluation.py`, which for every dataset produces, in one deterministic run (seed 42):

- model selection by 5-fold stratified CV on the train split only,
- `DummyClassifier(stratified)` and `DummyClassifier(most_frequent)` baselines on the SAME held-out test split,
- accuracy, balanced accuracy, precision, recall/sensitivity, specificity, F1, ROC-AUC, PR-AUC, Brier and the confusion matrix, with `false_positives` and `false_negatives` as separate top-level numbers,
- subgroup performance where a demographic column exists (recorded sex for heart and ILPD, age band for pima and ckd; WDBC has no usable demographic attribute in its processed features), with an explicit "this is not a fairness claim" note,
- the actual misclassified test records with raw feature values and exact linear-SHAP contributions.

Model cards were regenerated with this script. No metric in the submission is hand-transcribed.

**Rationale.** The organisers make baseline + FP/FN + failure analysis mandatory. Producing them from a script keeps the numbers reproducible and honest.

## D-014 (Phase 2) — Required disclaimer promoted to a first-class UI element
The exact sentence **"This project is a prototype and is not medical advice."** appears in the global application banner (`frontend/src/App.tsx`) and verbatim in `docs/ONEPAGE_SUBMIT.md`.

## D-015 (Phase 2) — Focus of the submission
The submission demonstrates ONE end-to-end workflow rather than the full platform breadth: a user (clinician-adjacent individual or researcher) enters real clinical measurements and labs, each specialised model returns an indicator with per-feature SHAP explanation, disclosed imputation and its own dataset/metrics/caveats; chest X-ray runs the genuine pretrained model with Grad-CAM. Additional models are available but are not load-bearing for the demo.

## D-016 (Phase 2) — Evaluation reconciliation: four defects fixed before submission
**Observed and fixed:**

1. **Heart subgroups silently empty.** `sex` is stored as a float (`1.0`), while the subgroup matcher compared it to the string `"1"`, so no heart subgroup was ever reported. The matcher now compares numeric group keys numerically. Heart now reports male (n=60, recall 0.871) and female (n=31, recall 0.727).
2. **Evaluation did not persist pipelines.** `run_full_evaluation.py` wrote model cards but no `model.joblib`, so re-running evaluation alone could leave cards without matching models. It now saves each fitted pipeline next to its card.
3. **Deprecated trainer could overwrite compliant cards.** `train_all.py` called `train_tabular.run_all`, which does not produce baselines, separate FP/FN, subgroups or failure records. `train_all.py` now delegates to `run_full_evaluation.run()`, so the documented reproduction command produces exactly the artifacts quoted in the submission.
4. **Failure records lacked attribution.** They now include exact linear-SHAP `top_contributions` and `top5_share_of_absolute_contribution` per misclassified record, computed against train-split feature means (no leakage). The former `~2 minutes` runtime claim was replaced with the measured `train_all.py` runtime (52.2 s on the submission CPU).

**Rationale:** each defect produced a false or missing statement in submission-facing material; the fix is in the generator, not in hand-edited numbers.

## D-017 (Phase 2) — Test isolation: duplicate conftest import reset the DB override
**Observed:** `backend/tests/test_permissions.py` imported `make_user` from `tests.conftest`. Re-executing that module reset `app.dependency_overrides[get_db]` to its module-level fallback database, so requests in the test saw a different database and returned 401.
**Fix:** the helper user is created locally inside the test module; no test imports `conftest`. Full suite: 29 passed (23.70 s, project `.venv`).
**Rationale:** the override must remain the per-test database for the whole test; production code was correct.

## D-018 (Phase 2) — Liveness path and static sample-case asset are covered by tests
**Observed:** the API exposed `/api/health` only, so uptime probes using the conventional `/health` path returned 404 and could report the service as down. Separately, the model forms load `/sample_cases.json` as a static asset; the backend serves it directly, but Vite only proxies `/api`, so the frontend needs its own copy in `frontend/public/` — a missing copy was masked by Vite's SPA fallback (HTTP 200 with `index.html`), leaving the "load example row" buttons silently empty.
**Fix:** `backend/app/main.py` serves `/health` with the same payload as `/api/health`; `ml/scripts/make_sample_cases.py` writes both the ML artifact and the frontend copy so they cannot drift; `backend/tests/test_health.py` asserts the alias agrees with `/api/health` and that the backend-served asset equals both on-disk copies.
**Rationale:** a deployment probe and a UI asset must not fail silently; both are now observable, testable and identical across copies.