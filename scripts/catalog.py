"""Catalog storage follows package identity, independently of source domains."""
import json
from pathlib import Path


def catalog_path(package_id, version, channel, target):
    if not isinstance(package_id, str) or len(package_id.split("/")) != 2:
        raise ValueError("catalog packageId must be publisher/name")
    parts = [*package_id.split("/"), version, channel, target]
    for part in parts:
        if (not isinstance(part, str) or not part or part in {".", ".."}
                or part.endswith((".", " "))
                or any(character in part for character in '/\\<>:"|?*\x00')):
            raise ValueError("catalog identity must use portable path segments")
    return Path(*parts[:-1], parts[-1] + ".json")


def load_targets(directory):
    targets = {}
    for path in sorted(directory.rglob("*.json")):
        record = json.loads(path.read_bytes())
        expected = catalog_path(record["packageId"], record["version"],
                                record["channel"], record["target"])
        if path.relative_to(directory) != expected:
            raise ValueError(f"catalog record is not at its identity path: {path}")
        archive = record["archive"]
        name = archive["targetName"]
        if name in targets:
            raise ValueError("duplicate catalog target")
        targets[name] = {"length": archive["length"],
                         "hashes": {"sha256": archive["sha256"].removeprefix("sha256:")},
                         "custom": {"aster": record}}
    if not targets:
        raise ValueError("catalog has no records; refusing to publish empty targets")
    return targets
