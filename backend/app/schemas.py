"""Pydantic request/response schemas for HealthSignal."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------- auth
class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10, max_length=72)
    role: str = Field(default="patient", pattern="^(patient|clinician|researcher|admin)$")


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    clinician_verified: bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------- profiles
class ProfileIn(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    is_synthetic: bool = False


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    is_synthetic: bool
    created_at: datetime
    owner_id: int


class MeasurementIn(BaseModel):
    kind: str
    value: float
    unit: Optional[str] = None
    observed_at: Optional[datetime] = None
    source: str = "manual"


class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    value: float
    unit: str
    observed_at: datetime
    source: str


class QuestionnaireIn(BaseModel):
    answers: dict[str, str]


class NoteIn(BaseModel):
    note_type: str = "manual"
    text: str = Field(min_length=1, max_length=8000)


# ---------------------------------------------------------------- predictions
class PredictionIn(BaseModel):
    model_key: str
    values: dict[str, Any]
    save_to_profile: Optional[int] = None


class FeatureContribution(BaseModel):
    feature: str
    value: Any = None
    contribution: float
    direction: str


class ExplanationOut(BaseModel):
    method: str
    top_features: list[FeatureContribution]
    note: str


class PredictionOut(BaseModel):
    model_key: str
    model_name: str
    probability: float
    probability_interpretation: str
    provided_features: dict[str, Any]
    imputed_features: list[str]
    explanation: Optional[ExplanationOut]
    limitations: list[str]
    safe_harbour: str


# ---------------------------------------------------------------- imaging
class ImagingRunIn(BaseModel):
    model_key: str = "cxr_nih"
    sample_file: Optional[str] = None


class ImagingRunOut(BaseModel):
    study_id: int
    model_key: str
    model_name: str
    labels: list[str]
    probabilities: dict[str, float]
    highest_label: Optional[str]
    probability_interpretation: str
    gradcam: Optional[dict]
    inference_ms: int


# ---------------------------------------------------------------- reports / assistant
class ReportOut(BaseModel):
    profile_id: int
    generated_at: datetime
    patient_provided: dict[str, Any]
    model_outputs: list[dict[str, Any]]
    missing: list[str]
    limitations: list[str]
    safe_harbour: str


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AnswerOut(BaseModel):
    answer: str
    evidence: list[dict[str, Any]]
    uncertainty: str
    sources: list[str]