"""Refuse damaged runtime bytes before a native package can be produced."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / "recipes/babeldoc-stream/darwin-arm64.py"
SPEC = importlib.util.spec_from_file_location("babeldoc_recipe", PATH)
RECIPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECIPE)


class BabeldocRecipeTest(unittest.TestCase):
    def test_wrong_length_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="BabelDOC 空格 ") as temporary:
            archive = Path(temporary) / "runtime.tar.gz"
            archive.write_bytes(b"wrong archive")
            with self.assertRaisesRegex(ValueError, "length mismatch"):
                RECIPE.verify_runtime(archive)

    def test_same_length_different_content_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="BabelDOC 空格 ") as temporary:
            archive = Path(temporary) / "runtime.tar.gz"
            with archive.open("wb") as stream:
                stream.truncate(RECIPE.RUNTIME_BYTES)
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                RECIPE.verify_runtime(archive)


if __name__ == "__main__":
    unittest.main()
