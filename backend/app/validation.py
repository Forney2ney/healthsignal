"""Measurement and upload validation.

Missing information must remain missing: values are never silently defaulted.
Every accepted value is checked against a medically plausible range and a
canonical unit. Values outside the range are rejected (or flagged, per config),
never clipped.
"""
from __future__ import annotations

from dataclasses import dataclass

MEASUREMENT_SPECS: dict[str, dict] = {
    "age": {"label": "Age", "unit": "years", "min": 0, "max": 120, "type": "int"},
    "height_cm": {"label": "Height", "unit": "cm", "min": 30, "max": 250, "type": "float"},
    "weight_kg": {"label": "Weight", "unit": "kg", "min": 1, "max": 400, "type": "float"},
    "systolic_bp": {"label": "Systolic blood pressure", "unit": "mmHg", "min": 50, "max": 300, "type": "float"},
    "diastolic_bp": {"label": "Diastolic blood pressure", "unit": "mmHg", "min": 20, "max": 200, "type": "float"},
    "heart_rate": {"label": "Heart rate", "unit": "bpm", "min": 20, "max": 250, "type": "float"},
    "spo2": {"label": "Oxygen saturation", "unit": "%", "min": 50, "max": 100, "type": "float"},
    "temperature_c": {"label": "Temperature", "unit": "C", "min": 25, "max": 45, "type": "float"},
    "glucose_fasting": {"label": "Fasting glucose", "unit": "mg/dL", "min": 20, "max": 900, "type": "float"},
    "glucose_random": {"label": "Random glucose", "unit": "mg/dL", "min": 20, "max": 900, "type": "float"},
    "hba1c": {"label": "HbA1c", "unit": "%", "min": 3, "max": 20, "type": "float"},
    "total_cholesterol": {"label": "Total cholesterol", "unit": "mg/dL", "min": 50, "max": 600, "type": "float"},
    "hdl": {"label": "HDL cholesterol", "unit": "mg/dL", "min": 10, "max": 200, "type": "float"},
    "ldl": {"label": "LDL cholesterol", "unit": "mg/dL", "min": 10, "max": 400, "type": "float"},
    "triglycerides": {"label": "Triglycerides", "unit": "mg/dL", "min": 20, "max": 2000, "type": "float"},
    "creatinine": {"label": "Serum creatinine", "unit": "mg/dL", "min": 0.1, "max": 20, "type": "float"},
    "urea": {"label": "Blood urea", "unit": "mg/dL", "min": 2, "max": 300, "type": "float"},
    "alt": {"label": "ALT", "unit": "U/L", "min": 1, "max": 2000, "type": "float"},
    "ast": {"label": "AST", "unit": "U/L", "min": 1, "max": 2000, "type": "float"},
    "bilirubin_total": {"label": "Total bilirubin", "unit": "mg/dL", "min": 0.1, "max": 40, "type": "float"},
    "albumin": {"label": "Albumin", "unit": "g/dL", "min": 1, "max": 7, "type": "float"},
    "hemoglobin": {"label": "Hemoglobin", "unit": "g/dL", "min": 3, "max": 25, "type": "float"},
    "wbc": {"label": "White blood cell count", "unit": "10^3/uL", "min": 0.5, "max": 100, "type": "float"},
    "platelets": {"label": "Platelet count", "unit": "10^3/uL", "min": 10, "max": 1200, "type": "float"},
    "egfr": {"label": "eGFR (estimated)", "unit": "mL/min/1.73m2", "min": 1, "max": 200, "type": "float"},
}


@dataclass
class ValidationResult:
    ok: bool
    value: float | None
    unit: str
    error: str | None = None


def validate_measurement(kind: str, value, unit: str | None = None) -> ValidationResult:
    spec = MEASUREMENT_SPECS.get(kind)
    if spec is None:
        return ValidationResult(False, None, unit or "", f"unknown measurement kind '{kind}'")
    canonical = spec["unit"]
    if unit is not None and unit.strip() != canonical:
        return ValidationResult(False, None, canonical, f"unit must be '{canonical}', got '{unit}'")
    if value is None:
        return ValidationResult(False, None, canonical, "value is required")
    try:
        v = float(value)
    except (TypeError, ValueError):
        return ValidationResult(False, None, canonical, "value must be numeric")
    if spec["type"] == "int":
        v = float(round(v))
    if not (spec["min"] <= v <= spec["max"]):
        return ValidationResult(
            False, None, canonical,
            f"value {v:g} outside plausible range {spec['min']}-{spec['max']} {canonical}",
        )
    return ValidationResult(True, v, canonical)


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm"}
ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg", "application/dicom"}

MAGIC = {
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".dcm": [b"DICM"],
}


def validate_upload(filename: str, content_type: str | None, size: int, max_mb: int) -> tuple[str, str | None]:
    """Return (extension, error). Validates extension, MIME and size before any write."""
    import os

    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return ext, f"unsupported file extension '{ext}' (allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)})"
    if size > max_mb * 1024 * 1024:
        return ext, f"file too large ({size} bytes > {max_mb} MB)"
    if content_type and content_type not in ALLOWED_IMAGE_MIME:
        return ext, f"unsupported content type '{content_type}'"
    return ext, None


def check_magic(ext: str, head: bytes) -> bool:
    sigs = MAGIC.get(ext)
    if not sigs:
        return False
    return any(head.startswith(sig) for sig in sigs)