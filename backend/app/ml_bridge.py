"""Bridge from the FastAPI backend to the ml package."""
from __future__ import annotations

import sys
from pathlib import Path

ML_SRC = Path(__file__).resolve().parents[2] / "ml" / "src"
if str(ML_SRC) not in sys.path:
    sys.path.insert(0, str(ML_SRC))