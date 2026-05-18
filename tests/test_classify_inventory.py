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
    build_confidence_buckets,
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


# ── ARCH-0473..0476: metadata field ──────────────────────────────────────────

class TestClassifyInventoryMetadata(unittest.TestCase):
    """ARCH-0473..0476: metadata field presence and correctness."""

    def setUp(self):
        self.inventory = {
            "metadata": {"tool": "inventory_readonly.py", "schema_version": "1.0"},
            "summary": {"source": "/tmp/test"},
            "files": [
                {"relative_path": "a.pdf", "filename": "a.pdf", "extension": ".pdf", "size_bytes": 1},
            ],
        }
        self.result = classify_inventory(self.inventory)

    def test_metadata_field_present(self):
        """ARCH-0473: top-level metadata field exists."""
        self.assertIn("metadata", self.result)

    def test_metadata_subfields_all_present(self):
        """ARCH-0474: all expected subfields present."""
        m = self.result["metadata"]
        for key in ("schema_version", "generated_at_iso", "tool", "mode",
                    "input_tool", "input_schema_version"):
            self.assertIn(key, m, f"metadata.{key} missing")

    def test_metadata_mode_dry_run_classification(self):
        """ARCH-0475: metadata.mode == dry_run_classification."""
        self.assertEqual(self.result["metadata"]["mode"], "dry_run_classification")

    def test_metadata_generated_at_iso_parsable(self):
        """ARCH-0476: generated_at_iso is a parsable ISO datetime."""
        from datetime import datetime
        val = self.result["metadata"]["generated_at_iso"]
        self.assertTrue(val)
        dt = datetime.fromisoformat(val)
        self.assertIsNotNone(dt)

    def test_input_tool_propagated(self):
        """ARCH-0471: input_tool taken from input metadata.tool."""
        self.assertEqual(self.result["metadata"]["input_tool"], "inventory_readonly.py")

    def test_input_schema_version_propagated(self):
        """ARCH-0472: input_schema_version taken from input metadata.schema_version."""
        self.assertEqual(self.result["metadata"]["input_schema_version"], "1.0")

    def test_input_fields_empty_when_no_metadata(self):
        """ARCH-0471/0472: input_tool and input_schema_version are empty when absent."""
        result = classify_inventory({"files": []})
        self.assertEqual(result["metadata"]["input_tool"], "")
        self.assertEqual(result["metadata"]["input_schema_version"], "")


# ── ARCH-0478/0481/0482: deterministic ordering ───────────────────────────────

class TestDeterministicOrder(unittest.TestCase):
    """ARCH-0478/0481/0482: deterministic ordering of output structures."""

    def _make_inventory(self, paths):
        return {
            "files": [
                {"relative_path": p, "filename": p.split("/")[-1],
                 "extension": "." + p.split(".")[-1], "size_bytes": 1}
                for p in paths
            ]
        }

    def test_classifications_sorted_by_relative_path(self):
        """ARCH-0478: classifications sorted by relative_path regardless of input order."""
        inv = self._make_inventory(["z_last.pdf", "a_first.pdf", "m_middle.pdf"])
        result = classify_inventory(inv)
        paths = [c["relative_path"] for c in result["classifications"]]
        self.assertEqual(paths, sorted(paths))

    def test_categories_count_stable_tie_break(self):
        """ARCH-0481: categories_count uses name as tie-breaker."""
        counts = build_category_counts([
            {"category": "Zebra"},
            {"category": "Apple"},
        ])
        keys = list(counts.keys())
        self.assertEqual(keys[0], "Apple", "tie should break alphabetically")

    def test_location_policy_counts_stable_tie_break(self):
        """ARCH-0482: location_policy_counts uses name as tie-breaker."""
        counts = build_location_policy_counts([
            {"location_policy": "zzz_policy"},
            {"location_policy": "aaa_policy"},
        ])
        keys = list(counts.keys())
        self.assertEqual(keys[0], "aaa_policy", "tie should break alphabetically")


# ── ARCH-0484: confidence_buckets ─────────────────────────────────────────────

