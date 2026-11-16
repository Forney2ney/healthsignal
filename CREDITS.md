# HealthSignal — Credits and Source Register

Every dataset, pretrained model, library and AI tool used by this project, with provenance. If something is
not in this file, it was not used.

## Datasets (all public, de-identified, no registration required)

| Dataset | Records used | Source URL | Licence / access | Used for |
|---|---|---|---|---|
| UCI Heart Disease (Cleveland, processed) | 303 | https://archive.ics.uci.edu/dataset/45/heart+disease | UCI ML Repository hosting; no registration | Heart-disease indicator classifier |
| UCI Breast Cancer Wisconsin (Diagnostic) | 569 | https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic | UCI ML Repository hosting; no registration | Malignancy classifier |
| UCI Chronic Kidney Disease | 400 documented, **399 loaded** | https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease | UCI ML Repository hosting; archive wraps a `.rar` requiring WinRAR/7-Zip | CKD classifier; missing-data handling |
| Pima Indians Diabetes (original NIDDK data) | 768 | Public GitHub dataset mirror (`jbrownlee/Datasets`) used as the download source; original data from the National Institute of Diabetes and Digestive and Kidney Diseases | Public mirror, no registration | Diabetes screening classifier |
| UCI Indian Liver Patient Records (ILPD) | 583 | https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset | UCI ML Repository hosting; no registration | Liver-condition classifier (imbalanced) |

### Data-handling disclosures

- **CKD:** 1 source row has a misplaced comma (26 fields where 25 are expected). It is **excluded**, and the
  loader prints the exclusion. We do not repair or reconstruct malformed rows.
- **Pima:** glucose, blood pressure, skinfold, insulin and BMI contain physiologically impossible zeros,
  which we treat as **missing** (documented conservative choice), not as real zero measurements.
- **ILPD:** the `selector` column is 1 = liver patient, 2 = not. Mapped to 1/0 accordingly.
- No identifiable patient data is present anywhere in this repository. The only synthetic profile is created
  by `backend/scripts/seed_demo.py`, is flagged `is_synthetic=True`, and is labelled "SYNTHETIC DEMO" in the
  UI.
- The "load positive/negative example row" buttons use real de-identified records from the same public
  datasets, selected near the dataset median and written to `ml/artifacts/sample_cases.json` (mirrored to
  `frontend/public/` as a static asset) by `ml/scripts/make_sample_cases.py`. They are dataset records, not
  synthetic patients and not a real living person.

## Pretrained models

| Model | Source | Licence | How used |
|---|---|---|---|
| DenseNet-121 chest X-ray pathology weights (`nih`) | https://github.com/mlmed/torchxrayvision/releases/download/v1/nih-densenet121-d121-tw-lr001-rot45-tr15-sc15-seed0-best.pt (28.4 MB) | Apache-2.0 code; weights trained on NIH ChestX-ray14 (public-domain images) | Multi-label thoracic pathology inference + Grad-CAM, CPU, no fine-tuning, **not re-validated locally** |
| DenseNet-121 pediatric pneumonia weights (`pc`) | Same release (`pc-densenet121-...-best.pt`) | as above | Verified downloadable; not wired into the UI (documented as such) |

Citation for the library: Cohen et al., "Torchxrayvision: A library of chest X-ray datasets and models",
MIDL 2022.

## Software libraries

| Library | Purpose | Version pinned in |
|---|---|---|
| scikit-learn | Tabular pipelines, metrics, CV | `requirements.txt` |
| LightGBM | Gradient-boosting candidate | `requirements.txt` |
| SHAP | Linear/tree explanations | `requirements.txt` |
| numpy / pandas / scipy | Data handling | `requirements.txt` |
| torch / torchvision (CPU) | Image model runtime | `requirements.txt` |
| torchxrayvision / pytorch-grad-cam | X-ray model + Grad-CAM | `requirements.txt` |
| FastAPI / uvicorn / pydantic / SQLAlchemy | Backend | `requirements.txt` |
| bcrypt / PyJWT | Password hashing and tokens | `requirements.txt` |
| React / TypeScript / Vite / Tailwind / Recharts | Frontend | `frontend/package.json` |
| lucide-react | UI icon set | `frontend/package.json` |
| pytest | Backend tests | `requirements.txt` |

Exact resolved versions are regenerated with `.\.venv\Scripts\python -m pip freeze > requirements-lock.txt`
by whoever reproduces the project; `requirements.txt` carries compatible ranges.

## Environment constraints discovered and worked around (see `DECISIONS.md`)

1. scikit-learn compiled extensions are blocked by a Windows Application Control policy in the user-wide
   site-packages → everything runs from the project `.venv` (D-002).
2. passlib 1.7.4 is incompatible with bcrypt 5.x → direct `bcrypt` API used (D-009).
3. UCI CKD archive wraps a `.rar` → extracted with the installed WinRAR (D-008).
4. No GPU is available; all training is small-tabular or pretrained-image inference on CPU.

## AI tools used

- OpenCode-connected coding agents were used for scaffolding, debugging, test scaffolding and documentation.
- No generative LLM API is used at runtime; the in-app assistant is a retrieval system over the user's own
  stored data plus the cited references above, and it states its own uncertainty.