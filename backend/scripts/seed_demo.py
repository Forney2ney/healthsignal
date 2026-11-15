"""Seed clearly-labelled SYNTHETIC demo data for the hackathon demonstration.

The synthetic profile is generated from public dataset statistics and is
permanently flagged is_synthetic=True everywhere it appears in the UI. It is
NOT patient data and must never be presented as real medical information.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import ml_bridge  # noqa: E402,F401  (adds ml/src to sys.path)
from healthsignal_ml import model_registry  # noqa: E402

from app import ml_bridge  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Measurement, ModelOutput, PatientProfile, ShareGrant, User  # noqa: E402
from app.security import hash_password  # noqa: E402

DEV_PASSWORD = "healthsignal-demo-pw-2026"

USERS = [
    ("patient.demo@healthsignal.dev", "Demo Patient", "patient"),
    ("clinician.demo@healthsignal.dev", "Demo Clinician", "clinician"),
    ("researcher.demo@healthsignal.dev", "Demo Researcher", "researcher"),
    ("admin.demo@healthsignal.dev", "Demo Admin", "admin"),
]

MEASUREMENTS = [
    ("age", 58, "years"),
    ("systolic_bp", 138, "mmHg"),
    ("diastolic_bp", 82, "mmHg"),
    ("heart_rate", 76, "bpm"),
    ("glucose_fasting", 121, "mg/dL"),
    ("hba1c", 5.8, "%"),
    ("total_cholesterol", 225, "mg/dL"),
    ("hdl", 42, "mg/dL"),
    ("ldl", 148, "mg/dL"),
    ("triglycerides", 165, "mg/dL"),
    ("creatinine", 1.0, "mg/dL"),
    ("alt", 24, "U/L"),
    ("ast", 26, "U/L"),
    ("hemoglobin", 14.2, "g/dL"),
    ("weight_kg", 84, "kg"),
    ("height_cm", 172, "cm"),
]

HEART_INPUTS = {
    "age": 58, "sex": "1", "cp": "2", "trestbps": 138, "chol": 225, "fbs": "1",
    "restecg": "0", "thalach": 152, "exang": "0", "oldpeak": 0.8, "slope": "1",
    "ca": "0", "thal": "3",
}
DIABETES_INPUTS = {
    "age": 58, "glucose": 121, "bloodpressure": 82, "bmi": 28.4,
    "pedigree": 0.35, "pregnancies": 2, "skinfold": None, "insulin": None,
}

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    if db.query(User).count() > 0:
        print("database already seeded; nothing to do")
        sys.exit(0)

    created = {}
    for email, name, role in USERS:
        u = User(email=email, full_name=name, hashed_password=hash_password(DEV_PASSWORD), role=role)
        db.add(u)
        db.flush()
        created[email] = u

    profile = PatientProfile(owner_id=created[USERS[0][0]].id,
                             label="SYNTHETIC demo profile (generated from public dataset statistics)",
                             is_synthetic=True)
    db.add(profile)
    db.flush()

    for kind, value, unit in MEASUREMENTS:
        db.add(Measurement(profile_id=profile.id, kind=kind, value=value, unit=unit,
                           source="synthetic-demo"))

    for model_key, inputs in (("heart", HEART_INPUTS), ("pima", DIABETES_INPUTS)):
        result = model_registry.predict(model_key, inputs)
        db.add(ModelOutput(profile_id=profile.id, model_key=model_key,
                           inputs_json=json.dumps(result["provided_features"]),
                           result_json=json.dumps(result)))
        print(f"synthetic demo model output: {model_key} -> {result['probability']:.4f}")

    db.add(ShareGrant(profile_id=profile.id, granted_to_user_id=created[USERS[1][0]].id))
    db.commit()
    print("seeded demo users (all roles, dev password set) and ONE synthetic profile")
    print("demo login emails:", ", ".join(u[0] for u in USERS))