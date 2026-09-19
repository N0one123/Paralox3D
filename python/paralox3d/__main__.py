"""Paralox3D developer command line interface."""

from __future__ import annotations

import argparse

from .build import build_native


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m paralox3d")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build the native engine")
    build.add_argument(
        "--platform",
        choices=("windows", "linux", "macos", "android", "ios"),
        default=None,
    )

    args = parser.parse_args()
    mapping = {"windows": "win32", "linux": "linux", "macos": "darwin", "android": "android", "ios": "ios"}
    path = build_native(mapping.get(args.platform, args.platform))
    print(f"Built native core: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())