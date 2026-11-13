"""Regression tests for the original, byte-identical signed Qwen browser presets."""
import csv
import hashlib
import json
from pathlib import Path

from ridi_check.cli import main

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "web" / "presets"
SOURCES = {
    "qwen_config_48.csv": (
        "18286273cf15a062629eaa59a3dbe976ea658a72d82d2b1dad5248e9b2e8317d",
        {"stable_regression": 4, "stable_improvement": 2, "unstable": 3},
        3,
    ),
    "qwen_swap_48.csv": (
        "8d9d0b48b48a0802df239fb47bbfa2dc9a72cb3eece853514aefec9ad982c629",
        {"stable_regression": 6, "stable_improvement": 16, "unstable": 0},
        2,
    ),
}


def test_source_hashes_are_original_signed_ci_bytes():
    for name, (expected_sha, _, runs) in SOURCES.items():
        file = PRESETS / name
        raw = file.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected_sha, name
        cases = list(csv.DictReader(raw.decode("utf-8-sig").splitlines(keepends=True)))
        assert len(cases) == 48
        assert len({c["case_id"] for c in cases}) == 48
        assert sum(c["expected"] == "YES" for c in cases) == 24
        assert all(c["expected"] in {"YES", "NO"} for c in cases)
        assert all(c["question"].startswith("POLICY [") for c in cases)
        if runs == 3:
            assert "baseline_repeat2_answer" in cases[0]
        else:
            assert "baseline_repeat2_answer" not in cases[0]


def test_both_original_csvs_are_parseable_by_release_analyzer(tmp_path):
    for filename, (_, expected_states, _) in SOURCES.items():
        output = tmp_path / filename.removesuffix(".csv")
        assert main(["report", str(PRESETS / filename), "--out", str(output)]) == 0
        summary = json.loads((output / "summary.json").read_text(encoding="utf8"))
        assert summary["cases"] == 48
        for state, value in expected_states.items():
            assert summary["states"][state] == value, (filename, state)


def test_home_links_to_real_preset_ids_and_existing_synthetic_control():
    html = (ROOT / "index.html").read_text(encoding="utf8")
    app = (ROOT / "web" / "app.js").read_text(encoding="utf8")
    for name in ("qwen_config", "qwen_swap", "library"):
        assert f"web/ridi-update-check.html?preset={name}" in html
    for name in ("qwen_config_48.csv", "qwen_swap_48.csv"):
        assert name in app
    assert "crypto.subtle.digest" in app
    assert "credentials: \"omit\"" in app
    assert "clinical_ddi" in app and "Clinical preset unavailable" in app
    assert "ridi-check compare --current" not in html


def test_preset_license_and_limitations_are_visible():
    license_text = (PRESETS / "README.md").read_text(encoding="utf8")
    assert "CC BY-SA 3.0" in license_text
    assert "original" in license_text.lower()
    assert "no verified real clinical ddi" in license_text.lower()
    assert "43317397792" in license_text
    assert "43312668253" in license_text
