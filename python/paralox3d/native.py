"""Native core loader for Paralox3D."""

from __future__ import annotations

import ctypes
import os
import runpy
import subprocess
import sys
from pathlib import Path


def _library_names():
    if sys.platform == "win32":
        return ["paralox3d.dll"]
    if sys.platform == "darwin":
        return ["libparalox3d.dylib"]
    return ["libparalox3d.so"]


def _source_repo():
    package = Path(__file__).resolve().parent
    return package.parent.parent


def _build_native():
    repo = _source_repo()
    build_script = repo / "python" / "paralox3d" / "build.py"
    if not build_script.is_file():
        return []

    namespace = runpy.run_path(str(build_script))
    path = namespace["build_native"]()
    return [path] if path else []


def _load_library(path: Path):
    # On Windows, bundled MinGW runtime DLLs live beside the native core.
    # Add that directory explicitly so ctypes can resolve their dependencies.
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(path.parent))

    return ctypes.CDLL(str(path))


def load():
    candidates = []

    env = os.environ.get("PARALOX3D_NATIVE")
    if env:
        candidates.append(Path(env))

    package = Path(__file__).resolve().parent
    names = _library_names()

    for name in names:
        candidates.append(package / "_native" / name)

    repo = _source_repo()
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
            return _load_library(path)

    # Source checkouts can build the native core on first use.
    try:
        built = _build_native()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "Paralox3D could not build its native core automatically. "
            "Make sure a C++ compiler is installed."
        ) from exc

    for path in built:
        if path.is_file():
            return _load_library(path)

    searched = "\n".join(f"  - {path}" for path in candidates)
    raise RuntimeError(
        "Paralox3D native core could not be loaded or built.\n"
        f"Searched:\n{searched}"
    )
