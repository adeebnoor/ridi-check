import csv
import io
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "synthetic_fixture.csv")

# `module:function` definitions in the tests resolve against the repository root and tests/.
for path in (ROOT, os.path.join(ROOT, "tests")):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def fixture_text():
    with open(FIXTURE, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def nokey_text(fixture_text):
    """The fixture with `expected` and every `_correct` column dropped."""
    rows = list(csv.reader(io.StringIO(fixture_text)))
    keep = [i for i, name in enumerate(rows[0]) if name != "expected" and not name.endswith("_correct")]
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows([[row[i] for i in keep] for row in rows])
    return out.getvalue()


@pytest.fixture
def write(tmp_path):
    def _write(name, text):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return str(path)
    return _write
