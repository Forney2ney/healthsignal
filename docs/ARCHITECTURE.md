# HealthSignal — Architecture & Data Flow

## System overview

```mermaid
flowchart LR
    U[User browser<br/>React + TS + Tailwind] -->|REST + JWT| API[FastAPI backend]
    API --> AUTH[Auth/RBAC<br/>bcrypt + PyJWT + audit log]
    API --> ING[Ingestion & validation<br/>units/ranges/provenance]
    API --> INF[Inference service]
    API --> IMG[Image service]
    API --> REP[Report service]
    API --> AST[Retrieval assistant]
    INF --> REG[(ml/artifacts<br/>joblib + model cards)]
    IMG --> XRV[torchxrayvision<br/>DenseNet-121 weights]
    ING --> DB[(SQLite<br/>users/profiles/measurements/<br/>outputs/audit)]
    REP --> DB
    AST --> DB
```

## Prediction pipeline (tabular)

```mermaid
flowchart TD
    subgraph training (offline, deterministic seed 42)
        D[public dataset] --> P1[stratified 70/30 split]
        P1 --> T[train split]
        T --> CV[5-fold stratified CV<br/>LR / RF / HistGB / LightGBM<br/>scored by ROC-AUC, PR-AUC]
        CV --> SEL[best pipeline refit on train]
        SEL --> TE[held-out test split:<br/>ROC-AUC, PR-AUC, F1, sens, spec,<br/>Brier, confusion matrix]
        SEL --> ART[ml/artifacts/model.joblib<br/>+ model_card.json]
    end
    subgraph serving
        F[feature form from model card] --> C[coerce + range check<br/>missing stays missing]
        C --> X[DataFrame aligned to<br/>training column order]
        X --> ART
        X --> SH[SHAP / linear SHAP]
    end
```

## Image pipeline

```mermaid
flowchart LR
    UP[Upload or sample X-ray] --> V[extension + MIME + magic bytes + size]
    V --> ST[stored file, sha256, random name]
    ST --> PP[load + scale to -1024..1024<br/>grayscale]
    PP --> MD[DenseNet-121 nih weights]
    MD --> OUT[14 pathology scores<br/>uncalibrated, disclosed]
    MD --> CAM[Grad-CAM target norm5<br/>overlay + caption]
```

## Security boundaries

```mermaid
flowchart TD
    R[Roles: patient, clinician,<br/>researcher, admin] --> PERM{Endpoint checks}
    PERM -->|patient| OWN[own profiles, own outputs,<br/>grant control]
    PERM -->|clinician| SH[only granted profiles<br/>verified identity NOT implemented]
    PERM -->|researcher| AGG[aggregate dataset stats<br/>+ model cards only]
    PERM -->|admin| ADM[users + audit logs]
    UP2[Uploads] --> F1[allow-listed extension]
    F1 --> F2[MIME check]
    F2 --> F3[magic bytes vs extension]
    F3 --> F4[size <= 10 MB]
    F4 --> ST2[stored under backend/uploads]
```

## Multimodal decision (honest framing)

HealthSignal deliberately does **not** fuse incompatible model outputs into one "risk score". Modality
integration is at the dashboard/report level: each specialised model keeps its own provenance, dataset, metrics
and caveats; the unified dashboard aggregates *information*, not probabilities. Fusion of calibrated,
compatible outputs is listed as future work in the technical report.