"""Chest X-ray inference for HealthSignal using torchxrayvision pretrained DenseNet-121.

Models (verified downloadable, 28.4 MB weights each, GitHub release v1):
  * nih  - multi-label thoracic pathology classifier trained on NIH ChestX-ray14
           (per-pathology AUCs published by the library authors:
           Cohen et al., "Torchxrayvision: A library of chest X-ray datasets
           and models", MIDL 2022)
  * pc   - pediatric pneumonia classifier trained on the Kaggle CXR pneumonia set

Every returned probability is a dataset-dependent, uncalibrated research
indicator. It is NOT a validated individual probability of disease.
"""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

IMAGING_AVAILABLE = True
try:
    import cv2
    import torch
    import torchxrayvision as xrv
    from pytorch_grad_cam import GradCAM
    from pytorch_grad_cam.utils.image import show_cam_on_image
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
except Exception as exc:  # pragma: no cover - only when optional deps are missing
    IMAGING_AVAILABLE = False
    _IMPORT_ERROR = str(exc)

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"
WEIGHTS_DIR = ARTIFACTS_DIR / "xrv_weights"

IMAGE_MODELS: dict[str, dict[str, Any]] = {
    "cxr_nih": {
        "display_name": "Chest X-ray pathology classifier (DenseNet-121, NIH ChestX-ray14 weights)",
        "weights": "nih",
        "kind": "multilabel",
    },
    "cxr_pc": {
        "display_name": "Pediatric pneumonia classifier (DenseNet-121, Kaggle pneumonia weights)",
        "weights": "pc",
        "kind": "binary",
    },
}

_CACHE: dict[str, Any] = {}


def imaging_status() -> dict:
    if IMAGING_AVAILABLE:
        return {"available": True}
    return {"available": False, "reason": _IMPORT_ERROR}


def _load_model(key: str):
    if not IMAGING_AVAILABLE:
        raise RuntimeError(f"imaging dependencies unavailable: {_IMPORT_ERROR}")
    if key not in _CACHE:
        import sys

        WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        # torchxrayvision's downloader writes a unicode progress bar; make stdout utf-8
        # capable on Windows consoles so the download cannot crash on cp1252.
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
        model = xrv.models.DenseNet(
            weights=IMAGE_MODELS[key]["weights"],
            apply_sigmoid=True,
            cache_dir=str(WEIGHTS_DIR),
        )
        model.eval()
        _CACHE[key] = model
    return _CACHE[key]


def load_xray_image(path: str | Path) -> np.ndarray:
    """Load an X-ray as a normalized single-channel float array (cv2/torchxrayvision path)."""
    if not IMAGING_AVAILABLE:
        raise RuntimeError(f"imaging dependencies unavailable: {_IMPORT_ERROR}")
    img = xrv.utils.load_image(str(path))  # -> 2D normalized [-1024,1024], or [1,H,W] for DICOM
    if img.ndim == 3:
        img = img[0]
    return img.astype(np.float32)


def preprocess_tensor(img: np.ndarray) -> "torch.Tensor":
    x = torch.from_numpy(img)[None, None, ...]
    return x


def _display_rgb(img: np.ndarray) -> np.ndarray:
    lo, hi = float(img.min()), float(img.max())
    norm = (img - lo) / (hi - lo + 1e-8)
    rgb = np.stack([norm] * 3, axis=-1).astype(np.float32)
    rgb = cv2.resize(rgb, (224, 224))
    return rgb


