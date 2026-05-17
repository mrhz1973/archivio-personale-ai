"""
Unit tests for classify_inventory.py.
All tests use in-memory data only and never touch real user archive paths.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from classify_inventory import (
    build_category_counts,
    classify_file,
    classify_inventory,
)


class TestClassifyFile(unittest.TestCase):
    def test_extension_classification(self):
        item = {
            "relative_path": "scans/documento.pdf",
            "filename": "documento.pdf",
            "extension": ".pdf",
            "size_bytes": 123,
        }
        result = classify_file(item)
        self.assertEqual(result["category"], "Documents")
        self.assertGreaterEqual(result["confidence"], 0.70)
        self.assertTrue(result["dry_run_only"])

    def test_keyword_overrides_extension(self):
        item = {
            "relative_path": "Auto/assicurazione.pdf",
            "filename": "assicurazione.pdf",
            "extension": ".pdf",
            "size_bytes": 123,
        }
        result = classify_file(item)
        self.assertEqual(result["category"], "Auto")
        self.assertTrue(any(signal.startswith("keyword:") for signal in result["signals"]))
        self.assertTrue(result["dry_run_only"])

    def test_unknown_extension_goes_to_misc(self):
        item = {
            "relative_path": "unknown/file.xyzunknown",
            "filename": "file.xyzunknown",
            "extension": ".xyzunknown",
            "size_bytes": 10,
        }
        result = classify_file(item)
        self.assertEqual(result["category"], "Misc")
        self.assertLess(result["confidence"], 0.60)

    def test_no_source_action_fields(self):
        item = {
            "relative_path": "photo.jpg",
            "filename": "photo.jpg",
            "extension": ".jpg",
            "size_bytes": 10,
        }
        result = classify_file(item)
        forbidden_keys = {"move_to", "delete", "rename_to", "destination_path"}
        self.assertTrue(forbidden_keys.isdisjoint(result.keys()))


class TestClassifyInventory(unittest.TestCase):
    def test_builds_summary(self):
        inventory = {
            "summary": {"source": "C:/Archivio_Test"},
            "files": [
                {"relative_path": "a.pdf", "filename": "a.pdf", "extension": ".pdf", "size_bytes": 1},
                {"relative_path": "b.jpg", "filename": "b.jpg", "extension": ".jpg", "size_bytes": 2},
            ],
        }
        result = classify_inventory(inventory)
        self.assertEqual(result["summary"]["total_files"], 2)
        self.assertEqual(result["summary"]["source"], "C:/Archivio_Test")
        self.assertTrue(result["summary"]["dry_run_only"])
        self.assertEqual(len(result["classifications"]), 2)

    def test_invalid_files_field_raises(self):
        with self.assertRaises(ValueError):
            classify_inventory({"files": "not-a-list"})


class TestBuildCategoryCounts(unittest.TestCase):
    def test_counts_categories(self):
        counts = build_category_counts([
            {"category": "Documents"},
            {"category": "Documents"},
            {"category": "Images"},
        ])
        self.assertEqual(counts["Documents"], 2)
        self.assertEqual(counts["Images"], 1)


if __name__ == "__main__":
    unittest.main()
