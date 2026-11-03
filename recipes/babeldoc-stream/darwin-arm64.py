#!/usr/bin/env python3
"""Package the qualified BabelDOC runtime without committing native payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_BYTES = 293903386
RUNTIME_SHA256 = "bfc1cef574cd1ddba11ce34d952a311e08b562c212d2d60e22794114319d6818"
ARCHIVE_NAME = "babeldoc-stream-darwin-arm64.tar.gz"


def verify_runtime(archive):
    if archive.stat().st_size != RUNTIME_BYTES:
        raise ValueError("qualified BabelDOC runtime length mismatch")
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != RUNTIME_SHA256:
        raise ValueError("qualified BabelDOC runtime digest mismatch")


def build(archive, aster_use, output):
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise ValueError("this recipe is qualified only on macOS ARM64")
    if output.exists():
        raise ValueError("output already exists")
    verify_runtime(archive)
    repository = output / "repository"
    source = repository / "plugins/knowledge/aster/babeldoc-stream"
    shutil.copytree(ROOT / "plugins/knowledge/aster/babeldoc-stream", source)
    shutil.copyfile(ROOT / "domains.acl", repository / "domains.acl")
    (source / "payload").mkdir()
    shutil.copyfile(archive, source / "payload" / ARCHIVE_NAME)
    (source / "toolchain.acl").write_text(f'''toolchain {{
 schema_version = 1
 name = "babeldoc-stream"
 spec = "pipx:babeldoc-stream"
 version = "0.6.4.post4"
 executable = "babeldoc-stream"
 platform = "aarch64-macos-"
 archive = "payload/{ARCHIVE_NAME}"
 length = {RUNTIME_BYTES}
 sha256 = "{RUNTIME_SHA256}"
 format = "tar.gz"
 prefix = "babeldoc-stream"
 bin_dirs = ["bin"]
 executable_mode = "0755"
 command "babeldoc-stream" {{ path = "bin/babeldoc-stream" }}
}}
''', encoding="utf-8")
    aix = output / "babeldoc-stream-0.1.0-darwin-arm64.aix"
    commands = [
        [str(aster_use), "registry", "package", "build", str(source), "--output", str(aix), "--json"],
        [str(aster_use), "registry", "package", "check", str(aix), "--json"],
        [str(aster_use), "registry", "package", "prepare", str(aix), "--repository", str(repository),
         "--domain", "knowledge", "--catalog-metadata", str(Path(__file__).with_suffix(".json")),
         "--output", str(aix.with_suffix(".oci.json")), "--json"],
    ]
    checks = []
    for argv in commands:
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
        checks.append({"argv": argv, "exitCode": result.returncode,
                       "stdout": result.stdout, "stderr": result.stderr})
        (output / "checks.json").write_text(json.dumps({
            "packageId": "aster/babeldoc-stream", "target": "darwin-arm64",
            "runtimeLength": RUNTIME_BYTES, "runtimeSha256": RUNTIME_SHA256,
            "checks": checks, "published": False,
        }, indent=2) + "\n", encoding="utf-8")
        result.check_returncode()
    return aix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Independently qualified runtime archive")
    parser.add_argument("--aster-use-bin", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(build(args.archive.resolve(), args.aster_use_bin.resolve(), args.out.resolve()))
