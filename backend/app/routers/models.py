import json

from .. import ml_bridge  # noqa: F401  (puts ml/src on sys.path)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, ModelOutput, PatientProfile, User
from healthsignal_ml import model_registry

router = APIRouter(prefix="/api", tags=["models"])

SAFE_HARBOUR = (
    "HealthSignal is a research/educational prototype, not a medical device. "
    "Scores are statistical indicators from small public datasets, not validated "
    "individual disease probabilities, and not diagnoses. Always discuss results "
    "with a qualified healthcare professional; seek urgent care for emergencies."
)

DOMAIN_META = model_registry.DOMAIN_META


def _held_out_metrics(card: dict) -> dict:
    """Read held-out test metrics from either card schema version."""
    methodology = card.get("methodology", {})
    if "held_out_test_metrics" in methodology:
        return methodology["held_out_test_metrics"]
    return methodology.get("final_metrics_on_held_out_test", {})


def _baseline(card: dict) -> dict:
    base = card.get("methodology", {}).get("baselines_on_same_test_split", {})
    stratified = base.get("baseline_stratified_random", {})
    return {"baseline_roc_auc": stratified.get("roc_auc"),
            "baseline_note": "stratified-random dummy on the same held-out split"}


def _available() -> list[str]:
    return model_registry.available_models()


@router.get("/models")
def list_models():
    out = []
    for key in _available():
        handle = model_registry.load_model(key)
        card = handle.card
        metrics = _held_out_metrics(card)
        performance = {k: metrics[k] for k in ("roc_auc", "pr_auc", "recall_sensitivity", "specificity", "f1", "brier", "n") if k in metrics}
        performance.update(_baseline(card))
        performance["false_positives"] = metrics.get("false_positives")
        performance["false_negatives"] = metrics.get("false_negatives")
        out.append({
            "model_key": key,
            "model_name": card["model_name"],
            "model_type": card["model_type"],
            "prediction_task": card["prediction_task"],
            "system": DOMAIN_META[key]["system"],
            "human_task": DOMAIN_META[key]["human_task"],
            "dataset": card["dataset"],
            "performance": performance,
            "subgroup_performance": card.get("methodology", {}).get("subgroup_performance", {}),
            "feature_schema": handle.feature_schema,
            "intended_use": card["intended_use"],
            "limitations": card["limitations"],
            "safe_harbour": SAFE_HARBOUR,
        })
    return {"models": out, "safe_harbour": SAFE_HARBOUR}


@router.get("/models/{model_key}")
def model_detail(model_key: str):
    if model_key not in _available():
        raise HTTPException(status_code=404, detail="unknown model")
    handle = model_registry.load_model(model_key)
    return {"card": handle.card, "feature_schema": handle.feature_schema, "safe_harbour": SAFE_HARBOUR}


@router.post("/predictions/tabular", response_model=schemas.PredictionOut)
def predict(body: schemas.PredictionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.model_key not in _available():
        raise HTTPException(status_code=404, detail=f"model '{body.model_key}' not available")
    try:
        result = model_registry.predict(body.model_key, body.values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"inference failed: {exc}")

    if body.save_to_profile:
        profile = db.get(PatientProfile, body.save_to_profile)
        if profile is None or profile.owner_id != user.id:
            raise HTTPException(status_code=404, detail="target profile not found")
        db.add(ModelOutput(
            profile_id=profile.id, model_key=body.model_key,
            inputs_json=json.dumps(result["provided_features"]),
            result_json=json.dumps(result),
        ))
        db.add(AuditLog(actor_user_id=user.id, action="prediction.tabular",
                        detail_json=json.dumps({"model": body.model_key})))
        db.commit()

    return schemas.PredictionOut(
        model_key=result["model_key"],
        model_name=result["model_name"],
        probability=result["probability"],
        probability_interpretation=result["interpretation"],
        provided_features=result["provided_features"],
        imputed_features=result["imputed_features"],
        explanation=schemas.ExplanationOut(
            method=result["explanation"]["method"],
            top_features=[
                schemas.FeatureContribution(**f) for f in result["explanation"]["top_features"]
            ],
            note=result["explanation"]["note"],
        ) if result["explanation"] else None,
        limitations=result["limitations"],
        safe_harbour=SAFE_HARBOUR,
    )