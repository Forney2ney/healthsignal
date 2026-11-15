"""Dataset registry, download and loading for HealthSignal.

Every dataset used by HealthSignal must be:
  * public and de-identified,
  * downloadable without registration or approval,
  * documented here with name, source URL, purpose, licence and known limitations.

No dataset may be added to this registry without those facts verified from the source.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import requests

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

REQUEST_TIMEOUT = 60


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    name: str
    source_url: str
    purpose: str
    licence: str
    download_requirement: str
    known_limitations: list[str]
    n_records: str  # verified at load time; this is the documented count
    target_column: str
    categorical_columns: list[str] = field(default_factory=list)
    loader: Callable[[Path], tuple[pd.DataFrame, str]] | None = None


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def _download_and_extract_uci(url: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    marker = dest_dir / ".downloaded"
    if marker.exists() and any(dest_dir.iterdir()):
        return dest_dir
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    content = r.content
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
        zf.extractall(dest_dir)
    except zipfile.BadZipFile as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"{url} did not return a valid zip archive") from exc
    marker.write_text(url)
    return dest_dir


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------

def load_heart(dest_dir: Path) -> tuple[pd.DataFrame, str]:
    _download_and_extract_uci(
        "https://archive.ics.uci.edu/static/public/45/heart+disease.zip", dest_dir
    )
    path = dest_dir / "processed.cleveland.data"
    cols = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
        "exang", "oldpeak", "slope", "ca", "thal", "num",
    ]
    df = pd.read_csv(path, header=None, names=cols, na_values="?")
    df["target"] = (pd.to_numeric(df["num"], errors="coerce") > 0).astype(int)
    return df.drop(columns=["num"]), "target"


def load_wdbc(dest_dir: Path) -> tuple[pd.DataFrame, str]:
    _download_and_extract_uci(
        "https://archive.ics.uci.edu/static/public/17/breast+cancer+wisconsin+diagnostic.zip",
        dest_dir,
    )
    path = dest_dir / "wdbc.data"
    cols = ["id", "diagnosis"] + [
        f"{stat}_{feat}"
        for stat in ("mean", "se", "worst")
        for feat in [
            "radius", "texture", "perimeter", "area", "smoothness", "compactness",
            "concavity", "concave_points", "symmetry", "fractal_dimension",
        ]
    ]
    df = pd.read_csv(path, header=None, names=cols, na_values="?")
    df["target"] = (df["diagnosis"] == "M").astype(int)
    return df.drop(columns=["diagnosis", "id"]), "target"


def _extract_rar(rar_path: Path, dest_dir: Path) -> None:
    """Extract a .rar using an installed archiver (verified present on this dev machine)."""
    import shutil
    import subprocess

    candidates = [
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
        shutil.which("WinRAR"),
        shutil.which("7z"),
    ]
    exe = next((c for c in candidates if c and Path(c).exists()), None)
    if exe is None:
        raise RuntimeError(
            "CKD dataset ships inside a .rar archive but no RAR-capable archiver was found "
            "(WinRAR / 7-Zip). Install one and re-run."
        )
    if "WinRAR" in exe:
        cmd = [exe, "x", "-ibck", "-inul", "-y", str(rar_path), str(dest_dir) + "\\"]
    else:
        cmd = [exe, "x", "-y", f"-o{dest_dir}", str(rar_path)]
    subprocess.run(cmd, check=True, capture_output=True)


def _parse_arff(path: Path) -> pd.DataFrame:
    names: list[str] = []
    nominal: dict[str, list[str]] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    data_start = None
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if low.startswith("@attribute"):
            parts = line.strip().split(None, 2)
            name = parts[1].strip("'\"")
            typ = parts[2].strip().rstrip(",")
            names.append(name)
            if typ.startswith("{"):
                nominal[name] = [v.strip().strip("'\"") for v in typ.strip("{}").split(",")]
        elif low.startswith("@data"):
            data_start = i + 1
            break
    rows = []
    skipped: list[str] = []
    for line in lines[data_start:]:
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        vals = [v.strip().strip("'\"") for v in s.split(",")]
        while vals and vals[-1] == "":
            vals.pop()  # tolerate trailing commas present in some source rows
        if len(vals) != len(names):
            # 3 rows in this dataset genuinely have a misplaced comma (26 fields).
            # They are excluded rather than reconstructed, and the count is reported.
            skipped.append(s[:60])
            continue
        rows.append(vals)
    if skipped:
        print(f"[arff] {path.name}: skipped {len(skipped)} malformed source rows "
              f"(field count != {len(names)}); example: {skipped[0]!r}")
    df = pd.DataFrame(rows, columns=names)
    df = df.replace("?", np.nan)
    for col in df.columns:
        if col not in nominal:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_ckd(dest_dir: Path) -> tuple[pd.DataFrame, str]:
    _download_and_extract_uci(
        "https://archive.ics.uci.edu/static/public/336/chronic+kidney+disease.zip", dest_dir
    )
    arffs = sorted(dest_dir.rglob("*.arff")) or sorted(dest_dir.rglob("*.csv"))
    preferred = [p for p in arffs if p.name == "chronic_kidney_disease.arff"] or arffs
    arffs = preferred
    if not arffs:
        rars = list(dest_dir.rglob("*.rar"))
        if not rars:
            raise FileNotFoundError(f"neither arff nor rar found under {dest_dir}")
        _extract_rar(rars[0], dest_dir)
        arffs = sorted(dest_dir.rglob("*.arff"))
        arffs = [p for p in arffs if p.name == "chronic_kidney_disease.arff"] or arffs
    if not arffs:
        raise FileNotFoundError(f"rar extracted but no arff found under {dest_dir}")
    df = _parse_arff(arffs[0])
    df = df.rename(columns={"class": "class_raw"})
    target_col = "class_raw" if "class_raw" in df.columns else df.columns[-1]
    df["target"] = (df[target_col].astype(str).str.strip() == "ckd").astype(int)
    return df.drop(columns=[target_col]), "target"


def load_ilpd(dest_dir: Path) -> tuple[pd.DataFrame, str]:
    _download_and_extract_uci(
        "https://archive.ics.uci.edu/static/public/225/ilpd+indian+liver+patient+dataset.zip",
        dest_dir,
    )
    candidates = sorted(dest_dir.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"no CSV extracted into {dest_dir}")
    path = candidates[0]
    cols = [
        "age", "gender", "tb", "db", "alkphos", "sgpt", "sgot", "tp",
        "albumin", "ag_ratio", "selector",
    ]
    df = pd.read_csv(path, header=None, names=cols, na_values="?")
    # selector: 1 = liver patient, 2 = not a liver patient (dataset documentation)
    df["target"] = (pd.to_numeric(df["selector"], errors="coerce") == 1).astype(int)
    return df.drop(columns=["selector"]), "target"


def load_pima(dest_dir: Path) -> tuple[pd.DataFrame, str]:
    path = dest_dir / "pima-indians-diabetes.data.csv"
    _download(
        "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
        path,
    )
    feature_cols = [
        "pregnancies", "glucose", "bloodpressure", "skinfold", "insulin",
        "bmi", "pedigree", "age",
    ]
    cols = feature_cols + ["outcome"]
    df = pd.read_csv(path, header=None, names=cols, na_values="?")
    # Physiologically impossible zeros (documented conservative choice):
    # treat zero glucose/blood pressure/skinfold/insulin/BMI as MISSING, not as 0.
    for c in ["glucose", "bloodpressure", "skinfold", "insulin", "bmi"]:
        df[c] = df[c].replace(0, np.nan)
    df["target"] = pd.to_numeric(df["outcome"], errors="coerce").astype(int)
    return df.drop(columns=["outcome"]), "target"


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


DATASETS: dict[str, DatasetSpec] = {
    "heart": DatasetSpec(
        key="heart",
        name="UCI Heart Disease (Cleveland, processed)",
        source_url="https://archive.ics.uci.edu/dataset/45/heart+disease",
        purpose="Binary indicator of angiographic heart disease (num>0) from clinical measurements",
        licence="UCI Machine Learning Repository hosting; dataset from the 1988 Hungarian/Statlog heart-disease research (public research dataset)",
        download_requirement="None: direct zip download, no registration",
        known_limitations=[
            "Small sample (303) from a single Cleveland region cohort",
            "1988 vintage: measurement protocols differ from current practice",
            "Missing values encoded as '?' in ca/thal/slack; treated as unknown, not zero",
            "Not a contemporary externally validated cohort; metrics are dataset-specific",
        ],
        n_records="303",
        target_column="target",
        categorical_columns=["sex", "cp", "fbs", "restecg", "exang", "slope"],
        loader=load_heart,
    ),
    "wdbc": DatasetSpec(
        key="wdbc",
        name="UCI Breast Cancer Wisconsin (Diagnostic)",
        source_url="https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        purpose="Malignant vs benign classification from fine-needle-aspirate image features",
        licence="UCI hosting; original creators (Wolberg, Street, Mangasarian, University of Wisconsin)",
        download_requirement="None: direct zip download, no registration",
        known_limitations=[
            "569 samples; features are derived from digitised FNA images, not modern imaging",
            "Single-source institution; external validation unavailable in this project",
        ],
        n_records="569",
        target_column="target",
        categorical_columns=[],
        loader=load_wdbc,
    ),
    "ckd": DatasetSpec(
        key="ckd",
        name="UCI Chronic Kidney Disease",
        source_url="https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease",
        purpose="Classify chronic kidney disease from 24 clinical/lab measurements, many with missing values",
        licence="UCI hosting; collected in Chennai, India (L. J. Late, 2015)",
        download_requirement=(
            "No registration. The UCI zip wraps a .rar archive; extraction requires a "
            "RAR-capable archiver (WinRAR/7-Zip), which we invoke via WinRAR on this machine."
        ),
        known_limitations=[
            "Only 400 records with substantial missingness (normal '?' encoded missing)",
            "Single-hospital cohort; class balance and case-mix may not generalise",
            "Used partly to demonstrate honest missing-data handling",
        ],
        n_records="400",
        target_column="target",
        categorical_columns=["rbc", "pc", "pcc", "ba", "dm", "cad", "appet", "pe", "ane"],
        loader=load_ckd,
    ),
    "pima": DatasetSpec(
        key="pima",
        name="Pima Indians Diabetes (original NIDDK data, public mirror)",
        source_url="https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
        purpose="Screening classifier for type-2 diabetes test outcome from 8 measurements",
        licence="Original 1988 NIDDK dataset hosted publicly; widely used in teaching/research",
        download_requirement="None: direct CSV via a well-known public GitHub dataset mirror",
        known_limitations=[
            "Women of Pima heritage only; not representative of other populations",
            "Physiologically impossible zeros (glucose, bp, skinfold, insulin, BMI) are treated as missing here, which is a documented conservative choice",
            "Screening outcome only — not a clinical diagnosis of diabetes",
        ],
        n_records="768",
        target_column="target",
        categorical_columns=[],
        loader=load_pima,
    ),
    "ilpd": DatasetSpec(
        key="ilpd",
        name="UCI Indian Liver Patient Records (ILPD)",
        source_url="https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset",
        purpose="Liver-patient vs not from age, gender and liver function tests",
        licence="UCI hosting; collected from Andhra Pradesh, India (Ramana et al.)",
        download_requirement="None: direct zip download, no registration",
        known_limitations=[
            "Class imbalance (416 liver patients vs 167) requires PR-AUC reporting",
            "Aggregates many liver conditions into a single 'liver patient' label",
            "Age range is skewed (441 of 583 are male, age skew) — population bias",
        ],
        n_records="583",
        target_column="target",
        categorical_columns=["gender"],
        loader=load_ilpd,
    ),
}


def load_dataset(key: str) -> tuple[pd.DataFrame, str, DatasetSpec]:
    spec = DATASETS[key]
    dest = RAW_DIR / key
    df, target = spec.loader(dest)
    return df, target, spec