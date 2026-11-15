"""Curated, cited knowledge snippets for the evidence-grounded assistant.

The assistant has NO generative LLM. It can only:
  1. quote facts from the user's own stored inputs and model outputs,
  2. quote the curated snippets below (each with a source),
  3. state uncertainty and recommend professional evaluation.

Every snippet describes what its underlying dataset/model can and cannot support.
Sources are canonical clinical-research references, cited by name and URL.
"""

UNKNOWN = "not in the available information"

TOPICS: dict[str, dict] = {
    "heart": {
        "keywords": ["heart", "cardiovascular", "cardio", "angina", "ecg", "chest pain",
                     "st segment", "thal", "vessels", "blood pressure", "cholesterol"],
        "title": "Heart disease indicator model",
        "snippet": (
            "The heart model predicts an angiographic heart-disease indicator from 13 clinical "
            "measurements. Its inputs include chest-pain type, exercise-induced angina, ST "
            "depression, maximum heart rate and major vessels seen on fluoroscopy. "
            "A high score indicates statistical resemblance to the positive cases in its "
            "training cohort (Cleveland, 1988)."
        ),
        "sources": [
            "UCI Heart Disease dataset: https://archive.ics.uci.edu/dataset/45/heart+disease",
            "NHLBI heart disease information: https://www.nhlbi.nih.gov/health/heart-disease",
        ],
    },
    "diabetes": {
        "keywords": ["diabetes", "glucose", "hba1c", "insulin", "bmi", "sugar", "metabolic"],
        "title": "Diabetes screening indicator model",
        "snippet": (
            "The diabetes model screens for the test outcome used in the Pima Indians dataset "
            "from glucose, blood pressure, BMI and a family-history pedigree score. It does not "
            "diagnose diabetes: diagnosis requires laboratory testing interpreted by a clinician."
        ),
        "sources": [
            "Pima Indians Diabetes dataset (original NIDDK data): public dataset mirror - see model card",
            "ADA Standards of Care overview: https://diabetes.org/",
        ],
    },
    "kidney": {
        "keywords": ["kidney", "ckd", "creatinine", "urea", "dialysis", "renal", "urine"],
        "title": "Chronic kidney disease indicator model",
        "snippet": (
            "The kidney model classifies chronic kidney disease from 24 clinical and laboratory "
            "measurements. Physiologically impossible zero values in metabolic datasets are "
            "treated as missing, never as zero, and missing inputs are disclosed rather than "
            "silently imputed."
        ),
        "sources": [
            "UCI Chronic Kidney Disease dataset: https://archive.ics.uci.edu/dataset/336",
            "National Kidney Foundation: https://www.kidney.org/",
        ],
    },
    "liver": {
        "keywords": ["liver", "hepatic", "bilirubin", "alt", "ast", "sgpt", "sgot", "albumin"],
        "title": "Liver condition indicator model",
        "snippet": (
            "The liver model flags increased likelihood of being categorised as a liver patient "
            "from liver function tests. That label groups several liver conditions and cannot "
            "distinguish between them."
        ),
        "sources": [
            "UCI ILPD liver patient records: https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset",
            "American Liver Foundation: https://liverfoundation.org/",
        ],
    },
    "breast": {
        "keywords": ["breast", "tumour", "tumor", "malignant", "wdbc", "mass", "radius_mean",
                     "concavity", "fna"],
        "title": "Breast mass malignancy indicator model",
        "snippet": (
            "The breast model classifies fine-needle-aspirate image features as malignant or "
            "benign. The 30 features describe digitised cell-nucleus measurements from imaging, "
            "not patient history, so it can only be run when such measurements are supplied."
        ),
        "sources": [
            "UCI Breast Cancer Wisconsin (Diagnostic): https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
            "Breastcancer.org: https://www.breastcancer.org/",
        ],
    },
    "xray": {
        "keywords": ["x-ray", "xray", "chest", "image", "grad-cam", "gradcam", "pneumonia",
                     "thoracic", "radiograph"],
        "title": "Chest X-ray pathology model",
        "snippet": (
            "The image model is a DenseNet-121 pretrained on NIH ChestX-ray14, reproducible via "
            "torchxrayvision. It outputs per-pathology scores that depend on the training "
            "cohort's prevalence. Grad-CAM overlays show which image regions influenced the "
            "score; they are model explanations, not diagnostic evidence."
        ),
        "sources": [
            "NIH ChestX-ray14 dataset (public domain images)",
            "torchxrayvision library: https://github.com/mlmed/torchxrayvision",
        ],
    },
    "emergency": {
        "keywords": ["emergency", "urgent", "ambulance", "stroke", "suicide", "can't breathe",
                     "cannot breathe", "heart attack", "unconscious"],
        "title": "Emergency guidance",
        "snippet": (
            "This platform cannot detect or rule out emergencies. If you may be having a "
            "medical emergency, contact your local emergency number immediately (for example "
            "911 in the United States) or go to the nearest emergency department."
        ),
        "sources": ["Emergency services: local emergency number"],
    },
}

GENERAL = (
    "HealthSignal is a research prototype. Answers below come only from your own stored data, "
    "stored model outputs, and a small set of cited public-health references. It does not "
    "diagnose, prescribe, or replace a clinician."
)


def match(question: str) -> list[str]:
    q = question.lower()
    return [key for key, t in TOPICS.items() if any(k in q for k in t["keywords"])]