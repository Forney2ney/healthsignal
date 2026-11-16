# HealthSignal --- Project Operating Specification

**Document type:** Persistent project specification and engineering
guidance\
**Project:** HealthSignal\
**Primary constraint:** Build the strongest scientifically defensible
prototype possible within the available hackathon time (approximately 24
hours of active development).\
**Status:** Living project document --- update it when major decisions
change.

This document is the source of truth for HealthSignal's goals, scope,
engineering standards, safety boundaries, priorities and deliverables.
Project contributors and AI coding agents should consult it before
making significant changes and keep implementation status accurate.

------------------------------------------------------------------------

## 1. Project purpose

HealthSignal is a multimodal AI health-intelligence research prototype.
It is intended to process different types of health information, run
suitable specialised models, explain supported outputs and present the
results in a coherent interface.

The long-term vision is a broad platform covering:

-   Cardiovascular conditions and risk factors.
-   Metabolic conditions, including diabetes and obesity.
-   Cancer-related risk research and appropriate medical-image analysis.
-   Respiratory conditions.
-   Neurological conditions.
-   Kidney and liver conditions.
-   Infectious diseases.
-   General preventative health screening.

The platform is designed to support individuals, patients, healthcare
professionals, healthcare organisations, researchers and students
through appropriately separated user experiences and permissions.

**Important distinction:** the platform vision is broader than the
hackathon implementation. Only conditions and workflows backed by real,
tested and appropriately evaluated models may be described as
implemented. Do not imply that HealthSignal detects every disease.

## 2. Product capabilities

The intended platform may accept the following inputs:

1.  **Manual measurements:** age, height, weight, blood pressure, heart
    rate, temperature, oxygen saturation and other relevant
    measurements.
2.  **Laboratory results:** glucose, HbA1c, cholesterol, complete blood
    count, kidney and liver indicators, and other supported tests.
3.  **Medical images:** X-rays, CT, MRI, ultrasound and other image
    types only where an appropriate model exists.
4.  **Medical records:** structured clinical information, medical
    history, conditions, medications, family history and uploaded
    documents.
5.  **Wearable data:** heart rate, resting heart rate, activity, sleep
    and other supported measurements.
6.  **Questionnaires:** symptoms, lifestyle, family history and relevant
    medical history.

The target user experience includes:

-   A unified health dashboard.
-   Separate outputs for each supported prediction task, with
    uncertainty and limitations.
-   An interactive body map showing relevant systems and indicators
    without implying an unsupported diagnosis.
-   A medical-image viewer with genuine model outputs where available.
-   Explainable reports.
-   A timeline of real recorded measurements and model outputs.
-   An evidence-grounded AI assistant.
-   A structured report that a user may share with a healthcare
    professional.
-   A research workspace for dataset exploration, model comparison and
    evaluation.

These are product goals, not a claim that every feature is already
implemented.

## 3. Engineering principles

### 3.1 Evidence before claims

-   Use real datasets, real model inference and actual test results.
-   Never fabricate dataset sizes, metrics, citations, validation,
    partnerships, users or completed features.
-   Clearly distinguish implemented, partially implemented, simulated
    and planned functionality.
-   Do not present a mock result as a model prediction.
-   Do not call an output a clinically meaningful probability unless the
    model and its calibration support that interpretation.

### 3.2 Modularity

Keep ingestion, preprocessing, model inference, fusion, explanation,
API, storage and presentation as separable components where practical.

Use well-defined interfaces between components. A failed optional module
must not prevent the core application from running.

### 3.3 Missing and uncertain data

-   Missing information must remain missing; do not silently invent or
    impute patient facts.
-   Validate units, ranges, timestamps, provenance and data types.
-   Display data completeness and quality.
-   Record which inputs contributed to each output.
-   Make uncertainty and limitations visible.

### 3.4 Practicality

The hackathon implementation has approximately 24 hours of active
development available. Prefer a small number of working, tested and
explainable workflows over a large collection of superficial features.

Do not spend the entire development window researching or building
infrastructure. Once the key decisions are sufficiently supported,
implement and test.

## 4. AI and model strategy

Investigate and select methods based on the prediction task, dataset,
compute, licence, evaluation quality and time available.

Candidate methods include:

-   Logistic Regression.
-   Random Forest.
-   XGBoost and LightGBM where suitable.
-   Support Vector Machines.
-   Neural networks and other appropriate deep-learning methods.
-   Pretrained medical vision models.
-   Biomedical language models and clinical text-extraction models.
-   Multimodal fusion at feature, embedding or decision level.
-   Ensembles where the outputs are meaningfully compatible.

