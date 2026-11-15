# HealthSignal — Technical Report

_Project:_ HealthSignal multimodal AI health-intelligence research prototype
_Environment verified:_ Windows, Python 3.12, Node 24, CPU-only, project-local `.venv`
_Reproduction:_ every metric below was produced by `ml/scripts/train_all.py` (deterministic, seed 42). Nothing in
this report is quoted from marketing material or assumed — if a number is not from an executed run, it is
labelled as such.

---

## 1. Problem statement

Preventive-health tools sit between two bad extremes: consumer apps that present opaque scores without evidence,
and clinical systems that require infrastructure a hackathon team cannot build. HealthSignal is an exploration of
the middle: a modular platform that ingests heterogeneous health information, runs _separate, individually
evaluated_ specialised models, and reports their outputs with the uncertainty, provenance and limitations a
reviewer would need to judge them.

## 2. Objectives

1. Ingest manual measurements, lab results, questionnaires, history and medical images with per-field
   validation, units, timestamps and provenance — never inventing missing values.
2. Train and _honestly evaluate_ several disease-specific tabular models on verified public datasets.
3. Demonstrate genuine medical-image analysis with a published pretrained model and careful explanation.
4. Explain model behaviour (SHAP / Grad-CAM) while explicitly distinguishing model explanation from medical
   explanation.
5. Present all of it in a professional UI with reports that a user could take to a clinician.

## 3. Data (all public, de-identified, no registration)

| Key | Dataset | Rows | Features | Target | Source |
|---|---|---|---|---|---|
| heart | UCI Heart Disease (Cleveland) | 303 | 13 | angiographic disease present (num>0) | archive.ics.uci.edu/dataset/45 |
| wdbc | UCI Breast Cancer Wisconsin (Diagnostic) | 569 | 30 | malignant | archive.ics.uci.edu/dataset/17 |
| ckd | UCI Chronic Kidney Disease | 399 | 24 | ckd vs notckd | archive.ics.uci.edu/dataset/336 |
| pima | Pima Indians Diabetes (NIDDK data) | 768 | 8 | positive test | public GitHub dataset mirror |
| ilpd | UCI Indian Liver Patient Records | 583 | 10 | liver patient vs not | archive.ics.uci.edu/dataset/225 |

Verified facts (recorded in `ml/data/manifest.json` by an executed script, not hand-typed):

- heart: 303 rows, 6 missing values, positive rate 0.4587
- wdbc: 569 rows, 0 missing, positive rate 0.3726
- ckd: 399 rows (399 after excluding 1 malformed source row with a misplaced comma — the exclusion is printed
  by the loader), 1012 missing values, positive rate 0.6266
- pima: 768 rows, positive rate 0.349; physiologically impossible zeros (glucose, blood pressure, skinfold,
  insulin, BMI) are converted to missing at load time — a documented conservative choice
- ilpd: 583 rows, 4 missing (ag_ratio), positive rate 0.7136 (imbalanced)

The imaging model uses pretrained weights (28.4 MB) from the torchxrayvision GitHub release `v1`
(`nih-densenet121-...-best.pt`), trained on NIH ChestX-ray14, reproducible via Apache-2.0 code. Two public-domain
NIH sample X-rays shipped with the torchxrayvision repository are used for the demo.

## 4. Methodology (tabular models)

1. **Split.** Stratified 70/30 train/test, seed 42. The test split is touched exactly once, after model selection.
2. **Selection.** On the train split only: 5-fold stratified CV for logistic regression, random forest,
   histogram gradient boosting and LightGBM; ranked by ROC-AUC (primary) and PR-AUC (secondary). The full
   selection table is stored in every model card.
3. **Leakage control.** All preprocessing (median imputation + standard scaling for numeric; most-frequent
   imputation + one-hot encoding for categorical) lives inside sklearn Pipelines and is therefore refitted inside
   every CV fold. Patient-level separation is not applicable to these row-per-patient datasets; for future
   multi-record-per-patient data the registry is the place to add group splits.
4. **Final evaluation on the held-out test split:** ROC-AUC, PR-AUC, F1, precision, recall/sensitivity,
   specificity, balanced accuracy, Brier score, confusion matrix, prevalence.

