from pathlib import Path
import runpy
import sys

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

ROOT = Path(__file__).resolve().parent
NATIVE_DIR = ROOT / "python" / "paralox3d" / "_native"
BUILD_SCRIPT = ROOT / "python" / "paralox3d" / "build.py"


def native_library():
    if sys.platform == "win32":
        name = "paralox3d.dll"
    elif sys.platform == "darwin":
        name = "libparalox3d.dylib"
    else:
        name = "libparalox3d.so"
    return NATIVE_DIR / name


def build_native():
    namespace = runpy.run_path(str(BUILD_SCRIPT))
    namespace["build_native"]()


class build_py(_build_py):
    def run(self):
        # The sdist already contains a prebuilt native library when one exists.
        # Only compile when the native library is actually missing.
        if not native_library().is_file():
            build_native()
        super().run()


class bdist_wheel(_bdist_wheel):
    def get_tag(self):
        python_tag, abi_tag, _ = super().get_tag()
        if sys.platform == "win32":
            platform_tag = "win_amd64"
        elif sys.platform == "darwin":
            platform_tag = "macosx_10_13_x86_64"
        else:
            platform_tag = "manylinux_2_17_x86_64"
        return python_tag, abi_tag, platform_tag


setup(cmdclass={"build_py": build_py, "bdist_wheel": bdist_wheel})
