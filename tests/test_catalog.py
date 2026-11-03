"""Exercise the real catalog reader against release records and temporary trees."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog import catalog_path, load_targets, planning_storage_path


class CatalogTest(unittest.TestCase):
    def record(self):
        path = next((ROOT / "registry/catalog").rglob("*.json"))
        return json.loads(path.read_bytes())

    def write_record(self, directory, record):
        path = directory / catalog_path(record["packageId"], record["version"],
                                        record["channel"], record["target"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        return path

    def test_all_catalog_records_match_current_signed_targets(self):
        signed = json.loads((ROOT / "registry/metadata/targets.json").read_bytes())
        self.assertEqual(load_targets(ROOT / "registry/catalog"), signed["signed"]["targets"])

    def test_runtime_locks_select_exact_available_catalog_records(self):
        locks = sorted((ROOT / "registry/locks/runtime").glob("*.json"))
        self.assertTrue(locks)
        for path in locks:
            lock = json.loads(path.read_bytes())
            for pin in lock["components"].values():
                with self.subTest(lock=path.name, package=pin["packageId"]):
                    self.assertEqual(path.stem, pin["target"])
                    record = json.loads((ROOT / "registry/catalog" / catalog_path(
                        pin["packageId"], pin["version"], "stable", pin["target"])).read_bytes())
                    self.assertEqual(record["availability"]["state"], "available")
                    self.assertEqual(record["archive"]["sha256"], "sha256:" + pin["sha256"])
                    self.assertEqual(record["archive"]["length"], pin["size"])
                    self.assertEqual(record["package"]["sha256"], "sha256:" + pin["packageSha256"])
                    self.assertEqual(record["package"]["manifestSha256"], "sha256:" + pin["manifestSha256"])
                    self.assertIn("operations", record["categories"])
                    self.assertTrue((ROOT / "plugins" / "operations" / pin["packageId"] / "LICENSE").is_file())

    def test_identity_includes_namespace_version_channel_and_target(self):
        self.assertEqual(catalog_path("acme/shared", "1.2.3", "beta", "linux-x86_64"),
                         Path("acme/shared/1.2.3/beta/linux-x86_64.json"))
        first = catalog_path("acme/shared", "1.2.3", "stable", "darwin-arm64")
        self.assertNotEqual(first, catalog_path("other/shared", "1.2.3", "stable", "darwin-arm64"))
        for package in ["acme/../shared", "/shared", "acme/..", "acme/a\\b", "acme/a:b"]:
            with self.subTest(package=package), self.assertRaises(ValueError):
                catalog_path(package, "1.2.3", "stable", "darwin-arm64")

    def test_recursive_loading_does_not_depend_on_domain(self):
        record = self.record()
        record["categories"] = ["development"]
        with tempfile.TemporaryDirectory(prefix="插件 catalog with spaces ") as temporary:
            directory = Path(temporary)
            self.write_record(directory, record)
            result = load_targets(directory)
            self.assertEqual(result[record["archive"]["targetName"]]["custom"]["aster"], record)

    def test_flat_or_misplaced_records_are_refused(self):
        record = self.record()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "old-flat-record.json").write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "identity path"):
                load_targets(directory)

    def test_duplicate_signed_targets_are_refused(self):
        record = self.record()
        other = copy.deepcopy(record)
        other["channel"] = "beta" if record["channel"] != "beta" else "stable"
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_record(directory, record)
            self.write_record(directory, other)
            with self.assertRaisesRegex(ValueError, "duplicate catalog target"):
                load_targets(directory)

    def test_missing_or_empty_catalog_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            for directory in [Path(temporary), Path(temporary) / "missing"]:
                with self.subTest(directory=directory), self.assertRaisesRegex(ValueError, "no records"):
                    load_targets(directory)

    def test_planning_bytes_are_separately_signed_and_checked_before_publication(self):
        record = self.record()
        data = b'{"planning":"fixture"}\n'
        record["planning"] = {"targetName": "extensions/aster/fixture/0.1.0/stable/any/planning-v1.json",
                              "length": len(data), "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "catalog"
            self.write_record(catalog, record)
            target = catalog.parent / "targets" / planning_storage_path(record["planning"])
            target.parent.mkdir(parents=True)
            target.write_bytes(data)
            signed = load_targets(catalog)
            self.assertEqual(signed[record["planning"]["targetName"]], {
                "length": len(data), "hashes": {"sha256": hashlib.sha256(data).hexdigest()}})
            target.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_targets(catalog)
        for name in ("../planning-v1.json", "extensions/../planning-v1.json", "extensions/a\\b/planning-v1.json"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                planning_storage_path({**record["planning"], "targetName": name})


if __name__ == "__main__":
    unittest.main()
