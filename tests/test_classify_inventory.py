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
    build_location_policy_counts,
    classify_file,
    classify_inventory,
    is_context_bound,
)


class TestContextBound(unittest.TestCase):
    def test_root_file_is_not_context_bound(self):
        self.assertFalse(is_context_bound("photo.jpg"))

    def test_subfolder_file_is_context_bound(self):
        self.assertTrue(is_context_bound("Project Alpha/documento.pdf"))

    def test_windows_separator_is_context_bound(self):
        self.assertTrue(is_context_bound("Project Alpha\\documento.pdf"))


class TestClassifyFile(unittest.TestCase):
    def test_extension_classification(self):
        item = {
            "relative_path": "documento.pdf",
            "filename": "documento.pdf",
            "extension": ".pdf",
            "size_bytes": 123,
        }
        result = classify_file(item)
        self.assertEqual(result["category"], "Documents")
        self.assertGreaterEqual(result["confidence"], 0.70)
        self.assertEqual(result["location_policy"], "classify_only")
        self.assertEqual(result["suggested_folder"], "Documents")
        self.assertFalse(result["context_bound"])
        self.assertTrue(result["dry_run_only"])

    def test_keyword_overrides_extension(self):
        item = {
            "relative_path": "assicurazione.pdf",
            "filename": "assicurazione.pdf",
            "extension": ".pdf",
            "size_bytes": 123,
        }
        result = classify_file(item)
        self.assertEqual(result["category"], "Auto")
        self.assertTrue(any(signal.startswith("keyword:") for signal in result["signals"]))
        self.assertTrue(result["dry_run_only"])

    def test_context_folder_keeps_file_in_place(self):
        item = {
            "relative_path": "Project Alpha/documento.pdf",
            "filename": "documento.pdf",
            "extension": ".pdf",
            "size_bytes": 123,
        }
        result = classify_file(item)
        self.assertEqual(result["category"], "Documents")
        self.assertEqual(result["location_policy"], "keep_in_place")
        self.assertIsNone(result["suggested_folder"])
        self.assertTrue(result["context_bound"])
        self.assertIn("context:inside_existing_folder", result["signals"])

    def test_unknown_extension_goes_to_misc(self):
        item = {
            "relative_path": "file.xyzunknown",
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
                {"relative_path": "Project/b.jpg", "filename": "b.jpg", "extension": ".jpg", "size_bytes": 2},
            ],
        }
        result = classify_inventory(inventory)
        self.assertEqual(result["summary"]["total_files"], 2)
        self.assertEqual(result["summary"]["source"], "C:/Archivio_Test")
        self.assertTrue(result["summary"]["dry_run_only"])
        self.assertEqual(result["summary"]["location_policy_counts"]["classify_only"], 1)
        self.assertEqual(result["summary"]["location_policy_counts"]["keep_in_place"], 1)
        self.assertEqual(len(result["classifications"]), 2)

    def test_invalid_files_field_raises(self):
        with self.assertRaises(ValueError):
            classify_inventory({"files": "not-a-list"})


class TestBuildCounts(unittest.TestCase):
    def test_counts_categories(self):
        counts = build_category_counts([
            {"category": "Documents"},
            {"category": "Documents"},
            {"category": "Images"},
        ])
        self.assertEqual(counts["Documents"], 2)
        self.assertEqual(counts["Images"], 1)

    def test_counts_location_policy(self):
        counts = build_location_policy_counts([
            {"location_policy": "keep_in_place"},
            {"location_policy": "keep_in_place"},
            {"location_policy": "classify_only"},
        ])
        self.assertEqual(counts["keep_in_place"], 2)
        self.assertEqual(counts["classify_only"], 1)


if __name__ == "__main__":
    unittest.main()
