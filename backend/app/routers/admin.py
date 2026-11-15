import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..deps import require_role
from ..models import AuditLog, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
def list_users(role: str = Query(None, pattern="^(patient|clinician|researcher|admin)$"),
               _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):  # noqa: B008
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    users = db.scalars(stmt).all()
    return {"users": [schemas.UserOut.model_validate(u).model_dump() for u in users]}


@router.get("/audit-logs")
def audit_logs(limit: int = Query(50, ge=1, le=500),
               _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):  # noqa: B008
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return {"logs": [
        {"id": r.id, "actor": r.actor_user_id, "action": r.action,
         "detail": json.loads(r.detail_json or "{}"), "created_at": r.created_at.isoformat()}
        for r in rows
    ]}


router_research = APIRouter(prefix="/api/research", tags=["research"])


@router_research.get("/datasets")
def dataset_manifest(_: User = Depends(require_role("researcher", "admin"))):  # noqa: B008
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "ml" / "data" / "manifest.json"
    if not path.exists():
        return {"manifest": {}, "note": "datasets not downloaded yet"}
    return {"manifest": json.loads(path.read_text(encoding="utf-8"))}


@router_research.get("/models")
def all_cards(_: User = Depends(require_role("researcher", "admin"))):  # noqa: B008
    from pathlib import Path

    cards = {}
    for card_path in sorted((Path(__file__).resolve().parents[2] / "ml" / "artifacts").glob("*/model_card.json")):
        cards[card_path.parent.name] = json.loads(card_path.read_text(encoding="utf-8"))
    return {"model_cards": cards}