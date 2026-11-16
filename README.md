# HealthSignal — multimodal AI health-intelligence research prototype

> **Safety notice.** HealthSignal is a research/educational hackathon prototype. It is **not** a medical device,
> **not** a diagnostic tool and **not** a substitute for a qualified healthcare professional. Every score it
> produces is a statistical indicator derived from a small public dataset — nothing here is a validated
> individual disease probability, a diagnosis, or treatment advice. If you may be experiencing a medical
> emergency, contact your local emergency services immediately.

HealthSignal ingests several kinds of health information (manual measurements, lab results, questionnaires,
medical images, health history) runs **specialised, individually trained models** on each supported signal,
explains their behaviour (SHAP for tabular models, Grad-CAM for the chest X-ray model) and presents the result
with explicit uncertainty, imputation disclosure and limitations.

## What is genuinely implemented and tested

| Model | Task | Dataset (verified) | Held-out test metrics |
|---|---|---|---|
| `heart` | Heart-disease indicator | UCI Heart Disease (303×13) | ROC-AUC 0.922 · PR-AUC 0.912 · F1 0.854 |
| `wdbc` | Breast mass malignancy indicator | UCI WDBC (569×30) | ROC-AUC 0.998 · PR-AUC 0.996 · F1 0.960 |
| `ckd` | Chronic kidney disease indicator | UCI CKD (399×24, missing values kept) | ROC-AUC 0.961 · PR-AUC 0.984 · F1 0.959 |
| `pima` | Diabetes screening indicator | Pima Indians Diabetes (768×8) | ROC-AUC 0.836 · PR-AUC 0.719 · F1 0.593 |
| `ilpd` | Liver-condition indicator | UCI ILPD (583×10, imbalanced) | ROC-AUC 0.779 · PR-AUC 0.911 · F1 0.838 |
| `cxr_nih` | 14-pathology thoracic classifier | Pretrained DenseNet-121, NIH ChestX-ray14 weights (torchxrayvision) | published AUCs quoted in the model card; **not** re-validated locally |

Full methodology, confusion matrices and limitations live in `ml/artifacts/*/model_card.json` and in
`docs/TECHNICAL_REPORT.md`. Metrics were produced by `ml/scripts/train_all.py` and are deterministic (seed 42).

Architecture coverage (designed for, not implemented): neurological, respiratory and infectious disease models,
CT/MRI/ultrasound interpretation, wearable-data ingestion, hospital integration. These are documented as future
work and are not claimed as present functionality.

## Architecture

```
                    ┌──────────────────────────── React UI (Vite + TS + Tailwind) ───────┐
                    │  dashboard · risk forms · image viewer · reports · assistant        │
                    └───────────────────────────────┬────────────────────────────────────┘
                                                    │ REST (JWT)
                    ┌───────────────────────────────▼────────────────────────────────────┐
                    │                    FastAPI backend (uvicorn)                        │
                    │  auth/RBAC · ingestion+validation · inference · reports · audit logs│
                    └───────┬───────────────────────┬──────────────────────────┬─────────┘
                            │ ml_bridge              │ uploads (validated)      │ SQLite
                    ┌───────▼────────┐      ┌────────▼─────────┐       ┌────────▼────────┐
                    │  ml package    │      │ chest X-ray svc  │       │ users/profiles/ │
                    │ sklearn        │      │ torchxrayvision  │       │ measurements/…  │
                    │ pipelines+SHAP │      │ DenseNet-121     │       │ (SQLAlchemy)    │
                    └────────────────┘      └──────────────────┘       └─────────────────┘
```

- Repository layout: `ml/` (training, artifacts, model cards) · `backend/` (API, DB, uploads, tests) ·
  `frontend/` (SPA) · `docs/` (report, diagrams, demo script) · `HEALTHSIGNAL_PROJECT.md` (specification,
  source of truth) · `PROJECT_STATUS.md` (live status) · `DECISIONS.md` (decision log).

## Requirements verified in the development environment

