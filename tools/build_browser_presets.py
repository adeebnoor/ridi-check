#!/usr/bin/env python3
"""Rebuild the public browser presets from the original GitHub-signed workflow ZIPs.

Usage:
 python tools/build_browser_presets.py --config-zip PATH --swap-zip PATH

Only accept byte-identical, recorded GitHub CI results. No synthetic substitutions,
post-hoc outcome manipulation, or changing published answer labels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import shutil
import zipfile
from pathlib import Path

SOURCES = {
    "qwen_config_48.csv": {
        "archive_member": "ridi-out/results.csv",
        "source_sha256": "18286273cf15a062629eaa59a3dbe976ea658a72d82d2b1dad5248e9b2e8317d",
        "source_run": "https://github.com/adeebnoor/ridi-check/actions/runs/43317397792",
    },
    "qwen_swap_48.csv": {
        "archive_member": "boolq/ridi-out/results.csv",
        "source_sha256": "8d9d0b48b48a0802df239fb47bbfa2dc9a72cb3eece853514aefec9ad982c629",
        "source_run": "https://github.com/adeebnoor/ridi-check/actions/runs/43312668253",
    },
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(archive: Path, output: Path, spec: dict):
    with zipfile.ZipFile(archive) as z:
        raw = z.read(spec["archive_member"])
    assert sha(raw) == spec["source_sha256"], "Signed CI result checksum mismatch"
    data = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    assert len(data) == 48
    assert len({row["case_id"] for row in data}) == 48
    assert all(row["expected"] in ("YES","NO") for row in data)
    assert all(row["question"].startswith("POLICY [") and "\nQUESTION:" in row["question"] for row in data)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    print(output, len(raw), sha(raw), spec["source_run"])

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config-zip", type=Path, required=True)
    p.add_argument("--swap-zip", type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / "web" / "presets"
    build(args.config_zip, out / "qwen_config_48.csv", SOURCES["qwen_config_48.csv"])
    build(args.swap_zip, out / "qwen_swap_48.csv", SOURCES["qwen_swap_48.csv"])
