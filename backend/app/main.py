from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import ml_bridge  # noqa: F401  (puts ml/src on sys.path)
from .config import get_settings
from .db import init_db
from .routers import admin, assistant, auth, data, imaging, models, reports

settings = get_settings()

app = FastAPI(
    title="HealthSignal API",
    version="0.1.0",
    description=(
        "Research/educational multimodal health-intelligence prototype. "
        "All predictive outputs are research indicators, not diagnoses."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, data.router, models.router, imaging.router,
          assistant.router, reports.router, admin.router, admin.router_research):
    app.include_router(r)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "healthsignal", "research_prototype": True}


@app.get("/health")
def health_alias():
    """Conventional liveness path for deployment probes.

    Same payload as /api/health. Hosted environments and container orchestrators
    commonly probe "/health", so serving it avoids false "service down" reports.
    """
    return health()


@app.get("/sample_cases.json")
def sample_cases():
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "sample_cases.json"
    if not path.exists():
        return Response(status_code=204)
    return FileResponse(path)


@app.get("/")
def index():
    from pathlib import Path

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"
    if dist.exists():
        return FileResponse(dist)
    return {"message": "HealthSignal API is running. Build the frontend (frontend/) for the UI."}