- Windows, Python 3.12, Node 24. CPU-only (no GPU). 16 GB RAM.
- A **project-local virtualenv is required** (`.venv` at the repo root) — the user-wide site-packages location
  blocks scikit-learn's compiled extensions under a Windows Application Control policy on this machine (see
  `DECISIONS.md`, D-002). Extract the UCI CKD dataset's `.rar` requires a RAR-capable archiver (WinRAR/7-Zip).
- All datasets are public, de-identified and download without registration.

## Installation

Trained models, model cards, the 28 MB pretrained chest X-ray weights, sample cases and sample X-rays are
**committed to the repository**, so a clean clone can run the full demo without retraining or re-downloading
weights. The steps below marked *optional* are only needed to reproduce training or refresh the public data.

```powershell
# from the repository root
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-lock.txt   # exact resolved versions
# (or: pip install -r requirements.txt for compatible ranges)

# optional: re-download + validate public datasets (overwrites ml/data/manifest.json)
.\.venv\Scripts\python ml\scripts\download_data.py

# optional: retrain tabular models and regenerate model cards (~2 min, CPU)
.\.venv\Scripts\python ml\scripts\train_all.py
.\.venv\Scripts\python ml\scripts\run_full_evaluation.py   # baselines, FP/FN, failures, subgroups

# optional: refresh the public-dataset example rows / sample X-rays
.\.venv\Scripts\python ml\scripts\make_sample_cases.py
.\.venv\Scripts\python ml\scripts\fetch_samples.py

# local config (optional for the demo; never commit .env)
Copy-Item .env.example .env
```

The frontend needs its own packages once: `cd frontend; npm install`.

## Run the application

```powershell
# terminal 1 — backend (serving the API at :8000)
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
# first-run bookkeeping
..\.venv\Scripts\python scripts\seed_demo.py   # optional: clearly-labelled SYNTHETIC demo profile + demo users

# terminal 2 — frontend
cd frontend
npm install
npm run dev     # http://localhost:5173
```

Demo login (after seeding): `patient.demo@healthsignal.dev` / `healthsignal-demo-pw-2026`
(also `clinician.demo@`, `researcher.demo@`, `admin.demo@healthsignal.dev`).

## Tests

```powershell
cd backend
..\.venv\Scripts\python -m pytest tests -q
```

The suite covers validation (units/ranges/magic bytes/size), auth (hashing, short passwords, duplicates),
prediction APIs (imputation disclosure, invalid features rejected, unknown models), permissions (profile
ownership, research endpoints cannot see patient data, admin-only audit logs), reports, the assistant's
grounding and the end-to-end chest X-ray workflow including Grad-CAM overlay generation.

## Configuration

All configuration comes from `.env` (never committed): `HS_SECRET_KEY`, `HS_TOKEN_EXPIRE_MINUTES`,
`HS_DATABASE_URL`, `HS_ALLOW_ORIGINS`, `HS_MAX_UPLOAD_MB`, `HS_MODEL_DIR`. See `.env.example`.

## Privacy & security posture (honest scope)

Implemented: bcrypt password hashing, JWT auth, role-based access control, patient-controlled profile sharing
grants (clinicians also require verification to be meaningful), upload validation (extension/MIME/magic
bytes/size), audit logging, secrets in `.env`, safe error responses. **Not implemented / not claimed**:
transport encryption configuration for production, regulatory compliance assessment (HIPAA/GDPR), encryption
at rest beyond OS-level disk protection, clinician identity verification. These are documented as limitations,
not features.

## Documentation

- `docs/TECHNICAL_REPORT.md` — problem, data, methodology, results, explainability, limitations.
- `docs/ARCHITECTURE.md` — architecture and data-flow diagrams (Mermaid).
- `docs/DEMO_SCRIPT.md` — 6-minute demonstration walkthrough using only real functionality.
- `PROJECT_STATUS.md` — feature-by-feature implementation status.
- `DECISIONS.md` — major technical decisions and their reasons.