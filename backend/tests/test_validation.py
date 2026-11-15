import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.validation import (check_magic, validate_measurement, validate_upload)  # noqa: E402


def test_measurement_range_and_unit_enforced():
    r = validate_measurement("systolic_bp", 120)
    assert r.ok and r.unit == "mmHg"

    low = validate_measurement("systolic_bp", 10)
    assert not low.ok and "outside plausible range" in low.error

    wrong_unit = validate_measurement("systolic_bp", 120, "kpa")
    assert not wrong_unit.ok and "unit must be" in wrong_unit.error

    text = validate_measurement("systolic_bp", "abc")
    assert not text.ok and "numeric" in text.error


def test_unknown_measurement_rejected():
    r = validate_measurement("not_a_measurement", 1)
    assert not r.ok and "unknown" in r.error


def test_upload_extension_and_magic_checks():
    ext, err = validate_upload("evil.exe", None, 100, 10)
    assert not ext.endswith("png") and err

    ext, err = validate_upload("scan.png", "image/png", 11 * 1024 * 1024, 10)
    assert err and "too large" in err

    ext, err = validate_upload("scan.png", "image/png", 1000, 10)
    assert err is None and ext == ".png"

    assert check_magic(".png", b"\x89PNG\r\n\x1a\n")
    assert not check_magic(".png", b"MZ\x90\x00")
    assert check_magic(".dcm", b"DICM" + b"\x00" * 20)
    assert not check_magic(".dcm", b"PK\x03\x04")