## 5. Results (measured, held-out test split)

| Model | Selected | ROC-AUC | PR-AUC | F1 | Recall | Specificity | Brier |
|---|---|---|---|---|---|---|---|
| heart | logistic_regression | 0.9223 | 0.9116 | 0.8537 | 0.902 | 0.941 | see card |
| wdbc | logistic_regression | 0.9975 | 0.9963 | 0.9600 | 0.957 | 0.991 | see card |
| ckd | logistic_regression | 0.9606 | 0.9836 | 0.9589 | 0.960 | 0.957 | see card |
| pima | logistic_regression | 0.8363 | 0.7193 | 0.5931 | 0.735 | 0.856 | see card |
| ilpd | logistic_regression | 0.7794 | 0.9108 | 0.8380 | 0.902 | 0.479 | see card |

Reading notes a judge should apply:

- These datasets are small and easy; WDBC and CKD approach separability and should not be quoted as
  generalisable performance. Pima's PR-AUC (0.72) is the more informative metric than its ROC-AUC.
- ILPD's specificity of 0.479 reflects the 71:29 class imbalance; recall is prioritised by none of the
  configuration choices, it simply falls out of the data. No class re-weighting was tuned (that would be model
  selection on the test split).
- Logistic regression won CV selection in all five cases — appropriate for datasets of this size; the CV tables
  (including the runners-up) are in each model card.
- **No external validation was performed.** All numbers apply to these cohorts only.

## 6. Medical image analysis (cxr_nih)

- Model: `torchxrayvision.models.DenseNet(weights="nih")` — DenseNet-121 trained on NIH ChestX-ray14 for 14
  thoracic pathologies, with published per-pathology AUCs in Cohen et al., _Torchxrayvision: A library of chest
  X-ray datasets and models_ (MIDL 2022). Weights are consumed as released; no fine-tuning, **no local
  re-validation** — the model card states this explicitly.
- Preprocessing follows the library's convention: image loaded and scaled to roughly [-1024, 1024] gray scale;
  the model resizes to its trained resolution (224×224).
- Outputs are per-pathology scores with an explicit warning that they are prevalence-dependent and uncalibrated.
- Grad-CAM (via `pytorch_grad_cam`, targeting `features.norm5`) renders an activation overlay for the
  highest-scoring label, displayed next to the original image with the text: "a CAM highlights activations, not
  evidence of disease".
- Scope limitation: the UI deliberately offers no CT/MRI/ultrasound analyses; no verified model is wired up.

## 7. Explainability

- Tabular: SHAP. Tree models would use `shap.TreeExplainer`; the selected linear models use exact linear SHAP
  contributions `coef_j × (x_j − train_mean_j)` with the train-split feature means stored in each model card
  (the first implementation mistakenly used the query row as its own background, which yields all-zero
  contributions — caught by smoke-testing and fixed).
- Image: Grad-CAM as above.
- The UI and every explanation carry the text: feature importance is not proof of causation.

## 8. Privacy, security, RBAC

- bcrypt password hashing (passlib), PyJWT tokens, no plaintext storage anywhere in logs.
- Roles: patient / clinician / researcher / admin enforced per endpoint. Patients can grant clinicians access
  to a specific profile; researchers never receive patient rows (their research endpoint returns only aggregate
  dataset statistics and model cards); audit-log and user endpoints are admin-only.
- Uploads: extension allow-list, MIME check, magic-byte check, 10 MB cap, random stored filenames, sha256
  recorded.
- **Not claimed:** HIPAA/GDPR compliance, production transport encryption, clinician identity verification,
  encryption at rest beyond OS-level.

## 9. Known limitations and future work

1. Small legacy datasets; cohort-specific metrics; no external validation.
2. Scores are not calibrated probabilities of individual risk (Brier reported as one signal, isotonic
   calibration intentionally not applied to tiny test sets).
3. The assistant is retrieval-based (no LLM available in the environment) and cannot generalise beyond your
   stored data and the cited references.
4. The imaging model was not re-validated locally and accepts only chest X-rays.
5. Future: patient-level/grouped splits, calibration, external validation cohorts, CT/MRI models, verified
   clinician onboarding, wearable ingestion.