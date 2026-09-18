"""Low-level loader for the Paralox3D native core.

The public engine API intentionally keeps native loading in one place so the
rest of the Python package does not care whether the core is a .dll, .so, or
.dylib.
"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path


def _library_names():
    if sys.platform == "win32":
        return ["paralox3d.dll"]
    if sys.platform == "darwin":
        return ["libparalox3d.dylib"]
    return ["libparalox3d.so"]


def load():
    candidates = []

    env = os.environ.get("PARALOX3D_NATIVE")
    if env:
        candidates.append(Path(env))

    root = Path(__file__).resolve().parent
    for name in _library_names():
        candidates.extend([
            root / "_native" / name,
            root / name,
            root.parent.parent / "build" / name,
        ])

    for path in candidates:
        if path.exists():
            return ctypes.CDLL(str(path))

    raise RuntimeError(
        "Paralox3D native core was not found. Build the native project first "
        "and/or set PARALOX3D_NATIVE to the library path."
    )
