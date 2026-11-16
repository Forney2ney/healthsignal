# HealthSignal --- Project Operating Specification

**Document type:** Persistent project specification and engineering
guidance\
**Project:** HealthSignal\
**Primary constraint:** Deliver a complete, scientifically defensible hackathon prototype before the official deadline. The long-term platform vision must not be confused with the scope of the submission.\
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

## 10. Hackathon execution strategy: narrow prototype, broad vision

### 10.1 Preserve the vision; narrow the submission

HealthSignal remains the long-term multimodal, multi-disease health-intelligence platform described in Sections 1–2. The hackathon submission, however, must demonstrate one specific user, one clearly defined health problem and one end-to-end AI workflow that genuinely works.

Do not attempt to implement every disease, input modality, dashboard panel or user role for the competition. A small, real, evaluated model with a reliable demonstration is stronger than a broad interface full of mock or unfinished features.

### 10.2 Select the focused use case from repository evidence

First audit the actual repository and identify what already works. Then select the strongest feasible focused use case using these criteria, in order:

1. A real model or training pipeline already exists and can be verified.
2. A suitable public, de-identified dataset is accessible within the remaining time and its licence/access conditions are understood.
3. The task has a clear target label, a defensible baseline and an unseen test set.
4. The workflow can be demonstrated from input to output in the application or a clearly documented runnable notebook.
5. The team can explain the model, data, evaluation, failure modes and limitations.

Do not assume a particular disease task before inspecting the repository. If no working model exists, choose one small tabular or image task from a reputable public dataset and implement the simplest defensible baseline/model workflow. Prefer a complete end-to-end path over ambitious multimodal fusion.

### 10.3 Mandatory evidence for the chosen task

The final project must answer all four questions:

- **Who is it for, and when do they use it?** Define one specific user and use moment.
- **What goes in and what comes out?** Show a genuine input producing a real model output.
- **Does it beat a simple baseline?** Compare the model with an appropriate baseline on held-out test data.
- **Where does it fail?** Show at least one real error or failure case and explain a plausible reason.

For health tasks, report false negatives and false positives separately. Include sensitivity/recall and specificity where appropriate; do not rely on accuracy alone. Never select or tune a model using the held-out test set.

### 10.4 Health-track rules that must appear in the submission

- Use public datasets only. Do not use real patient records, including records obtained through family, school, work or personal contacts.
- Synthetic examples may be used for interface demonstrations, but label them clearly as synthetic. Never pass synthetic values off as patient data or model-evaluation evidence.
- Include this exact sentence in the write-up and an appropriate place in the application: **"This project is a prototype and is not medical advice."**
- State that outputs are research predictions, not diagnoses, and that the prototype is not clinically validated.
- Credit all datasets, pretrained models, tutorials, libraries and AI tools with links.
- Report honest results, including weak performance, errors and limitations.
- The AI/ML system must be central to the product's main function; using AI only to write the code does not satisfy the track.

### 10.5 Original contribution

If the chosen task follows a suggested project or tutorial, add and document at least one meaningful original contribution. This may be a distinct target user or setting, a justified feature/analysis, a new evaluation question, a comparison, a carefully designed interface/workflow, or another contribution the team can explain. Do not merely re-skin a tutorial.

### 10.6 Feature status and truthful demo

Every visible feature must be classified as implemented and tested, partially implemented, simulated, planned or blocked. A simulated UI example must be visibly labelled and must never be represented as a model prediction. Remove or hide unfinished features if they confuse the main demonstration. Do not show fake confidence, fake patient histories, fake clinical recommendations or invented model metrics.

### 10.7 Required one-page write-up structure

Use the official structure:

