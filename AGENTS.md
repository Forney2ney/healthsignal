# Repository instructions

Before planning or making significant changes in this repository, read
`HEALTHSIGNAL_PROJECT.md` in full. It is the source of truth for the
project's purpose, scope, engineering standards, clinical-safety
boundaries, privacy requirements, time constraints, priorities and
deliverables.

Follow it throughout the project. Do not treat its future-facing product
goals as claims that features are already implemented.

Before changing existing code, inspect the repository and preserve
working functionality. Verify datasets, licences, model availability and
technical claims. Run tests and report only results that were actually
observed.

Keep `PROJECT_STATUS.md` and `DECISIONS.md` up to date. Clearly
distinguish implemented and tested, partially implemented, simulated,
planned and blocked work.

For this health-related project, never fabricate clinical results, model
metrics, dataset details or validation. Treat HealthSignal as a research
and educational prototype, not a diagnostic device.

---

## Official hackathon requirements (binding)

HealthSignal is being submitted to the **Veritas AI International High School Hackathon 2026 (Health track)**. Before any work, read `HEALTHSIGNAL_PROJECT.md` section 16, which contains the organisers' full requirements. The binding summary:

1. **Focused prototype over feature count.** One target user, one prediction task, one working end-to-end workflow. Do not bolt on extra models or modalities to look advanced; add only what can be completed and demonstrated.
2. **Evaluation is mandatory and must include a baseline.** Every predictive model needs: train/validation/held-out-test separation, no leakage, a comparison against a simple baseline on the SAME split, precision / recall / F1 / confusion matrix, and FALSE POSITIVES AND FALSE NEGATIVES REPORTED SEPARATELY. Missing-data handling, class imbalance, subgroup performance and at least one explained failure case must be documented. `ml/scripts/run_full_evaluation.py` implements all of this; regenerate model cards with it, never by hand.
3. **Never fabricate.** No invented metrics, dataset counts, citations, users or capabilities. Display only real model outputs. Demonstration data must be explicitly labelled synthetic.
4. **Required disclaimer.** The exact sentence "This project is a prototype and is not medical advice." must remain in the write-up and the UI.
5. **Submission files.** `docs/ONEPAGE_SUBMIT.md` (one-page write-up), `CREDITS.md` (sources), `README.md` (reproducible setup/run/test), plus a public GitHub repo. `PROJECT_STATUS.md` and `DECISIONS.md` must stay current.
6. **Preserve existing work.** Inspect before changing; do not rewrite working code; keep the project running locally (.venv, FastAPI on :8000, Vite on :5173) and the pytest suite green.
