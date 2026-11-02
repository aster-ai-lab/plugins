#!/usr/bin/env python3
"""Rebuild the initial macOS ARM64 runtime sources from approved desktop bytes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import shutil
import sys
import tempfile

SOURCE_VERSION = "0.1.11"
SOURCE_BYTES = 275433346
SOURCE_SHA256 = "952707ed923cbd5665b42f1df7bf2315de658ba1a10e5ad6bb5067455476e08e"
SOURCE_URL = "https://github.com/aster-ai-lab/aster/releases/download/desktop-stable/Aster-darwin-aarch64-v0.1.11.zip"


def build(archive, aster_root, aster_use, output, ocr_binary):
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
        recipe = importlib.util.spec_from_file_location("ocr_plugin", aster_root / "crates/ocr/scripts/package_plugin.py")
        ocr = importlib.util.module_from_spec(recipe)
        recipe.loader.exec_module(ocr)
        document = app / "Contents/Resources/document"
        source = Path(directory) / "aster-ocr"
        ocr.stage_plugin(source, ocr_binary, app / "Contents/MacOS/libonnxruntime.dylib",
                         document / "ocr-models/PP-OCRv6_small", document / "licenses", "darwin-arm64")
        shutil.copytree(source / "payload", app / "Contents/Resources/ocr")
        shutil.rmtree(document / "ocr-models")
        (app / "Contents/MacOS/libonnxruntime.dylib").unlink()
        (document / "manifest.json").unlink()
        receipt = {"schema": "aster.document-assets.v2", "target": ["darwin", "arm64"], "files": {
            path.relative_to(document).as_posix(): ocr.digest(path) for path in sorted(document.rglob("*")) if path.is_file()}}
        (document / "manifest.json").write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
        subprocess.run([sys.executable, str(producer), str(app), "--version", SOURCE_VERSION,
                        "--out", str(output), "--aster-use-bin", str(aster_use)], check=True, cwd=aster_root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help=SOURCE_URL)
    parser.add_argument("--aster-root", required=True, type=Path)
    parser.add_argument("--aster-use-bin", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ocr-binary", required=True, type=Path, help="Newly built native aster-use-ocr executable")
    args = parser.parse_args()
    build(args.archive.resolve(), args.aster_root.resolve(), args.aster_use_bin.resolve(), args.out.resolve(), args.ocr_binary.resolve())
