"""Fetch sample chest X-ray images shipped in the torchxrayvision repository.

Provenance: the two PNG files are NIH ChestX-ray14 images (public domain) that the
torchxrayvision authors redistribute with their test suite (Apache-2.0 code repo).
They are used ONLY to demonstrate the imaging pipeline on real, verifiable inputs.
No patient identifiers are present. Images whose provenance is not established
(e.g. the covid sample in the same repo) are deliberately NOT downloaded.
"""
import sys
import urllib.request
from pathlib import Path

import _bootstrap  # noqa: F401

OUT = Path(__file__).resolve().parents[2] / "backend" / "assets" / "samples"
FILES = [
    ("00000001_000.png", "https://raw.githubusercontent.com/mlmed/torchxrayvision/master/tests/00000001_000.png"),
    ("00027426_000.png", "https://raw.githubusercontent.com/mlmed/torchxrayvision/master/tests/00027426_000.png"),
]

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in FILES:
        dest = OUT / name
        if not dest.exists():
            urllib.request.urlretrieve(url, dest)
        print("sample ->", dest, dest.stat().st_size, "bytes")