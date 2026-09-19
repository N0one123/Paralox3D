"""Native core loader for Paralox3D."""

from __future__ import annotations

import ctypes
import os
import shutil
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
    cmake_file = repo / "CMakeLists.txt"
    if not cmake_file.is_file():
        return []

    build_dir = repo / "build" / "paralox3d-native"
    build_dir.mkdir(parents=True, exist_ok=True)

    subprocess.check_call(["cmake", "-S", str(repo), "-B", str(build_dir)])
    args = ["cmake", "--build", str(build_dir)]
    if sys.platform == "win32":
        args += ["--config", "Release"]
    subprocess.check_call(args)

    names = _library_names()
    possible = []
    for name in names:
        possible.extend([
            build_dir / "Release" / name,
            build_dir / "Debug" / name,
            build_dir / name,
            repo / "build" / "Release" / name,
            repo / "build" / "Debug" / name,
            repo / "build" / name,
        ])

    found = [path for path in possible if path.is_file()]
    if found:
        package_native = repo / "python" / "paralox3d" / "_native"
        package_native.mkdir(parents=True, exist_ok=True)
        destination = package_native / found[0].name
        shutil.copy2(found[0], destination)
        return [destination, *found]

    return []


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
            return ctypes.CDLL(str(path))

    # Source checkouts can transparently build the native core on first use.
    try:
        built = _build_native()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "Paralox3D could not build its native core automatically. "
            "Make sure CMake and a C++ compiler are installed."
        ) from exc

    for path in built:
        if path.is_file():
            return ctypes.CDLL(str(path))

    searched = "\n".join(f"  - {path}" for path in candidates)
    raise RuntimeError(
        "Paralox3D native core could not be loaded or built.\n"
        f"Searched:\n{searched}"
    )
