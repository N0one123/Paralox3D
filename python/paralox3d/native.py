"""Low-level loader for the Paralox3D native core."""

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
    package = Path(__file__).resolve().parent
    names = _library_names()
    for name in names:
        candidates.append(package / "_native" / name)
    repo = package.parent.parent
    for name in names:
        candidates.extend([
            repo / "build" / "Release" / name,
            repo / "build" / "Debug" / name,
            repo / "build" / name,
            repo / "build" / "paralox3d-native" / "Release" / name,
            repo / "build" / "paralox3d-native" / "Debug" / name,
            repo / "build" / "paralox3d-native" / name,
        ])
    for path in candidates:
        if path.is_file():
            return ctypes.CDLL(str(path))
    searched = "\n".join(f"  - {path}" for path in candidates)
    raise RuntimeError(
        "Paralox3D native core could not be loaded. "
        "Install Paralox3D with 'python -m pip install -e .' to build it automatically.\n"
        f"Searched:\n{searched}"
    )