Potential tools and model resources to investigate include scikit-learn,
XGBoost, PyTorch, TensorFlow, MONAI, Hugging Face and Google CXR
Foundation. These are candidates, not mandatory dependencies. Verify
that each selected resource is accessible, suitable, licensed for the
intended use and feasible to run.

For every implemented model, document:

-   Model name and version.
-   Exact prediction target.
-   Dataset and source.
-   Preprocessing and feature handling.
-   Training and validation strategy.
-   Evaluation method and actual results.
-   Calibration status, if relevant.
-   Known limitations and intended use.

For medical imaging, validate image formats and preprocessing. Use an
appropriate pretrained model or fine-tuning approach if feasible.
Explain visualisations such as Grad-CAM carefully: highlighted regions
are not proof of disease.

For multimodal analysis, do not combine incompatible outputs simply to
claim multimodality. Use a documented fusion method, retain modality
provenance and handle unavailable modalities safely.

For explainability, investigate methods such as SHAP for suitable
tabular models and Grad-CAM for suitable image models. Feature
importance is not causation.

## 5. Dataset research and data governance

Prefer public, de-identified datasets from legitimate sources such as
PhysioNet, UCI, NIH, official research repositories and appropriately
licensed Hugging Face or Kaggle datasets.

For each selected dataset, record:

-   Name and source URL.
-   Intended research task.
-   Features and labels.
-   Record or image count, verified from the source.
-   Licence and access restrictions.
-   Preprocessing requirements.
-   Known biases and limitations.
-   Why it is appropriate for the selected task.

Do not pretend gated, registration-only or unavailable data can be
downloaded immediately. Do not use identifiable patient data in the
hackathon demonstration. Use public de-identified data or clearly
labelled synthetic profiles.

## 6. Evaluation standards

Evaluation is mandatory for every predictive model.

Use appropriate metrics rather than accuracy alone. Depending on the
task, report:

-   Accuracy.
-   Precision.
-   Recall / sensitivity.
-   Specificity.
-   F1 score.
-   ROC-AUC.
-   PR-AUC for imbalanced tasks.
-   Confusion matrix.
-   Calibration and Brier score where appropriate.

Prevent data leakage. Keep preprocessing and feature selection inside
the training pipeline. Use patient-level separation when required by the
dataset. Do not use the test set for model selection. Explain when
external validation is unavailable.

Discuss false positives, false negatives, class imbalance, dataset
representativeness and generalisability. Results from different datasets
or prediction tasks must not be presented as directly comparable without
justification.

## 7. Clinical safety boundaries

HealthSignal is an educational and research prototype, not a clinically
validated diagnostic device and not a substitute for a qualified
healthcare professional.

-   Present outputs as research predictions or potential indicators,
    never confirmed diagnoses.
-   Do not prescribe treatment or medication.
-   Do not provide false reassurance from a low model score.
-   Do not claim to rule out disease or emergencies.
-   Do not infer a disease from a body-map indicator alone.
-   Make model limitations, uncertainty, missing data and intended use
    visible.
-   Encourage appropriate professional assessment where relevant.
-   The AI assistant must distinguish patient-provided facts, extracted
    facts, model outputs and generated explanations.
-   Ground assistant responses in available information and reliable
    sources; acknowledge when information is insufficient.

Any urgent-warning feature must be carefully scoped and must not claim
to reliably detect or exclude emergencies.

## 8. Privacy and security

Treat health information as sensitive.

Implement feasible protections, including:

-   Authentication where supported.
-   Password hashing, never plaintext password storage.
-   Role-based access control.
-   User-controlled sharing permissions.
-   Encryption in transit and appropriate protection at rest.
-   Secure file handling and upload validation.
-   Restricted file types and file sizes.
-   Input validation and safe error handling.
-   Secrets outside source code and version control.
-   Audit logs where appropriate.
-   Data deletion and retention controls.
-   De-identification for research use.

Separate permissions for individuals, patients, clinicians,
organisations, researchers and administrators. Do not assume a user is a
verified clinician without a verification process. Researchers must not
automatically receive access to identifiable patient data.

Do not claim HIPAA, GDPR or other regulatory compliance without a real
assessment. If a security feature is not implemented or verified, state
that clearly.

## 9. Application and deployment direction

The preferred product direction is a responsive web application with a
Python backend, while keeping the architecture portable enough to
support local development, Colab-based experimentation and future cloud
or mobile deployment.

Potential stack:

-   **Backend:** Python, FastAPI, Pydantic.
-   **Frontend:** React and TypeScript, with Next.js if useful.
-   **ML:** scikit-learn, XGBoost, PyTorch, TensorFlow or MONAI as
    justified.
-   **Storage:** SQLite for a fast prototype; PostgreSQL if the
    requirements justify it.
-   **Experimentation:** Google Colab and local Windows development.
-   **Version control:** Git and GitHub.

