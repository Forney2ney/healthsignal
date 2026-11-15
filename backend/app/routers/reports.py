import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, ModelOutput, PatientProfile, User

router = APIRouter(prefix="/api/reports", tags=["reports"])

SAFE_HARBOUR = (
    "AI-GENERATED RESEARCH OUTPUT - NOT A MEDICAL DIAGNOSIS. Produced by HealthSignal, an "
    "educational prototype. Nothing here is a validated individual risk estimate or a "
    "diagnosis, and no treatment is implied. Review with a qualified healthcare professional."
)


def _collect(profile: PatientProfile, db: Session) -> dict:
    measurements: dict[str, object] = {}
    for m in profile.measurements:
        measurements.setdefault(m.kind, m.value)
    outputs = db.scalars(select(ModelOutput).where(ModelOutput.profile_id == profile.id)).all()
    model_outputs = []
    for o in outputs:
        data = json.loads(o.result_json)
        model_outputs.append({
            "model_key": o.model_key,
            "probability": data.get("probability"),
            "interpretation": data.get("interpretation"),
            "inputs": data.get("provided_features"),
            "imputed_features": data.get("imputed_features"),
            "performance": data.get("performance"),
            "created_at": o.created_at.isoformat(),
        })
    return {
        "profile_id": profile.id,
        "profile_label": profile.label,
        "is_synthetic": profile.is_synthetic,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "patient_provided": {"measurements": measurements},
        "model_outputs": model_outputs,
        "missing": [],  # filled by caller against model feature schemas
        "limitations": [
            "Small, unrepresentative public datasets; no external validation performed.",
            "Scores are uncalibrated research indicators, not clinical probabilities.",
            "Missing inputs were imputed by the training pipeline and are listed per output.",
            "The chest X-ray model was not re-validated locally.",
        ],
        "safe_harbour": SAFE_HARBOUR,
    }


@router.get("/profile/{profile_id}")
def clinician_report(profile_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(PatientProfile, profile_id)
    if profile is None or profile.owner_id != user.id:
        raise HTTPException(status_code=404, detail="profile not found")
    report = _collect(profile, db)
    db.add(AuditLog(actor_user_id=user.id, action="report.generate",
                    detail_json=json.dumps({"profile": profile_id})))
    db.commit()
    return report


@router.get("/profile/{profile_id}/markdown")
def clinician_report_markdown(profile_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(PatientProfile, profile_id)
    if profile is None or profile.owner_id != user.id:
        raise HTTPException(status_code=404, detail="profile not found")
    r = _collect(profile, db)
    lines = [
        "# HealthSignal report (AI-generated, not a diagnosis)",
        "",
        f"- Profile: {r['profile_label']}{' (SYNTHETIC demo profile)' if r['is_synthetic'] else ''}",
        f"- Generated: {r['generated_at']}",
        "",
        "## Patient-provided measurements",
    ]
    if r["patient_provided"]["measurements"]:
        for k, v in r["patient_provided"]["measurements"].items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- none recorded")
    lines.append("\n## Model outputs")
    if r["model_outputs"]:
        for o in r["model_outputs"]:
            lines.append(
                f"- {o['model_key']}: score {o['probability']:.1%} - {o['interpretation']}"
            )
    else:
        lines.append("- none")
    lines.append(f"\n## Limitations\n" + "\n".join(f"- {x}" for x in r["limitations"]))
    lines.append(f"\n---\n\n> {r['safe_harbour']}")
    return Response("\n".join(lines), media_type="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename=healthsignal-report-{profile_id}.md"})