1. Project name; track; team members and school.
2. **The problem:** one specific user, the moment of use and why the problem matters.
3. **What we built:** inputs, outputs and how the user interacts with it.
4. **What we added:** identify the suggested project/tutorial basis and the team's original contribution, or state that it is the team's own idea.
5. **How it works:** dataset/source, verified sample count, cleaning/preprocessing, target, model and why it was chosen.
6. **Results:** baseline and model results on held-out test data, false positives, false negatives and at least one failure case.
7. **What we'd do next:** realistic next steps and limitations.
8. **Sources and credits:** dataset, pretrained model, libraries, tutorials and AI tools, with links.

Keep it to one page if required by the form. Do not fill gaps with invented facts. If a metric or feature was not measured or completed, say so.

### 10.8 Submission deliverables and final checks

Required:

- Public GitHub repository or Google Colab notebook accessible to judges. If using Colab, ensure outputs are saved and visible. If Colab is unavailable, use GitHub.
- One-page write-up as a viewable Google Doc, GitHub README or accepted PDF/Word upload.
- Team details: names, emails and schools, with one person submitting for the team.
- Full source/AI credits with links.

Optional: demo video up to two minutes. A concise demo should show the problem (about 15 seconds), working product (about 60 seconds), method/results (about 30 seconds), and next steps/limitations (about 15 seconds).

Before submitting, test every link in a private/incognito window, verify repository visibility, run the project from a clean/reproducible state, ensure the write-up and code describe the same implementation, and confirm that all teammates listed contributed. Resubmission is allowed; the latest submission is used. Do not wait until the final minutes to test links.

## 11. Time-based implementation priorities

The official event runs from Saturday 14 November 2026, 09:00 Oman time, to Monday 16 November 2026, 08:59 Oman time. At the time this guidance pack was updated (15 November 2026, 21:42 Oman time), approximately 11 hours and 17 minutes remained. Recalculate the actual time remaining whenever work resumes; do not assume the original 24-hour estimate is still available.

The submission deadline is a hard constraint. Reserve meaningful time for a clean run, evidence capture, the one-page write-up, source credits, link-permission checks and final submission. Do not spend the remaining time expanding the platform vision.

### Priority 0 --- submission-critical

- One specific user and health problem are defined.
- At least one genuine AI/ML model or inference workflow runs.
- Public dataset and licence/source are verified and credited.
- A simple baseline and model are evaluated on unseen test data.
- False positives and false negatives are reported separately.
- At least one real failure case is documented.
- The core input-to-output demonstration works reliably.
- The exact medical disclaimer is present.
- One-page write-up, code link and source credits are complete.

### Priority 1 --- only after Priority 0 is secure

- A useful explanation or feature-contribution view.
- A polished focused dashboard and report.
- One additional modality or model, only if it strengthens the same user problem and can be evaluated.
- A short demo video.

### Priority 2 --- defer unless time is clearly available

- Broad multimodal fusion.
- Multiple additional disease modules.
- Interactive body map, complex timeline and clinician portal.
- Complex accounts, permissions and cloud infrastructure.

### Priority 3 --- post-hackathon roadmap

- Full multi-disease coverage.
- Medical-record and wearable integrations.
- Hospital-scale infrastructure and production deployment.
- Native mobile apps and advanced governance.

Suggested allocation of the remaining time (adjust to the actual clock):

- 10%: repository audit, use-case decision and dataset/model feasibility.
- 35%: complete the real model, baseline and held-out evaluation.
- 25%: integrate and polish the single end-to-end demonstration.
- 15%: test, capture evidence and document a genuine failure case.
- 15%: one-page write-up, citations/credits, README, link checks and submission.

If the model is already working, move time from implementation to evaluation, integration and submission quality. If the model is not working, cut scope immediately. Do not sacrifice the required write-up and submission checks for extra interface features.

## 12. Development workflow for contributors and AI agents

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

## 13. Testing and quality requirements

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

## 14. Hackathon and submission requirements

Review the actual judging criteria and submission instructions. Map
project work to those criteria rather than guessing what judges value.

Optimise for:

-   A genuine AI/ML capability central to the product (not merely AI-assisted coding).
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

## 15. Required status tracking

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

## 16. Definition of a successful hackathon prototype

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
