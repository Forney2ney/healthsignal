from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="patient")  # patient|clinician|researcher|admin
    clinician_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    profiles: Mapped[list["PatientProfile"]] = relationship(back_populates="owner")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped[User] = relationship(back_populates="profiles")
    measurements: Mapped[list["Measurement"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    questionnaire: Mapped[list["QuestionnaireAnswer"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    studies: Mapped[list["ImagingStudy"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    outputs: Mapped[list["ModelOutput"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    record_notes: Mapped[list["RecordNote"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class Measurement(Base):
    """A single time-stamped measurement with a unit and provenance."""

    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32), default="manual")  # manual|imported|synthetic-demo
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    profile: Mapped[PatientProfile] = relationship(back_populates="measurements")


class QuestionnaireAnswer(Base):
    __tablename__ = "questionnaire_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    question_key: Mapped[str] = mapped_column(String(64), index=True)
    answer: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    profile: Mapped[PatientProfile] = relationship(back_populates="questionnaire")


class RecordNote(Base):
    __tablename__ = "record_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    note_type: Mapped[str] = mapped_column(String(64), default="manual")  # manual|extracted|history
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    profile: Mapped[PatientProfile] = relationship(back_populates="record_notes")


class ImagingStudy(Base):
    __tablename__ = "imaging_studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(64))
    modality: Mapped[str] = mapped_column(String(32), default="unknown")  # xray|ct|mri|ultrasound|unknown
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    profile: Mapped[PatientProfile | None] = relationship(back_populates="studies")
    outputs: Mapped[list["ImageAnalysis"]] = relationship(back_populates="study", cascade="all, delete-orphan")


class ImageAnalysis(Base):
    __tablename__ = "image_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("imaging_studies.id"), index=True)
    model_key: Mapped[str] = mapped_column(String(64))
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    study: Mapped[ImagingStudy] = relationship(back_populates="outputs")


class ModelOutput(Base):
    __tablename__ = "model_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    model_key: Mapped[str] = mapped_column(String(64), index=True)
    inputs_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    profile: Mapped[PatientProfile] = relationship(back_populates="outputs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(128), index=True)
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(32), default="clinician")  # clinician|patient
    summary_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class ShareGrant(Base):
    """A patient-controlled grant letting a specific clinician read a profile."""

    __tablename__ = "share_grants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    granted_to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)