def analyze_image(path: str | Path, model_key: str = "cxr_nih",
                  with_gradcam: bool = True, topk: int | None = None) -> dict:
    """Run X-ray inference and optionally produce a Grad-CAM overlay.

    Returns predictions (label -> probability), and, for Grad-CAM, an overlay of
    the image region that most influenced the highest-scoring label. A CAM
    highlights activations, it does NOT establish disease.
    """
    started = time.time()
    model = _load_model(model_key)
    img = load_xray_image(path)
    x = preprocess_tensor(img)

    with torch.no_grad():
        logits = model(x)
    logits = logits.cpu().numpy()[0]

    labels = list(model.pathologies)
    scores = {label: float(v) for label, v in zip(labels, logits)}
    if topk:
        scores = dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:topk])

    result: dict[str, Any] = {
        "model_key": model_key,
        "model_name": IMAGE_MODELS[model_key]["display_name"],
        "labels": labels,
        "probabilities": scores,
        "highest_label": max(scores, key=scores.get) if scores else None,
        "probability_interpretation": (
            "Uncalibrated dataset-dependent score. Not an individual disease probability; "
            "threshold depends on the population the model was trained on."
        ),
        "inference_ms": int((time.time() - started) * 1000),
    }

    if with_gradcam and IMAGE_MODELS[model_key]["kind"] == "multilabel":
        best_idx = labels.index(result["highest_label"])
        cam = GradCAM(model=model, target_layers=[model.features.norm5])
        targets = [ClassifierOutputTarget(best_idx)]
        grayscale_cam = cam(input_tensor=x, targets=targets)[0]
        display = _display_rgb(img)
        # the CAM mask matches the model input resolution; align it to the 224x224 display
        if grayscale_cam.shape != display.shape[:2]:
            grayscale_cam = cv2.resize(grayscale_cam, (display.shape[1], display.shape[0]),
                                       interpolation=cv2.INTER_LINEAR)
        overlay = show_cam_on_image(display, grayscale_cam, use_rgb=True, image_weight=0.6)
        grayscale_cam = None  # type: ignore[assignment]
        overlay_bgr = cv2.cvtColor((overlay * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        _, png = cv2.imencode(".png", overlay_bgr)
        result["gradcam"] = {
            "target_label": result["highest_label"],
            "cam_explanation": (
                "Grad-CAM highlights the image regions with the strongest gradient-weighted "
                "activation for the selected label. It is a model-explanation visual, not "
                "evidence that a finding exists or that a disease is present."
            ),
            "overlay_png_b64": base64.b64encode(png.tobytes()).decode(),
        }

    return result


def model_card(key: str = "cxr_nih") -> dict:
    meta = IMAGE_MODELS[key]

    def weight_url() -> str:
        try:
            from torchxrayvision.models import model_urls
            return model_urls[meta["weights"]]["weights_url"]
        except Exception:
            return ""

    card = {
        "model_name": f"healthsignal-{key}-v1",
        "model_type": "torchxrayvision DenseNet-121 (pretrained)",
        "library": f"torchxrayvision=={__import__('torchxrayvision').__version__}",
        "weights": meta["weights"],
        "weights_url": weight_url(),
        "prediction_task": meta["display_name"],
        "training_data": {
            "nih": "NIH ChestX-ray14 (112,120 frontal-view chest X-rays, 14 thoracic pathologies)",
            "pc": "Kaggle Chest X-Ray Images (Pneumonia), pediatric patients",
        }[meta["weights"]],
        "published_evaluation": (
            "Per-pathology AUCs were published by the torchxrayvision authors "
            "(Cohen et al., 'Torchxrayvision: A library of chest X-ray datasets and "
            "models', MIDL 2022). Weights are used as released; we did NOT re-validate "
            "them on a held-out set in this project and did not fine-tune them."
        ),
        "preprocessing": (
            "Input loaded and scaled to roughly [-1024, 1024] gray scale via "
            "torchxrayvision.utils.load_image; the model resizes to its trained resolution."
        ),
        "limitations": [
            "Trained on frontal chest X-rays; non-CXR images or CT/MRI/ultrasound are invalid inputs.",
            "Probabilities are uncalibrated and prevalence-dependent; not validated for individual risk.",
            "Grad-CAM overlays are activation explanations, not diagnostic evidence.",
            "No local re-validation was performed; metrics quoted are from the original publications.",
        ],
        "intended_use": "Research and educational demonstration of explainable medical-image analysis.",
    }
    return card


def write_image_model_cards() -> dict:
    if not IMAGING_AVAILABLE:
        return {}
    cards = {}
    for key in IMAGE_MODELS:
        c = model_card(key)
        out = ARTIFACTS_DIR / key
        out.mkdir(parents=True, exist_ok=True)
        (out / "model_card.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
        cards[key] = c
    return cards