# HealthSignal — One-Page Project Write-Up (Veritas AI Hackathon 2026)

**Project name:** HealthSignal
**Track:** Health
**Team members:** Elyaseen Al Forqani - Nasser Al Habsi

## The problem

People receive health information in fragments: a blood-pressure reading here, a lab result there, a chest
X-ray somewhere else. Nothing joins them up, and nothing explains how confident a statement is. Commercial
"symptom checkers" either fabricate certainty or produce an opaque score. The people with this problem are
individuals trying to understand whether a set of measurements warrants a conversation with a clinician —
and they need to see *what would change the answer*, not just the answer.

## What we built

A working multimodal health-intelligence **research prototype** (not a clinical device):

- **Inputs:** manual measurements with unit/range validation (blood pressure, glucose, HbA1c, lipids, liver
  and kidney function, CBC, age/sex), a questionnaire, and chest X-ray images.
- **Real model outputs:** five tabular classifiers and one published pretrained chest X-ray model each
  produce a score with an explicit interpretation string, the list of features you actually provided, and
  the features the model had to impute (nothing is silently invented).
- **Explanation:** SHAP-based top contributing features for tabular models; Grad-CAM overlay for the X-ray
  model, captioned so it cannot be mistaken for evidence.
- **Outputs:** an explainable patient report and a structured clinician report (markdown) that records
  inputs, outputs, imputed fields, dataset limitations, model version and date.

**This project is a prototype and is not medical advice.** Every screen states that it is an
educational/research prototype, not a clinically validated diagnostic system or a substitute for a qualified
healthcare professional.

## What we added (original contribution)

Most student health projects demo one model with one accuracy number. Our contribution:

1. **Honest evaluation as a first-class output.** Every model card reports model selection by CV,
   **two dummy baselines on the identical held-out split**, separate false positives and false negatives,
   PR-AUC and Brier alongside ROC-AUC, subgroup performance where the dataset carries a demographic
   attribute, and the actual misclassified records with their feature values.
2. **A single ingestion layer that keeps "missing" missing.** Missing measurements are never replaced with
   invented defaults; the imputation the model performs at inference is disclosed per prediction.
3. **Cross-task comparability without false equivalence.** Each model keeps its own dataset, metrics and
   caveats; the dashboard aggregates *information*, not probabilities.

## How it works

- **Datasets** (all public, de-identified, no registration): UCI Heart Disease (303×13), UCI WDBC (569×30),
  UCI Chronic Kidney Disease (400 documented rows → 399 loaded, 1 malformed source row excluded and
  disclosed), Pima Indians Diabetes (768×8), UCI ILPD (583×10). Imaging: pretrained DenseNet-121 weights
  trained on NIH ChestX-ray14, reproducible via Apache-2.0 `torchxrayvision`.
- **Preprocessing:** median imputation + standard scaling for numeric columns; most-frequent imputation +
  one-hot encoding for categorical columns, all inside sklearn Pipelines refitted inside every CV fold.
- **Model:** 4 candidates (logistic regression, random forest, histogram gradient boosting, LightGBM)
  compared by 5-fold stratified CV **on the training split only**; logistic regression won all five CV
  competitions. Deterministic seed 42; `train_all.py` (retrain + full evaluation of all five models +
  image-model cards) took **52 s** on the CPU used for this submission.
- **Stack:** Python/FastAPI backend with JWT + bcrypt auth and role-based access; React + TypeScript +
  Tailwind frontend; SQLite; pytest suite (31 tests, all passing on a clean clone).

## Results (held-out 30% test split, seed 42)

| Model | ROC-AUC | Baseline (stratified random) | Precision | Recall | Specificity | F1 | PR-AUC | FP / FN | n_test |
|---|---|---|---|---|---|---|---|---|---|
| Heart disease | **0.922** | 0.478 | 0.875 | 0.833 | 0.898 | 0.854 | 0.912 | 5 / 7 | 91 |
| Breast cancer (WDBC) | **0.998** | 0.449 | 0.984 | 0.938 | 0.991 | 0.960 | 0.996 | 1 / 4 | 171 |
| Chronic kidney disease | **0.961** | 0.522 | 0.986 | 0.933 | 0.978 | 0.959 | 0.984 | 1 / 5 | 120 |
| Diabetes screening (Pima) | **0.836** | 0.529 | 0.672 | 0.531 | 0.860 | 0.593 | 0.719 | 21 / 38 | 231 |
| Liver condition (ILPD) | **0.779** | 0.522 | 0.748 | 0.952 | 0.200 | 0.838 | 0.911 | 40 / 6 | 175 |

