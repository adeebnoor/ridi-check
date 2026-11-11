"""Small shared helpers. Standard library only."""

from __future__ import annotations

import hashlib
import importlib
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Callable


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_write_text(path: str, text: str) -> None:
    """Write a whole file or leave the previous one untouched."""
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp-", suffix=os.path.basename(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)  # mkstemp makes the file private; use the usual permissions
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_callable(spec: str, what: str) -> Callable:
    """Resolve ``module:function``. The current directory is importable."""
    module_name, sep, attr = spec.partition(":")
    if not sep or not module_name or not attr:
        raise ValueError(f"{what}: expected module:function, got {spec!r}")
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    try:
        obj = importlib.import_module(module_name)
    except Exception as exc:  # the user's module may fail in any way on import
        raise ValueError(f"{what}: cannot import {module_name!r}: {type(exc).__name__}: {exc}") from exc
    for part in attr.split("."):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            raise ValueError(f"{what}: {module_name!r} has no attribute {attr!r}") from None
    if not callable(obj):
        raise ValueError(f"{what}: {spec!r} is not callable")
    return obj
