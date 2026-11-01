#!/usr/bin/env python3
"""Rebuild the initial macOS ARM64 runtime sources from approved desktop bytes."""
import argparse
import hashlib
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

SOURCE_VERSION = "0.1.11"
SOURCE_BYTES = 275433346
SOURCE_SHA256 = "952707ed923cbd5665b42f1df7bf2315de658ba1a10e5ad6bb5067455476e08e"
SOURCE_URL = "https://github.com/aster-ai-lab/aster/releases/download/desktop-stable/Aster-darwin-aarch64-v0.1.11.zip"


def build(archive, aster_root, aster_use, output):
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise ValueError("this recipe is qualified only on macOS ARM64")
    if archive.stat().st_size != SOURCE_BYTES:
        raise ValueError("upstream desktop archive length mismatch")
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != SOURCE_SHA256:
        raise ValueError("upstream desktop archive digest mismatch")
    producer = aster_root / "apps/studio/scripts/package_runtime_components.py"
    with tempfile.TemporaryDirectory(prefix="aster-runtime-source-") as directory:
        subprocess.run(["ditto", "-x", "-k", str(archive), directory], check=True)
        app = Path(directory) / "Aster.app"
        subprocess.run([sys.executable, str(producer), str(app), "--version", SOURCE_VERSION,
                        "--out", str(output), "--aster-use-bin", str(aster_use)], check=True, cwd=aster_root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help=SOURCE_URL)
    parser.add_argument("--aster-root", required=True, type=Path)
    parser.add_argument("--aster-use-bin", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    build(args.archive.resolve(), args.aster_root.resolve(), args.aster_use_bin.resolve(), args.out.resolve())
