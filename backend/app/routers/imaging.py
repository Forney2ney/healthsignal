import json
import secrets
from pathlib import Path

from .. import ml_bridge  # noqa: F401
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, ImageAnalysis, ImagingStudy, User
from ..validation import check_magic, validate_upload
from healthsignal_ml import imaging as hsimaging

settings = get_settings()
router = APIRouter(prefix="/api/imaging", tags=["imaging"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
SAMPLES_DIR = Path(__file__).resolve().parents[2] / "assets" / "samples"

SAFE = (
    "Image analyses are research demonstrations from a pretrained model. A CAM overlay "
    "highlights model activations, not evidence of disease. This is not a diagnosis; "
    "always obtain professional interpretation of any medical image."
)


@router.get("/status")
def status():
    return {"available": hsimaging.IMAGING_AVAILABLE, "safe_harbour": SAFE}


@router.get("/samples")
def samples():
    if not SAMPLES_DIR.exists():
        return {"samples": []}
    return {"samples": [p.name for p in sorted(SAMPLES_DIR.glob("*")) if p.suffix.lower() in (".png", ".jpg", ".jpeg")]}


@router.get("/samples/{name}")
def sample_image(name: str):
    path = SAMPLES_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="sample not found")
    return FileResponse(path)


@router.post("/upload", status_code=201)
def upload(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    name = file.filename or "upload"
    ext, error = validate_upload(name, file.content_type, len(content), settings.max_upload_mb)
    if error:
        raise HTTPException(status_code=422, detail=error)
    if not check_magic(ext, content[:16]):
        raise HTTPException(status_code=422, detail="file content does not match its extension")
    import hashlib

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{secrets.token_hex(16)}{ext}"
    (UPLOAD_DIR / stored_name).write_bytes(content)
    study = ImagingStudy(
        profile_id=None, filename=name, stored_path=str(UPLOAD_DIR / stored_name),
        content_type=file.content_type or "application/octet-stream",
        modality="xray" if ext != ".dcm" else "unknown",
        size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
    )
    db.add(study)
    db.add(AuditLog(actor_user_id=user.id, action="imaging.upload",
                    detail_json=json.dumps({"study": study.id, "ext": ext})))
    db.commit()
    db.refresh(study)
    return {"study_id": study.id, "filename": name, "modality": study.modality}


@router.post("/analyze/{study_id}", response_model=schemas.ImagingRunOut)
def analyze(study_id: int, body: schemas.ImagingRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    study = db.get(ImagingStudy, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail="study not found")
    if not hsimaging.IMAGING_AVAILABLE:
        raise HTTPException(status_code=503, detail="imaging dependencies unavailable on this deployment")
    try:
        result = hsimaging.analyze_image(study.stored_path, model_key=body.model_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"inference failed: {exc}")
    analysis = ImageAnalysis(study_id=study.id, model_key=body.model_key, result_json=json.dumps(result))
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return schemas.ImagingRunOut(
        study_id=study.id, model_key=body.model_key, model_name=result["model_name"],
        labels=result["labels"], probabilities=result["probabilities"],
        highest_label=result["highest_label"],
        probability_interpretation=result["probability_interpretation"] + " " + SAFE,
        gradcam=result.get("gradcam"), inference_ms=result["inference_ms"],
    )


@router.post("/analyze-sample", response_model=schemas.ImagingRunOut)
def analyze_sample(body: schemas.ImagingRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not body.sample_file:
        raise HTTPException(status_code=400, detail="sample_file is required")
    path = SAMPLES_DIR / body.sample_file
    if not path.is_file():
        raise HTTPException(status_code=404, detail="sample not found")
    if not hsimaging.IMAGING_AVAILABLE:
        raise HTTPException(status_code=503, detail="imaging dependencies unavailable on this deployment")
    try:
        result = hsimaging.analyze_image(path, model_key=body.model_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"inference failed: {exc}")
    return schemas.ImagingRunOut(
        study_id=0, model_key=body.model_key, model_name=result["model_name"],
        labels=result["labels"], probabilities=result["probabilities"],
        highest_label=result["highest_label"],
        probability_interpretation=result["probability_interpretation"] + " " + SAFE,
        gradcam=result.get("gradcam"), inference_ms=result["inference_ms"],
    )