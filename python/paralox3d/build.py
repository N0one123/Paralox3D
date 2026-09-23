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
    cxx = _portable_compiler("g++.exe", "clang++.exe")
    if cxx:
        return cxx

    cxx = _which("cl")
    if cxx:
        return cxx

    return _which("g++", "clang++")


def _progress(percent: int, label: str) -> None:
    width = 32
    filled = round(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    print(f"\r[{bar}] {percent:3d}%  {label:<34}", end="", flush=True)


def _finish_progress() -> None:
    print()


def _copy_mingw_runtime() -> None:
    """Copy MinGW runtime DLLs needed by the native core beside it."""
    _progress(90, "Bundling MinGW runtime libraries")
    for name in (
        "libstdc++-6.dll",
        "libgcc_s_seh-1.dll",
        "libwinpthread-1.dll",
    ):
        source = TOOLS / name
        if source.is_file():
            shutil.copy2(source, OUT / name)


def _run_compile(cmd: list[str], label: str) -> None:
    _progress(25, label)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        _finish_progress()
        raise
    _progress(75, "Native C++ compilation complete")


def _build_windows() -> Path:
    cxx = _find_windows_cxx()
    if not cxx:
        raise RuntimeError(
            "No C++ compiler was found. Put a portable MinGW-w64 compiler in "
            "tools\\\\mingw64\\\\bin, install Visual Studio Build Tools (MSVC), "
            "or make g++/clang++ available on PATH."
        )

    out = OUT / "paralox3d.dll"
    _progress(5, f"Found compiler: {Path(cxx).name}")

    if Path(cxx).name.lower() == "cl.exe":
        cmd = [
            cxx, "/nologo", "/std:c++17", "/O2", "/EHsc", "/LD",
            f"/I{INCLUDE}", "/DP3D_BUILD", *map(str, SRC),
            "/link", f"/OUT:{out}", "opengl32.lib", "user32.lib", "gdi32.lib",
        ]
        _run_compile(cmd, "Compiling native C++ core")
    else:
        cmd = [
            cxx, "-std=c++17", "-O2", "-shared", "-DP3D_BUILD",
            f"-I{INCLUDE}", *map(str, SRC), "-o", str(out),
            "-lopengl32", "-luser32", "-lgdi32",
        ]
        _run_compile(cmd, "Compiling native C++ core")

    _copy_mingw_runtime()
    _progress(100, "Build complete")
    _finish_progress()
    return out


def _build_unix() -> Path:
    cxx = _which("clang++", "g++")
    if not cxx:
        raise RuntimeError("No C++ compiler found. Install clang++ or g++.")

    suffix = ".dylib" if sys.platform == "darwin" else ".so"
    out = OUT / f"libparalox3d{suffix}"
    _progress(5, f"Found compiler: {Path(cxx).name}")
    _run_compile([
        cxx, "-std=c++17", "-O2", "-fPIC", "-shared", "-DP3D_BUILD",
        f"-I{INCLUDE}", *map(str, SRC), "-o", str(out),
    ], "Compiling native C++ core")
    _progress(100, "Build complete")
    _finish_progress()
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
