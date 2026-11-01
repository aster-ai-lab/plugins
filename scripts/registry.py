#!/usr/bin/env python3
"""Sign the official Aster TUF catalog; root signing stays in macOS Keychain."""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "registry/metadata"
ROLES = ("root", "targets", "snapshot", "timestamp")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def keychain(operation, role, data=None):
    return subprocess.run(["swift", str(ROOT / "scripts/keychain.swift"), operation, role],
                          input=data, check=True, capture_output=True).stdout.strip()


def expires(days):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def signed(role, value, root, local):
    key_id = root["roles"][role]["keyids"][0]
    data = canonical(value)
    if local:
        signature = bytes.fromhex(keychain("sign", role, data).decode())
    else:
        seed = base64.b64decode(os.environ["TUF_" + role.upper() + "_KEY"], validate=True)
        if role == "root" or len(seed) != 32:
            raise ValueError("only 32-byte online Ed25519 seeds are admitted")
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory) / "key.der"
            private.touch(mode=0o600)
            private.write_bytes(bytes.fromhex("302e020100300506032b657004220420") + seed)
            message = Path(directory) / "message"
            message.write_bytes(data)
            signature = subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-keyform", "DER",
                                        "-inkey", str(private), "-in", str(message)],
                                       check=True, capture_output=True).stdout
    public = bytes.fromhex(root["keys"][key_id]["keyval"]["public"])
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        (directory / "public.der").write_bytes(bytes.fromhex("302a300506032b6570032100") + public)
        (directory / "message").write_bytes(data)
        (directory / "signature").write_bytes(signature)
        subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-keyform", "DER", "-rawin",
                        "-inkey", str(directory / "public.der"), "-in", str(directory / "message"),
                        "-sigfile", str(directory / "signature")], check=True, capture_output=True)
    return canonical({"signed": value, "signatures": [{"keyid": key_id, "sig": signature.hex()}]}) + b"\n"


def initialize():
    if (METADATA / "root.json").exists():
        raise ValueError("root already exists; use an explicit root rotation")
    keys, roles = {}, {}
    for role in ROLES:
        public = json.loads(keychain("ensure", role))["public"]
        key = {"keytype": "ed25519", "scheme": "ed25519", "keyval": {"public": public}}
        key_id = sha(canonical(key))
        keys[key_id] = key
        roles[role] = {"keyids": [key_id], "threshold": 1}
    root = {"_type": "root", "spec_version": "1.0.0", "consistent_snapshot": True,
            "version": 1, "expires": expires(365), "keys": keys, "roles": roles}
    document = signed("root", root, root, True)
    METADATA.mkdir(parents=True, exist_ok=True)
    (METADATA / "root.json").write_bytes(document)
    (METADATA / "1.root.json").write_bytes(document)
    (ROOT / "registry/root.sha256").write_text(sha(document) + "\n", encoding="utf-8")


def refresh(local):
    root = json.loads((METADATA / "root.json").read_bytes())["signed"]
    current = METADATA / "timestamp.json"
    version = json.loads(current.read_bytes())["signed"]["version"] + 1 if current.exists() else 1
    targets = {}
    for path in sorted((ROOT / "registry/catalog").glob("*.json")):
        record = json.loads(path.read_bytes())
        archive = record["archive"]
        name = archive["targetName"]
        if name in targets:
            raise ValueError("duplicate catalog target")
        targets[name] = {"length": archive["length"], "hashes": {"sha256": archive["sha256"].removeprefix("sha256:")},
                         "custom": {"aster": record}}
    documents = {}
    for role, days in (("targets", 90), ("snapshot", 7), ("timestamp", 2)):
        value = {"_type": role, "spec_version": "1.0.0", "version": version, "expires": expires(days)}
        if role == "targets":
            value["targets"] = targets
        else:
            previous = "targets" if role == "snapshot" else "snapshot"
            data = documents[previous]
            value["meta"] = {previous + ".json": {"version": version, "length": len(data),
                                                  "hashes": {"sha256": sha(data)}}}
        documents[role] = signed(role, value, root, local)
    for role, data in documents.items():
        (METADATA / (role + ".json")).write_bytes(data)
        if role != "timestamp":
            (METADATA / f"{version}.{role}.json").write_bytes(data)
    print(json.dumps({"version": version, "targets": len(targets),
                      "rootSha256": sha((METADATA / "root.json").read_bytes())}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init-root", "refresh"])
    parser.add_argument("--keychain", action="store_true")
    args = parser.parse_args()
    if args.command == "init-root":
        initialize()
    else:
        refresh(args.keychain)
