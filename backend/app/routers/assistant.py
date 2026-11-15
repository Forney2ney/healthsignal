from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, ModelOutput, PatientProfile, User
from .. import knowledge as kb

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/ask", response_model=schemas.AnswerOut)
def ask(body: schemas.AskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    matched = kb.match(body.question)
    evidence: list[dict] = []
    sources: list[str] = []
    parts: list[str] = [kb.GENERAL]

    if "emergency" in matched:
        parts.append(kb.TOPICS["emergency"]["snippet"])
        sources += kb.TOPICS["emergency"]["sources"]

    profile = None
    profiles = db.scalars(select(PatientProfile).where(PatientProfile.owner_id == user.id)).all()
    if profiles:
        profile = profiles[0]  # evidence scope is the user's first (or only) profile

    for key in matched:
        topic = kb.TOPICS[key]
        parts.append(f"{topic['title']}: {topic['snippet']}")
        sources += topic["sources"]

    if profile is not None:
        meas = sorted(profile.measurements, key=lambda m: m.observed_at)
        if meas:
            latest: dict[str, object] = {}
            for m in meas:
                latest[m.kind] = m.value
            evidence.append({"source": "your stored measurements", "facts": latest})

        outs = db.scalars(select(ModelOutput).where(ModelOutput.profile_id == profile.id)).all()
        for o in outs:
            import json

            data = json.loads(o.result_json)
            evidence.append({
                "source": f"stored model output ({o.model_key})",
                "probability": data.get("probability"),
                "interpretation": data.get("interpretation"),
            })
        if not outs:
            parts.append(
                "No stored model outputs exist for your profile yet, so I cannot quote any "
                "prediction. Missing information is disclosed rather than estimated."
            )
    else:
        parts.append("You have no stored health profile yet, so no personal facts can be quoted.")

    if not matched and not evidence:
        parts.append(
            "I could not ground an answer in the available information. This assistant only "
            "cites your own data, stored model outputs, and listed references."
        )

    db.add(AuditLog(actor_user_id=user.id, action="assistant.ask",
                    detail_json='{"matched":' + str(len(matched)) + '}'))
    db.commit()

    return schemas.AnswerOut(
        answer="\n\n".join(parts),
        evidence=evidence,
        uncertainty=(
            "This retrieval-based assistant has no generative model and cannot infer facts "
            "that are not stored or in the listed references. It cannot diagnose and cannot "
            "assess emergencies."
        ),
        sources=sorted(set(sources)),
    )