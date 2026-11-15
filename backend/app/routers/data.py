from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, Measurement, ModelOutput, PatientProfile, QuestionnaireAnswer, RecordNote, ShareGrant, User
from ..validation import MEASUREMENT_SPECS, validate_measurement

router = APIRouter(prefix="/api", tags=["data"])


def _owned_profile(profile_id: int, user: User, db: Session) -> PatientProfile:
    profile = db.get(PatientProfile, profile_id)
    if profile is None or profile.owner_id != user.id:
        raise HTTPException(status_code=404, detail="profile not found")
    return profile


# ------------------------------------------------------------------ profiles
@router.post("/profiles", response_model=schemas.ProfileOut, status_code=201)
def create_profile(body: schemas.ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = PatientProfile(owner_id=user.id, label=body.label, is_synthetic=body.is_synthetic)
    db.add(profile)
    db.add(AuditLog(actor_user_id=user.id, action="profile.create", detail_json='{}'))
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profiles", response_model=list[schemas.ProfileOut])
def list_profiles(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(PatientProfile).where(PatientProfile.owner_id == user.id)).all()


@router.get("/profiles/{profile_id}/completeness")
def profile_completeness(profile_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _owned_profile(profile_id, user, db)
    kinds = sorted({m.kind for m in profile.measurements})
    groups = {
        "body": [k for k in kinds if k in ("age", "height_cm", "weight_kg")],
        "cardiovascular": [k for k in kinds if k in ("systolic_bp", "diastolic_bp", "heart_rate", "spo2")],
        "metabolic": [k for k in kinds if k in ("glucose_fasting", "hba1c", "total_cholesterol", "hdl", "ldl", "triglycerides")],
        "liver": [k for k in kinds if k in ("alt", "ast", "bilirubin_total", "albumin")],
        "kidney": [k for k in kinds if k in ("creatinine", "urea", "egfr")],
        "blood": [k for k in kinds if k in ("hemoglobin", "wbc", "platelets")],
        "inflammatory": [k for k in kinds if k == "temperature_c"],
    }
    return {
        "profile_id": profile_id,
        "is_synthetic": profile.is_synthetic,
        "measurement_kinds": kinds,
        "measurement_count": len(profile.measurements),
        "questionnaire_answers": len(profile.questionnaire),
        "imaging_studies": len(profile.studies),
        "model_outputs": len(profile.outputs),
        "groups": groups,
        "available_measurement_kinds": sorted(MEASUREMENT_SPECS.keys()),
    }


# ------------------------------------------------------------------ measurements
@router.post("/profiles/{profile_id}/measurements", response_model=schemas.MeasurementOut, status_code=201)
def add_measurement(profile_id: int, body: schemas.MeasurementIn,
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _owned_profile(profile_id, user, db)
    result = validate_measurement(body.kind, body.value, body.unit)
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)
    m = Measurement(
        profile_id=profile.id, kind=body.kind, value=result.value, unit=result.unit,
        observed_at=body.observed_at or datetime.now(timezone.utc), source=body.source,
    )
    db.add(m)
    db.add(AuditLog(actor_user_id=user.id, action="measurement.create", detail_json='{"kind":"' + body.kind + '"}'))
    db.commit()
    db.refresh(m)
    return m


@router.get("/profiles/{profile_id}/measurements", response_model=list[schemas.MeasurementOut])
def list_measurements(profile_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                      kind: str | None = None):
    profile = _owned_profile(profile_id, user, db)
    stmt = select(Measurement).where(Measurement.profile_id == profile.id).order_by(Measurement.observed_at)
    if kind:
        stmt = stmt.where(Measurement.kind == kind)
    return db.scalars(stmt).all()


@router.delete("/measurements/{measurement_id}", status_code=204)
def delete_measurement(measurement_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.get(Measurement, measurement_id)
    if m is None:
        raise HTTPException(status_code=404, detail="measurement not found")
    profile = db.get(PatientProfile, m.profile_id)
    if profile is None or profile.owner_id != user.id:
        raise HTTPException(status_code=404, detail="measurement not found")
    db.delete(m)
    db.add(AuditLog(actor_user_id=user.id, action="measurement.delete", detail_json='{"id":' + str(measurement_id) + '}'))
    db.commit()


# ------------------------------------------------------------------ questionnaires
@router.post("/profiles/{profile_id}/questionnaire", status_code=201)
def answer_questionnaire(profile_id: int, body: schemas.QuestionnaireIn,
                         user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _owned_profile(profile_id, user, db)
    for key, answer in body.answers.items():
        db.add(QuestionnaireAnswer(profile_id=profile.id, question_key=str(key)[:64], answer=str(answer)[:255]))
    db.add(AuditLog(actor_user_id=user.id, action="questionnaire.create", detail_json='{}'))
    db.commit()
    return {"saved": len(body.answers)}


# ------------------------------------------------------------------ notes / history
@router.post("/profiles/{profile_id}/notes", status_code=201)
def add_note(profile_id: int, body: schemas.NoteIn,
             user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _owned_profile(profile_id, user, db)
    note = RecordNote(profile_id=profile.id, note_type=body.note_type, text=body.text)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "note_type": note.note_type}


# ------------------------------------------------------------------ sharing (patient-controlled)
@router.post("/profiles/{profile_id}/grants", status_code=201)
def grant_access(profile_id: int, clinician_email: str = Query(..., description="email of the clinician to grant access to"),
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _owned_profile(profile_id, user, db)
    clinician = db.scalar(select(User).where(User.email == clinician_email))
    if clinician is None:
        raise HTTPException(status_code=404, detail="no user with that email")
    if clinician.role not in ("clinician", "admin"):
        raise HTTPException(
            status_code=400,
            detail="grants may only be made to clinician/admin accounts; clinicians still require verification",
        )
    grant = ShareGrant(profile_id=profile.id, granted_to_user_id=clinician.id)
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return {"grant_id": grant.id, "granted_to": clinician.email}


@router.get("/profiles/shared-with-me")
def shared_with_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ("clinician", "admin"):
        raise HTTPException(status_code=403, detail="clinician role required")
    grants = db.scalars(select(ShareGrant).where(ShareGrant.granted_to_user_id == user.id, ShareGrant.revoked == False)).all()
    out = []
    for g in grants:
        profile = db.get(PatientProfile, g.profile_id)
        if profile is None:
            continue
        out.append({
            "grant_id": g.id,
            "profile_id": profile.id,
            "label": profile.label,
            "is_synthetic": profile.is_synthetic,
            "measurements": len(profile.measurements),
            "model_outputs": len(profile.outputs),
        })
    return {"shared_profiles": out}


@router.get("/profiles/{profile_id}/timeline")
def timeline(profile_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _owned_profile(profile_id, user, db)
    entries = [
        {"type": "measurement", "kind": m.kind, "value": m.value, "unit": m.unit,
         "observed_at": m.observed_at.isoformat(), "source": m.source}
        for m in sorted(profile.measurements, key=lambda x: x.observed_at)
    ]
    entries += [
        {"type": "model_output", "model_key": o.model_key, "created_at": o.created_at.isoformat()}
        for o in sorted(profile.outputs, key=lambda x: x.created_at)
    ]
    entries += [
        {"type": "imaging_study", "filename": s.filename, "created_at": s.created_at.isoformat()}
        for s in sorted(profile.studies, key=lambda x: x.created_at)
    ]
    return {"profile_id": profile_id, "entries": entries}