class TestConfidenceBuckets(unittest.TestCase):
    """ARCH-0484: build_confidence_buckets correctness."""

    def test_buckets_correct(self):
        """ARCH-0484: high >= 0.75, medium >= 0.55, low < 0.55."""
        classifications = [
            {"confidence": 0.90},
            {"confidence": 0.80},
            {"confidence": 0.65},
            {"confidence": 0.55},
            {"confidence": 0.40},
            {"confidence": 0.30},
        ]
        buckets = build_confidence_buckets(classifications)
        self.assertEqual(buckets["high"], 2)
        self.assertEqual(buckets["medium"], 2)
        self.assertEqual(buckets["low"], 2)

    def test_buckets_in_summary(self):
        """ARCH-0484: confidence_buckets present in classify_inventory summary."""
        inv = {
            "files": [
                {"relative_path": "a.pdf", "filename": "a.pdf", "extension": ".pdf", "size_bytes": 1},
                {"relative_path": "b.xyzunknown", "filename": "b.xyzunknown",
                 "extension": ".xyzunknown", "size_bytes": 1},
            ]
        }
        result = classify_inventory(inv)
        buckets = result["summary"].get("confidence_buckets")
        self.assertIsNotNone(buckets)
        for key in ("high", "medium", "low"):
            self.assertIn(key, buckets)


# ── ARCH-0487: root_file_count / context_bound_count ─────────────────────────

class TestRootAndContextCounts(unittest.TestCase):
    """ARCH-0485..0487: root_file_count and context_bound_count."""

    def test_root_and_context_counts(self):
        """ARCH-0487: counts match root vs context-bound files."""
        inv = {
            "files": [
                {"relative_path": "root1.pdf", "filename": "root1.pdf",
                 "extension": ".pdf", "size_bytes": 1},
                {"relative_path": "root2.jpg", "filename": "root2.jpg",
                 "extension": ".jpg", "size_bytes": 1},
                {"relative_path": "sub/nested.pdf", "filename": "nested.pdf",
                 "extension": ".pdf", "size_bytes": 1},
            ]
        }
        result = classify_inventory(inv)
        self.assertEqual(result["summary"]["root_file_count"], 2)
        self.assertEqual(result["summary"]["context_bound_count"], 1)

    def test_all_root_files(self):
        """ARCH-0487: all root files → context_bound_count == 0."""
        inv = {"files": [
            {"relative_path": "a.txt", "filename": "a.txt", "extension": ".txt", "size_bytes": 1},
        ]}
        result = classify_inventory(inv)
        self.assertEqual(result["summary"]["root_file_count"], 1)
        self.assertEqual(result["summary"]["context_bound_count"], 0)


# ── ARCH-0488: help wording ───────────────────────────────────────────────────

class TestClassifyInventoryHelp(unittest.TestCase):
    """ARCH-0488: --help exits 0 and contains safe wording."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        result = subprocess.run(
            [sys.executable,
             str(Path(__file__).parent.parent / "scripts" / "classify_inventory.py"),
             "--help"],
            capture_output=True, text=True,
        )
        cls._help = result.stdout + result.stderr
        cls._code = result.returncode

    def test_help_exits_zero(self):
        """ARCH-0488: --help exits 0."""
        self.assertEqual(self._code, 0, f"--help exited {self._code}")

    def test_help_mentions_dry_run(self):
        """ARCH-0488: help mentions dry-run."""
        self.assertIn("dry-run", self._help.lower())

    def test_help_no_destructive_language(self):
        """ARCH-0488: help has no destructive language."""
        lower = self._help.lower()
        for phrase in ("will delete", "will move", "will rename",
                       "cancella automaticamente", "sposta automaticamente"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)

    def test_help_no_cloud_api(self):
        """ARCH-0488: help has no cloud/API/n8n/MCP references."""
        lower = self._help.lower()
        for phrase in ("api_key", "access_token", "n8n", " mcp", "s3://"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)


if __name__ == "__main__":
    unittest.main()
