from pathlib import Path
import shutil
import subprocess
import sys

from setuptools import Command, setup

ROOT = Path(__file__).resolve().parent

class BuildNative(Command):
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
        build_dir = ROOT / "build" / "paralox3d-native"
        build_dir.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(["cmake", "-S", str(ROOT), "-B", str(build_dir)])
        args = ["cmake", "--build", str(build_dir)]
        if sys.platform == "win32":
            args += ["--config", "Release"]
        subprocess.check_call(args)
        if sys.platform == "win32":
            source = build_dir / "Release" / "paralox3d.dll"
            if not source.exists(): source = build_dir / "paralox3d.dll"
        elif sys.platform == "darwin":
            source = build_dir / "libparalox3d.dylib"
        else:
            source = build_dir / "libparalox3d.so"
        if not source.exists():
            raise RuntimeError(f"Native build completed, but library was not found: {source}")
        destination = ROOT / "python" / "paralox3d" / "_native"
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination / source.name)

class build(Command):
    description = "Build Python package and native Paralox3D core"
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
        self.run_command("build_py")
        self.run_command("build_native")

setup(cmdclass={"build_native": BuildNative, "build": build})
