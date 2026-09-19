from pathlib import Path
import shutil
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent


def build_native():
    build_dir = ROOT / "build" / "paralox3d-native"
    build_dir.mkdir(parents=True, exist_ok=True)

    subprocess.check_call(["cmake", "-S", str(ROOT), "-B", str(build_dir)])

    args = ["cmake", "--build", str(build_dir)]
    if sys.platform == "win32":
        args += ["--config", "Release"]
    subprocess.check_call(args)

    if sys.platform == "win32":
        source = build_dir / "Release" / "paralox3d.dll"
        if not source.exists():
            source = build_dir / "paralox3d.dll"
    elif sys.platform == "darwin":
        source = build_dir / "libparalox3d.dylib"
    else:
        source = build_dir / "libparalox3d.so"

    if not source.exists():
        raise RuntimeError(f"Native build completed, but the library was not found: {source}")

    destination = ROOT / "python" / "paralox3d" / "_native"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination / source.name)


class build_py(_build_py):
    def run(self):
        build_native()
        super().run()


setup(cmdclass={"build_py": build_py})
