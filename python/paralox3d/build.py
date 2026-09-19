"""CMake-free native build tools for Paralox3D."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native"
SRC = [NATIVE / "src" / "paralox3d.cpp", NATIVE / "src" / "renderer.cpp"]
INCLUDE = NATIVE / "include"
OUT = ROOT / "python" / "paralox3d" / "_native"
TOOLS = ROOT / "tools" / "mingw64" / "bin"


def _which(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _portable_compiler(*names: str) -> str | None:
    for name in names:
        path = TOOLS / name
        if path.is_file():
            return str(path)
    return None


def _find_windows_cxx() -> str | None:
    # Prefer a compiler bundled with the source checkout so no system
    # installation or PATH modification is required.
    cxx = _portable_compiler("g++.exe", "clang++.exe")
    if cxx:
        return cxx

    cxx = _which("cl")
    if cxx:
        return cxx

    return _which("g++", "clang++")


def _build_windows() -> Path:
    cxx = _which("cl")
    if cxx:
        out = OUT / "paralox3d.dll"
        cmd = [
            cxx, "/nologo", "/std:c++17", "/O2", "/EHsc", "/LD",
            f"/I{INCLUDE}", "/DP3D_BUILD", *map(str, SRC),
            "/link", f"/OUT:{out}", "opengl32.lib", "user32.lib", "gdi32.lib",
        ]
        subprocess.check_call(cmd)
        return out

    cxx = _find_windows_cxx()
    if not cxx:
        raise RuntimeError(
            "No C++ compiler was found. Put a portable MinGW-w64 compiler in "
            "tools\\mingw64\\bin, install Visual Studio Build Tools (MSVC), "
            "or make g++/clang++ available on PATH."
        )

    out = OUT / "paralox3d.dll"
    subprocess.check_call([
        cxx, "-std=c++17", "-O2", "-shared", "-DP3D_BUILD",
        f"-I{INCLUDE}", *map(str, SRC), "-o", str(out),
        "-lopengl32", "-luser32", "-lgdi32",
    ])
    return out


def _build_unix() -> Path:
    cxx = _which("clang++", "g++")
    if not cxx:
        raise RuntimeError("No C++ compiler found. Install clang++ or g++.")

    suffix = ".dylib" if sys.platform == "darwin" else ".so"
    out = OUT / f"libparalox3d{suffix}"
    subprocess.check_call([
        cxx, "-std=c++17", "-O2", "-fPIC", "-shared", "-DP3D_BUILD",
        f"-I{INCLUDE}", *map(str, SRC), "-o", str(out),
    ])
    return out


def build_native(platform: str | None = None) -> Path:
    platform = platform or sys.platform
    OUT.mkdir(parents=True, exist_ok=True)

    if platform == "win32":
        return _build_windows()
    if platform in {"linux", "darwin"}:
        return _build_unix()
    raise RuntimeError(
        f"Native target {platform!r} is not implemented yet. "
        "Android and iOS will use their platform toolchains through this "
        "same build interface."
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m paralox3d.build")
    parser.add_argument(
        "--platform",
        choices=("windows", "linux", "macos", "android", "ios"),
        default=None,
    )
    args = parser.parse_args(argv)

    mapping = {
        "windows": "win32",
        "linux": "linux",
        "macos": "darwin",
        "android": "android",
        "ios": "ios",
    }
    path = build_native(mapping.get(args.platform, args.platform))
    print(f"Built native core: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