Inspect the actual environment before choosing. Do not assume a GPU, API
key, cloud account or service is available. Avoid unnecessary
dependencies and infrastructure.

## 10. Time-based implementation priorities

The available active development window is approximately 24 hours.
Adjust the schedule based on actual progress.

### Priority 0 --- must work

-   The project starts reliably.
-   Data input and validation work.
-   At least one real predictive model runs.
-   Its evaluation is documented.
-   Frontend and backend connect.
-   An end-to-end demonstration succeeds.

### Priority 1 --- high value

-   Additional disease-specific prediction tasks.
-   A genuine medical-image workflow, if feasible.
-   Explainability.
-   Unified dashboard.
-   Structured report generation.

### Priority 2 --- additional value

-   Multimodal integration.
-   Evidence-grounded assistant.
-   Interactive body map.
-   Timeline.
-   Additional model families and research tools.

### Priority 3 --- future development

-   Full clinical integrations.
-   Hospital-scale infrastructure.
-   Production cloud deployment.
-   Native mobile applications.
-   Advanced model governance and broader disease coverage.

Suggested time allocation:

  Stage                                           Approximate elapsed time
  --------------------------------------------- --------------------------
  Environment, rules and feasibility research                   0--2 hours
  Architecture and build plan                                   2--3 hours
  Core AI and evaluation                                        3--9 hours
  Application and integration                                  9--15 hours
  Testing and debugging                                       15--19 hours
  Polish, documentation and submission                        19--24 hours

These are planning guides, not rigid gates. Reallocate time to protect
the core working demonstration.

## 11. Development workflow for contributors and AI agents

Before making significant changes:

1.  Read this specification and the root-level agent instructions.
2.  Inspect the repository, current branch, existing files and project
    status.
3.  Read the official hackathon rules, brief and submission requirements
    if available.
4.  Check existing implementations and tests before replacing anything.
5.  Verify relevant dataset, model and dependency sources.
6.  Record important technical decisions.
7.  Implement in small, testable increments.
8.  Run relevant tests and inspect actual outputs.
9.  Update the project status and documentation.

Make routine, reversible engineering decisions independently. Ask for
approval before destructive operations, overwriting important files,
spending money, exposing private information, creating external accounts
or making major irreversible changes.

Preserve useful existing work. Do not rewrite a working project without
a clear reason.

If a dataset or model is unavailable, find a feasible alternative. If a
feature is infeasible within the deadline, preserve the core application
and document the limitation.

## 12. Testing and quality requirements

Test the important workflows, including:

-   Data preprocessing and validation.
-   Missing values and invalid units.
-   Model loading and inference.
-   API endpoints.
-   File uploads and unsupported formats.
-   Oversized or malformed files.
-   Database operations.
-   Permissions and access control.
-   Report generation.
-   Frontend interactions.
-   End-to-end demonstration.
-   Failure handling and recovery.

Use reproducible seeds where appropriate and record dependency versions.
A test may only be marked as passed if it was actually executed
successfully. Do not hide errors to make the project appear complete.

## 13. Hackathon and submission requirements

Review the actual judging criteria and submission instructions. Map
project work to those criteria rather than guessing what judges value.

Optimise for:

-   Meaningful problem definition.
-   Technical depth.
-   Genuine AI functionality.
-   Appropriate data and methodology.
-   Honest evaluation.
-   Responsible AI and explainability.
-   A polished working demonstration.
-   Reproducibility.
-   Clear documentation.
-   Strong presentation.

Prepare as required:

-   Runnable source code.
-   README with setup, configuration, run and test instructions.
-   Technical report with methods, data, metrics, results and
    limitations.
-   Architecture and data-flow diagrams.
-   Dataset and model references.
-   Demonstration script.
-   Required competition submission files.

Verify that final files exist and open correctly.

## 14. Required status tracking

Maintain a project status document, preferably `PROJECT_STATUS.md`.

Classify each feature as one of:

-   **IMPLEMENTED AND TESTED**
-   **IMPLEMENTED BUT NOT FULLY TESTED**
-   **PARTIALLY IMPLEMENTED**
-   **SIMULATED FOR DEMONSTRATION**
-   **PLANNED**
-   **BLOCKED**

For each model, record its name/version, task, dataset, evaluation
approach, actual metrics, limitations and whether inference has been
tested.

Keep a technical decision log, preferably `DECISIONS.md`, for major
architecture and dataset choices.

## 15. Definition of a successful hackathon prototype

A successful prototype is not the one with the longest feature list. It
is the one that demonstrates a coherent, functioning and scientifically
credible workflow.

At minimum, a judge should be able to:

