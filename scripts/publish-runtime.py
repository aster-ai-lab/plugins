#!/usr/bin/env python3
"""Publish already validated native AIX output without rewriting its OCI manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from catalog import catalog_path, planning_storage_path

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
        shutil.copyfile(ROOT / "domains.acl", source / "domains.acl")
        metadata = stem.with_suffix(stem.suffix + ".catalog-metadata.json")
        record = publication["catalog"]
        planning = record.get("planning")
        with tempfile.TemporaryDirectory() as validation:
            command = [str(aster), "registry", "package", "prepare", str(archive),
                       "--repository", str(source), "--domain", "operations", "--catalog-metadata", str(metadata),
                       "--output", str(Path(validation) / "manifest.json"), "--json"]
            if planning:
                command.extend(["--planning-output", str(Path(validation) / "planning.json")])
            result = subprocess.run(command, check=True, capture_output=True)
            prepared = json.loads(result.stdout)["data"]["aixPublication"]
            require(prepared["package"] == package and prepared["manifestSha256"] == publication["manifestSha256"]
                    and prepared["catalog"] == record, "native preparation changed")
            if planning:
                data = stem.with_suffix(stem.suffix + ".planning.json").read_bytes()
                require(data == (Path(validation) / "planning.json").read_bytes(), "native planning changed")
                destination = ROOT / "registry/targets" / planning_storage_path(planning)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    require(destination.read_bytes() == data, "published planning target changed")
                else:
                    destination.write_bytes(data)
        with zipfile.ZipFile(archive) as content:
            require(sha(content.read("aster-use-extension.acl")) == pin["manifestSha256"], "native manifest pin mismatch")
        repository = publication["ociRepository"]
        require(repository == "ghcr.io/aster-ai-lab/plugins/aster/" + name, "unexpected OCI repository")
        record_path = catalog / catalog_path(pin["packageId"], pin["version"], "stable", pin["target"])
        if record_path.exists():
            previous = json.loads(record_path.read_bytes())
            require(previous["archive"]["sha256"] == "sha256:" + pin["sha256"],
                    "a published version is immutable; reuse its original AIX and lock")
            continue
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
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    locks = ROOT / "registry/locks/runtime"
    locks.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate / "runtime-components.json", locks / (next(iter(lock["components"].values()))["target"] + ".json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--aster-use-bin", required=True, type=Path)
    parser.add_argument("--oras", required=True, type=Path)
    args = parser.parse_args()
    publish(args.candidate.resolve(), args.aster_use_bin.resolve(), args.oras.resolve())
