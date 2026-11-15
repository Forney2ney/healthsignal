# HealthSignal — 6-minute demonstration script

Everything below exercises **real** functionality. Where a feature does not exist, the presenter says so —
that is part of the demo's credibility.

## Setup before the demo

1. `.\.venv\Scripts\python ml\scripts\download_data.py` (datasets) — done once earlier.
2. `.\.venv\Scripts\python ml\scripts\train_all.py` (models) — done once earlier.
3. `.\.venv\Scripts\python backend\scripts\seed_demo.py` (demo users + one SYNTHETIC profile).
4. Backend: `cd backend; ..\.venv\Scripts\python -m uvicorn app.main:app`
5. Frontend: `cd frontend; npm run dev`

## 0:00 — Frame the problem (30 s)

> "HealthSignal is a research prototype that ingests different kinds of health information, runs *separate,
> individually evaluated* models, and shows you its own uncertainty. Nothing you'll see is a diagnosis."

Point at the banner at the top of the page: research prototype, not a medical device.

## 0:30 — Sign in (30 s)

Log in as `patient.demo@healthsignal.dev` (password on the README/login page).

## 1:00 — Dashboard: honesty about data (1 min)

Show the dashboard for the seeded **SYNTHETIC** profile (clearly labelled). Add a measurement live: age, then a
systolic BP. Show that:

- Every value carries unit + timestamp; the completeness panel lists what is present *and what is absent*
  (e.g. "no data recorded" for systems with no input).
- The body map light-up is information, not diagnosis — say it aloud: "an indicator means data present, not
  organ disease".

## 2:00 — Risk models: real models, real metrics (2 min)

Open **Risk models**. Click the heart card. Its panel shows:

- Dataset name and link (UCI Heart Disease, 303 records), held-out metrics: ROC-AUC 0.922, PR-AUC 0.912.
- Click **Load positive example row** — this is a *real de-identified record* from the public dataset. Run it.
- Show the score, the SHAP explanation (top contributing features), and the note that feature importance is
  not causation.
- Switch to **Load negative example row** and run again — the score drops; the same form, same disclosed
  imputation.
- Leave a field blank and run: the output explicitly lists **imputed features** — "we never silently invent your
  data".

Do the same quickly for diabetes (metabolic) and CKD (kidney, with genuinely messy missing data).

## 3:30 — Image analysis: genuine pretrained model (1.5 min)

Open **Image analysis**. Run the **cxr_nih** model on a public-domain NIH sample X-ray.

- Show 14 pathology probabilities, highest label highlighted.
- Show the Grad-CAM overlay next to the original image, and read the caption: "highlights activations, not
  evidence of disease".
- Upload a non-CXR image (e.g. any PNG) and note: the model only accepts chest X-rays; other inputs are
  meaningless by design — say that limitation is real, not hidden.

## 5:00 — Reports + assistant (1 min)

- **Reports**: generate the clinician report for the demo profile; show that it lists patient-provided
  measurements, model outputs with the exact interpretation text, imputed fields, limitations, and the
  AI-generated/not-a-diagnosis statement. Download the markdown.
- **Assistant**: ask "what does my heart model output mean?" — show it answers *only* from the user's stored
  data and cited references; ask something impossible ("my unicorn test") and show it responds with grounded
  uncertainty rather than invention.

## 5:30 — Research workspace + close (30 s)

Log in as `researcher.demo@healthsignal.dev` → **Research workspace**: dataset manifest with verified row
counts and full model cards — and no patient data (the permission is enforced by the API, not the UI).

Close: "Five tabular models and one published imaging model, each with documented metrics and limitations;
everything else on the screen is architecture, not claims."