1.  Open the application.
2.  Provide or select a clearly labelled demonstration health profile.
3.  Submit valid information.
4.  Trigger at least one genuine AI prediction.
5.  See an understandable output with appropriate uncertainty and
    limitations.
6.  Inspect the evidence or explanation available for that output.
7.  Understand which parts are real, incomplete or planned.

Additional working modalities and features should be added when they can
be implemented and tested without compromising this core experience.

**Guiding principle: ambitious scope, disciplined execution, verifiable
results and honest communication.**

---

## 16. Official competition requirements (Veritas AI International High School Hackathon 2026)

These take precedence over any earlier interpretation in this document. They were
provided by the organisers and must remain available to future agents.

### 16.1 Prototype focus

The long-term multi-disease, multimodal vision remains. The SUBMISSION, however,
must demonstrate a focused, genuinely working AI prototype:

1. One clearly identified target user.
2. One specific health problem or prediction task.
3. At least one real, functioning AI/ML model.
4. A real input producing an actual model output.
5. A usable interface demonstrating the complete workflow.
6. Explainable results where technically appropriate.
7. A meaningful comparison against a simple baseline.
8. Honest evaluation using unseen test data.

Do NOT force multiple incompatible models or modalities into the prototype to
look advanced. Current health-track use case: a person (or clinician) enters real
clinical measurements and labs; specialised tabular models produce indicator
scores with per-feature SHAP explanation, disclosed imputation and dataset
honesty; chest X-rays run a genuine pretrained model with Grad-CAM.

### 16.2 Mandatory evaluation requirements (Health track)

- Public datasets only; never identifiable patient records.
- Proper training / validation / HELD-OUT TEST sets. No leakage (preprocessing
  inside CV pipelines; patient-level separation when applicable).
- Compare the model against an appropriate SIMPLE BASELINE on the same split.
  Implemented: `DummyClassifier(stratified)` and `DummyClassifier(most_frequent)`
  in `ml/scripts/run_full_evaluation.py`.
- Report actual measured performance, never estimated or fabricated metrics.
- Report FALSE POSITIVES and FALSE NEGATIVES separately.
- Include precision, recall, F1 and other appropriate metrics, plus the
  confusion matrix.
- Identify at least one incorrect prediction or failure case and explain
  possible reasons. Implemented: `methodology.failure_cases` in each model card.
- Consider performance across relevant demographic groups where the dataset
  supports it. Implemented: `methodology.subgroup_performance` (age band for
  Pima / CKD, recorded sex for heart / ILPD; WDBC has no usable demographic
  attribute in its processed features), with an explicit "not a fairness claim" note.
- Document dataset limitations, class imbalance and generalisability concerns.

### 16.3 Distinctiveness

HealthSignal's differentiators, all demonstrable: (a) evaluation itself is a
first-class, inspectable output (baselines, separate FP/FN, failure records,
subgroup figures); (b) missing data stays missing and imputation is disclosed
per prediction; (c) cross-task aggregation without false equivalence; (d) honest,
interpretable prediction interface.

### 16.4 Interface and demonstration

A complete working demonstration beats many unfinished features. No fabricated
predictions, fake patient records, invented model confidence or simulated
functionality may be presented as real. Any demonstration data must be
explicitly labelled synthetic.

### 16.5 Required disclaimer

The exact sentence ``This project is a prototype and is not medical advice.``
must appear in the final write-up (`docs/ONEPAGE_SUBMIT.md`) and in the
application UI. Equivalent wording must also make clear that HealthSignal is an
educational/research prototype, not a clinically validated diagnostic system or
substitute for a qualified healthcare professional.

### 16.6 Required submission documentation

One-page write-up structure (implemented in `docs/ONEPAGE_SUBMIT.md`): project
name; track and team members; the problem; what we built (inputs, outputs,
usage); what we added; how it works (datasets, sample counts, preprocessing,
model); results (baseline vs model on held-out test data); failure analysis;
what we would do next; sources (datasets, pretrained models, tutorials, AI
tools, with links).

Submission requires a publicly accessible GitHub repository or Google Colab
notebook. A demo video of up to two minutes is optional but recommended.

### 16.7 Persistent files

Keep current at all times: this specification, `AGENTS.md` / `CLAUDE.md` /
`GEMINI.md`, `PROJECT_STATUS.md` (implemented / partial / simulated / planned /
blocked), `DECISIONS.md`, and `CREDITS.md` (complete source register).

### 16.8 Operating order

1. Working end-to-end AI health use case.
2. Correct data handling and evaluation.
3. Reliable demonstration.
4. Clear, polished interface.
5. Explainability and useful reporting.
6. Documentation, reproducibility, submission readiness.
7. Additional features only if time permits.

Never fabricate progress, test results, sources, citations or capabilities.