All figures above are read directly from `ml/artifacts/<task>/model_card.json` (`methodology.held_out_test_metrics` and `baselines_on_same_test_split`), not transcribed by hand.

Interpretation we make explicitly in the report:

- ILPD's high recall (0.952) comes at the cost of **40 false positives** in 175 test records and a
  specificity of only 0.200 — the model flags most healthy people. That is a screening trade-off, not an
  achievement, and we say so.
- Pima's ROC-AUC (0.836) is modest while its PR-AUC (0.719) is the more informative figure given the 35/65
  split; 38 false negatives is the clinically costly direction.
- WDBC and CKD are near-separable datasets; quoting their ROC-AUCs as "99% accurate AI" would be
  misleading and we do not.
- No external validation was performed. All numbers apply to these cohorts only.

## Failure analysis

Failure cases are stored in `ml/artifacts/<task>/model_card.json` under
`methodology.failure_cases`, with raw feature values.

- **Pima diabetes, 38 false negatives** (recall 0.531): the strongest single predictor is plasma glucose and
  the label is a diagnostic threshold outcome; people just below a decision boundary are systematically
  missed. Missing glucose/skinfold/insulin values (physiologically impossible zeros treated as missing)
  further weaken borderline cases.
- **ILPD liver, 40 false positives** (specificity 0.200): the dataset aggregates many liver conditions into
  one label with modest signal; the model over-flags. With 71% positive prevalence the always-positive
  baseline reaches recall 1.0 with zero false negatives — our model trades FP for less-obvious FN, which is
  why we report FP and FN separately rather than a single accuracy.
- **Heart, 7 false negatives / 5 false positives:** errors concentrate on two sparse source fields, `ca`
  (major vessels visible on fluoroscopy) and `thal` (defect category). In the strongest false positive
  (true label 0, p=0.956) `ca=3` contributes +2.72 and `thal=7` +0.77; in a false negative with `ca=0`,
  the same feature contributes −0.73 and `thal=3` −0.55, holding the score at 0.205. The top five features
  account for 54–76% of total absolute attribution, so this is a concentrated dependency, not diffuse noise.
  A second pattern is the missed 58-year-old woman with cholesterol 319 mg/dl (p=0.187), where `sex=female`
  contributes −0.75. These are descriptions of model behaviour, not causal claims; the 0.5 threshold is
  fixed and was never tuned on the test split.
- **Subgroup caveat:** subgroups are reported only where the processed data carries a demographic column —
  recorded sex for heart (male n=60, recall 0.871; female n=31, recall 0.727) and ILPD (male n=133, female
  n=42), and age bands for Pima and CKD. WDBC has no demographic attribute. The heart female subgroup has
  only 11 positive cases and the smallest subgroup is n=31, so these figures are presented for transparency
  and must not be read as fairness claims.

## What we would do next

1. Calibrate scores (isotonic/Platt) with enough held-out data so they can be discussed as probabilities.
2. External, ideally multi-site validation, and patient-level grouping for any multi-record dataset.
3. Verified clinician onboarding and real report-sharing workflow (currently the verifier is a stub).
4. More imaging tasks only if a validated public dataset is obtainable; today only chest X-ray is wired.

## Sources

- UCI Heart Disease — https://archive.ics.uci.edu/dataset/45/heart+disease
- UCI Breast Cancer Wisconsin (Diagnostic) — https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic
- UCI Chronic Kidney Disease — https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease
- UCI Indian Liver Patient Records — https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset
- Pima Indians Diabetes (original NIDDK data) — public dataset mirror used for download
- torchxrayvision (pretrained DenseNet-121, NIH ChestX-ray14) — https://github.com/mlmed/torchxrayvision
- Cohen et al., "Torchxrayvision: A library of chest X-ray datasets and models", MIDL 2022
- Tools: scikit-learn, LightGBM, SHAP, PyTorch, FastAPI, React/TypeScript, Tailwind. AI assistance: OpenCode
  coding agents used for scaffolding, debugging and documentation.
- Full credits register: `CREDITS.md`. Full technical detail: `docs/TECHNICAL_REPORT.md`.
