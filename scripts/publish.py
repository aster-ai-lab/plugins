#!/usr/bin/env python3
"""Publish already validated native AIX output without rewriting its OCI manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def publish(candidate, aster, oras):
    lock = json.loads((candidate / "runtime-components.json").read_bytes())
    catalog = ROOT / "registry/catalog"
    catalog.mkdir(parents=True, exist_ok=True)
    for name, pin in sorted(lock["components"].items()):
        archive = candidate / pin["archive"]
        stem = archive.with_suffix("")
        publication = json.loads(stem.with_suffix(stem.suffix + ".publication.json").read_bytes())["data"]["aixPublication"]
        manifest = stem.with_suffix(stem.suffix + ".oci.json").read_bytes()
        require(archive.stat().st_size == pin["size"] == publication["archiveLength"] <= 512 * 1024 * 1024, "archive length mismatch")
        require(sha(archive.read_bytes()) == pin["sha256"], "archive digest mismatch")
        require(publication["archiveSha256"] == "sha256:" + pin["sha256"], "publication digest mismatch")
        require("sha256:" + sha(manifest) == publication["manifestSha256"], "OCI manifest digest mismatch")
        package = publication["package"]
        require((package["packageId"], package["version"], package["packageSha256"]) == (pin["packageId"], pin["version"], pin["packageSha256"]), "package identity mismatch")
        source = candidate / "repository" / pin["target"]
        with tempfile.TemporaryDirectory() as validation:
            result = subprocess.run([str(aster), "registry", "package", "prepare", str(archive),
                                     "--repository", str(source), "--domain", "operations",
                                     "--output", str(Path(validation) / "manifest.json"), "--json"],
                                    check=True, capture_output=True)
            prepared = json.loads(result.stdout)["data"]["aixPublication"]
            require(prepared["package"] == package and prepared["manifestSha256"] == publication["manifestSha256"], "native preparation changed")
        repository = publication["ociRepository"]
        require(repository == "ghcr.io/aster-ai-lab/plugins/operations/aster/" + name, "unexpected OCI repository")
        record_path = catalog / (name + "-" + pin["version"] + "-" + pin["target"] + ".json")
        if record_path.exists():
            previous = json.loads(record_path.read_bytes())
            require(previous["archive"]["sha256"] == "sha256:" + pin["sha256"],
                    "a published version is immutable; reuse its original AIX and lock")
        with tempfile.TemporaryDirectory() as directory:
            layout = Path(directory)
            blobs = layout / "blobs/sha256"
            blobs.mkdir(parents=True)
            (layout / "oci-layout").write_text('{"imageLayoutVersion":"1.0.0"}', encoding="utf-8")
            (blobs / sha(manifest)).write_bytes(manifest)
            (blobs / sha(b"{}")).write_bytes(b"{}")
            shutil.copyfile(archive, blobs / pin["sha256"])
            descriptor = {"mediaType": "application/vnd.oci.image.manifest.v1+json", "digest": "sha256:" + sha(manifest),
                          "size": len(manifest), "annotations": {"org.opencontainers.image.ref.name": "candidate"}}
            (layout / "index.json").write_text(json.dumps({"schemaVersion": 2, "manifests": [descriptor]}), encoding="utf-8")
            subprocess.run([str(oras), "cp", "--from-oci-layout", str(layout) + ":candidate",
                            repository + ":" + pin["target"] + "-" + pin["sha256"]], check=True)
            subprocess.run([str(oras), "manifest", "fetch", repository + "@sha256:" + sha(manifest),
                            "--output", str(layout / "fetched.json")], check=True)
            require((layout / "fetched.json").read_bytes() == manifest, "published OCI manifest changed")
        permission = {"schema": "aster.use.plugin-permissions.v1", "surfaces": []}
        permission_digest = sha(json.dumps(permission, sort_keys=True, separators=(",", ":")).encode())
        target = (f'extensions/{pin["packageId"]}/{pin["version"]}/stable/{pin["target"]}/'
                  f'oci-ghcr-v1/operations/{sha(manifest)}/{name}.aix')
        record = {"schema": "aster.use.plugin-catalog.v3", "packageId": pin["packageId"],
                  "displayName": name, "description": "Pinned native runtime assets for Aster desktop.",
                  "publisher": "aster", "keywords": ["desktop", "runtime"], "categories": ["operations"],
                  "version": pin["version"], "channel": "stable", "requiresUse": ">=0.3.0, <0.4.0",
                  "target": pin["target"], "surfaces": [{"kind": "plugin", "id": "runtime", "optional": False}],
                  "permissionCeiling": permission, "permissionCeilingDigest": "sha256:" + permission_digest,
                  "archive": {"targetName": target, "length": pin["size"], "sha256": "sha256:" + pin["sha256"]},
                  "package": {"expandedBytes": package["byteCount"], "fileCount": package["fileCount"],
                              "sha256": "sha256:" + pin["packageSha256"], "manifestSha256": "sha256:" + pin["manifestSha256"]},
                  "license": "MIT", "repository": "https://github.com/aster-ai-lab/plugins", "availability": {"state": "available"}}
        (record_path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    locks = ROOT / "registry/runtime-locks"
    locks.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate / "runtime-components.json", locks / (next(iter(lock["components"].values()))["target"] + ".json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--aster-use-bin", required=True, type=Path)
    parser.add_argument("--oras", required=True, type=Path)
    args = parser.parse_args()
    publish(args.candidate.resolve(), args.aster_use_bin.resolve(), args.oras.resolve())
