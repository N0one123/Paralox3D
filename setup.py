from pathlib import Path
import runpy

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / "python" / "paralox3d" / "build.py"


def build_native():
    namespace = runpy.run_path(str(BUILD_SCRIPT))
    namespace["build_native"]()


class build_py(_build_py):
    def run(self):
        build_native()
        super().run()


setup(cmdclass={"build_py": build_py})
