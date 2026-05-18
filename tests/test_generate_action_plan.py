"""
Unit tests for generate_action_plan.py.
All tests use in-memory data only and never touch real user archive paths.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_action_plan import (
    build_action_plan,
    build_duplicate_groups,
    build_priority_counts,
    build_sort_candidates,
    fmt_size,
    is_root_file,
)


class TestRootFile(unittest.TestCase):
    def test_root_file(self):
        self.assertTrue(is_root_file("photo.jpg"))

    def test_nested_file(self):
        self.assertFalse(is_root_file("Project/photo.jpg"))

    def test_windows_nested_file(self):
        self.assertFalse(is_root_file("Project\\photo.jpg"))


class TestActionPlan(unittest.TestCase):
    def test_root_media_candidate(self):
        inventory = {
            "photo.jpg": {
                "relative_path": "photo.jpg",
                "filename": "photo.jpg",
                "extension": ".jpg",
                "size_bytes": 10,
                "sha256": "a",
            }
        }
        classifications = {
            "photo.jpg": {
                "relative_path": "photo.jpg",
                "category": "Images",
                "confidence": 0.72,
                "location_policy": "classify_only",
            }
        }
        result = build_sort_candidates(inventory, classifications)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["action_type"], "root_sort_candidate")
        self.assertEqual(result[0]["status"], "requires_manual_approval")
        self.assertEqual(result[0]["proposed_destination_relative_path"], "Foto/photo.jpg")

    def test_context_bound_file_not_candidate(self):
        inventory = {
            "Project/photo.jpg": {
                "relative_path": "Project/photo.jpg",
                "filename": "photo.jpg",
                "extension": ".jpg",
                "size_bytes": 10,
                "sha256": "a",
            }
        }
        classifications = {
            "Project/photo.jpg": {
                "relative_path": "Project/photo.jpg",
                "category": "Images",
                "confidence": 0.72,
                "location_policy": "keep_in_place",
            }
        }
        result = build_sort_candidates(inventory, classifications)
        self.assertEqual(result, [])

    def test_duplicate_group_review_only(self):
        inventory = {
            "a/file.pdf": {"relative_path": "a/file.pdf", "size_bytes": 10, "sha256": "same"},
            "b/file.pdf": {"relative_path": "b/file.pdf", "size_bytes": 10, "sha256": "same"},
        }
        classifications = {
            "a/file.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
            "b/file.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
        }
        result = build_duplicate_groups(inventory, classifications)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "review_only")
        self.assertEqual(result[0]["count"], 2)
        self.assertTrue(result[0]["dry_run_only"])

    def test_action_plan_summary(self):
        inventory_data = {
            "summary": {"source": "C:/Archivio_Test"},
            "files": [
                {"relative_path": "photo.jpg", "filename": "photo.jpg", "extension": ".jpg", "size_bytes": 1, "sha256": "x"},
                {"relative_path": "Project/photo.jpg", "filename": "photo.jpg", "extension": ".jpg", "size_bytes": 1, "sha256": "x"},
            ],
        }
        classifications_data = {
            "summary": {"location_policy_counts": {"classify_only": 1, "keep_in_place": 1}},
            "classifications": [
                {"relative_path": "photo.jpg", "category": "Images", "confidence": 0.72, "location_policy": "classify_only"},
                {"relative_path": "Project/photo.jpg", "category": "Images", "confidence": 0.72, "location_policy": "keep_in_place", "context_bound": True},
            ],
        }
        plan = build_action_plan(inventory_data, classifications_data)
        self.assertEqual(plan["summary"]["root_sort_candidates_count"], 1)
        self.assertEqual(plan["summary"]["duplicate_groups_count"], 1)
        self.assertEqual(plan["summary"]["keep_in_place_count"], 1)
        self.assertTrue(plan["summary"]["dry_run_only"])

    def test_potential_reclaimable_bytes_calculated(self):
        inventory = {
            "a/file.pdf": {"relative_path": "a/file.pdf", "size_bytes": 500, "sha256": "dup"},
            "b/file.pdf": {"relative_path": "b/file.pdf", "size_bytes": 500, "sha256": "dup"},
            "c/file.pdf": {"relative_path": "c/file.pdf", "size_bytes": 500, "sha256": "dup"},
        }
        classifications = {
            "a/file.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
            "b/file.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
            "c/file.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
        }
        result = build_duplicate_groups(inventory, classifications)
        self.assertEqual(len(result), 1)
        group = result[0]
        # 3 copies × 500 B each; keeping one means 1000 B is theoretically reclaimable
        self.assertEqual(group["potential_reclaimable_bytes"], 1000)

    def test_review_priority_field_exists(self):
        inventory = {
            "a/x.txt": {"relative_path": "a/x.txt", "size_bytes": 10, "sha256": "abc"},
            "b/x.txt": {"relative_path": "b/x.txt", "size_bytes": 10, "sha256": "abc"},
        }
        classifications = {
            "a/x.txt": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": False},
            "b/x.txt": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": False},
        }
        result = build_duplicate_groups(inventory, classifications)
        self.assertEqual(len(result), 1)
        group = result[0]
        self.assertIn("review_priority", group)
        self.assertIn("review_priority_reason", group)
        self.assertIsInstance(group["review_priority"], str)
        self.assertTrue(len(group["review_priority"]) > 0)

    def test_context_bound_cross_folder_gets_low_risk_priority(self):
        # All context-bound, different top-level folders → low_context_risk_review
        inventory = {
            "Alpha/report.pdf": {"relative_path": "Alpha/report.pdf", "size_bytes": 100, "sha256": "xyz"},
            "Beta/report.pdf": {"relative_path": "Beta/report.pdf", "size_bytes": 100, "sha256": "xyz"},
        }
        classifications = {
            "Alpha/report.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
            "Beta/report.pdf": {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True},
        }
        result = build_duplicate_groups(inventory, classifications)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["review_priority"], "low_context_risk_review")

    def test_no_destructive_action_fields(self):
        inventory_data = {
            "summary": {},
            "files": [
                {"relative_path": "photo.jpg", "filename": "photo.jpg", "extension": ".jpg", "size_bytes": 1, "sha256": "x"},
            ],
        }
        classifications_data = {
            "summary": {"location_policy_counts": {"classify_only": 1}},
            "classifications": [
                {"relative_path": "photo.jpg", "category": "Images", "confidence": 0.72, "location_policy": "classify_only"},
            ],
        }
        plan = build_action_plan(inventory_data, classifications_data)
        forbidden = {"delete", "rename_to", "move_now", "execute", "destination_path"}
        for item in plan["root_sort_candidates"]:
            self.assertTrue(forbidden.isdisjoint(item.keys()))


# ── ARCH-0525..0528: metadata ─────────────────────────────────────────────────

class TestActionPlanMetadata(unittest.TestCase):
    """ARCH-0525..0528: metadata field presence and correctness."""

    def _make_plan(self, inv_meta=None, cls_meta=None):
        inv = {
            "summary": {"source": "/tmp"},
            "files": [
                {"relative_path": "a.pdf", "filename": "a.pdf",
                 "extension": ".pdf", "size_bytes": 1, "sha256": "x"},
            ],
        }
        cls = {
            "summary": {"location_policy_counts": {"classify_only": 1}},
            "classifications": [
                {"relative_path": "a.pdf", "category": "Documents",
                 "confidence": 0.70, "location_policy": "classify_only"},
            ],
        }
        if inv_meta:
            inv["metadata"] = inv_meta
        if cls_meta:
            cls["metadata"] = cls_meta
        return build_action_plan(inv, cls)

    def test_metadata_field_present(self):
        """ARCH-0525: top-level metadata exists."""
        plan = self._make_plan()
        self.assertIn("metadata", plan)

    def test_metadata_subfields_all_present(self):
        """ARCH-0526: all expected subfields present."""
        plan = self._make_plan(
            inv_meta={"tool": "inventory_readonly.py", "schema_version": "1.0"},
            cls_meta={"tool": "classify_inventory.py", "schema_version": "1.0"},
        )
        m = plan["metadata"]
        for key in ("schema_version", "generated_at_iso", "tool", "mode",
                    "inventory_tool", "classifications_tool",
                    "inventory_schema_version", "classifications_schema_version"):
            self.assertIn(key, m, f"metadata.{key} missing")

    def test_metadata_mode_review_only_action_plan(self):
        """ARCH-0527: metadata.mode == review_only_action_plan."""
        plan = self._make_plan()
        self.assertEqual(plan["metadata"]["mode"], "review_only_action_plan")

    def test_metadata_generated_at_iso_parsable(self):
        """ARCH-0528: generated_at_iso is parsable ISO datetime."""
        from datetime import datetime
        val = self._make_plan()["metadata"]["generated_at_iso"]
        self.assertTrue(val)
        self.assertIsNotNone(datetime.fromisoformat(val))

    def test_inventory_tool_propagated(self):
        """ARCH-0521: inventory_tool from input metadata.tool."""
        plan = self._make_plan(inv_meta={"tool": "inventory_readonly.py", "schema_version": "1.0"})
        self.assertEqual(plan["metadata"]["inventory_tool"], "inventory_readonly.py")

    def test_classifications_tool_propagated(self):
        """ARCH-0522: classifications_tool from input metadata.tool."""
        plan = self._make_plan(cls_meta={"tool": "classify_inventory.py", "schema_version": "1.0"})
        self.assertEqual(plan["metadata"]["classifications_tool"], "classify_inventory.py")

    def test_input_fields_empty_when_no_metadata(self):
        """ARCH-0521..0524: all input fields empty when metadata absent."""
        plan = self._make_plan()
        m = plan["metadata"]
        self.assertEqual(m["inventory_tool"], "")
        self.assertEqual(m["classifications_tool"], "")
        self.assertEqual(m["inventory_schema_version"], "")
        self.assertEqual(m["classifications_schema_version"], "")


# ── ARCH-0530: deterministic sort_candidates order ────────────────────────────

class TestDeterministicSortCandidates(unittest.TestCase):
    """ARCH-0529/0530: root_sort_candidates sorted by relative_path."""

    def test_candidates_sorted_alphabetically(self):
        inventory = {
            "z_last.jpg": {"relative_path": "z_last.jpg", "size_bytes": 1, "sha256": "a"},
            "a_first.jpg": {"relative_path": "a_first.jpg", "size_bytes": 1, "sha256": "b"},
            "m_mid.jpg": {"relative_path": "m_mid.jpg", "size_bytes": 1, "sha256": "c"},
        }
        classifications = {
            "z_last.jpg": {"category": "Images", "confidence": 0.72, "location_policy": "classify_only"},
            "a_first.jpg": {"category": "Images", "confidence": 0.72, "location_policy": "classify_only"},
            "m_mid.jpg": {"category": "Images", "confidence": 0.72, "location_policy": "classify_only"},
        }
        result = build_sort_candidates(inventory, classifications)
        paths = [c["relative_path"] for c in result]
        self.assertEqual(paths, sorted(paths))


# ── ARCH-0532: deterministic duplicate_groups tie-break ──────────────────────

class TestDeterministicDuplicateGroups(unittest.TestCase):
    """ARCH-0531/0532: duplicate_groups tie-break by sha256."""

    def test_duplicate_groups_stable_sha256_tiebreak(self):
        """ARCH-0532: equal reclaimable/count/size → sha256 tiebreak."""
        inventory = {
            "a/x.pdf": {"relative_path": "a/x.pdf", "size_bytes": 100, "sha256": "zzz"},
            "b/x.pdf": {"relative_path": "b/x.pdf", "size_bytes": 100, "sha256": "zzz"},
            "a/y.pdf": {"relative_path": "a/y.pdf", "size_bytes": 100, "sha256": "aaa"},
            "b/y.pdf": {"relative_path": "b/y.pdf", "size_bytes": 100, "sha256": "aaa"},
        }
        classifications = {
            k: {"category": "Documents", "location_policy": "keep_in_place", "context_bound": True}
            for k in inventory
        }
        result = build_duplicate_groups(inventory, classifications)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sha256"], "aaa")
        self.assertEqual(result[1]["sha256"], "zzz")


# ── ARCH-0534: deterministic duplicate_priority_counts tie-break ──────────────

class TestDeterministicPriorityCounts(unittest.TestCase):
    """ARCH-0533/0534: duplicate_priority_counts tie-break by name."""

    def test_priority_counts_stable_tie_break(self):
        """ARCH-0534: equal counts → alphabetical tie-break."""
        groups = [
            {"review_priority": "zzz_priority"},
            {"review_priority": "aaa_priority"},
        ]
        counts = build_priority_counts(groups)
        keys = list(counts.keys())
        self.assertEqual(keys[0], "aaa_priority")


# ── ARCH-0537: fmt_size / potential_reclaimable_human ─────────────────────────

class TestFmtSize(unittest.TestCase):
    """ARCH-0536/0537: fmt_size helper correctness."""

    def test_zero_bytes(self):
        self.assertEqual(fmt_size(0), "0.0 B")

    def test_small_bytes(self):
        self.assertEqual(fmt_size(512), "512.0 B")

    def test_kib(self):
        self.assertEqual(fmt_size(1024), "1.0 KiB")

    def test_mib(self):
        self.assertEqual(fmt_size(1024 * 1024), "1.0 MiB")

    def test_potential_reclaimable_human_in_summary(self):
        """ARCH-0535: potential_reclaimable_human present in action plan summary."""
        inv_data = {
            "summary": {"source": "/tmp"},
            "files": [
                {"relative_path": "a/f.pdf", "filename": "f.pdf", "extension": ".pdf",
                 "size_bytes": 2048, "sha256": "dup"},
                {"relative_path": "b/f.pdf", "filename": "f.pdf", "extension": ".pdf",
                 "size_bytes": 2048, "sha256": "dup"},
            ],
        }
        cls_data = {
            "summary": {"location_policy_counts": {"keep_in_place": 2}},
            "classifications": [
                {"relative_path": "a/f.pdf", "category": "Documents",
                 "confidence": 0.70, "location_policy": "keep_in_place", "context_bound": True},
                {"relative_path": "b/f.pdf", "category": "Documents",
                 "confidence": 0.70, "location_policy": "keep_in_place", "context_bound": True},
            ],
        }
        plan = build_action_plan(inv_data, cls_data)
        self.assertIn("potential_reclaimable_human", plan["summary"])
        self.assertIn("KiB", plan["summary"]["potential_reclaimable_human"])


# ── ARCH-0538: help wording ───────────────────────────────────────────────────

class TestGenerateActionPlanHelp(unittest.TestCase):
    """ARCH-0538: --help exits 0 and contains safe wording."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        result = subprocess.run(
            [sys.executable,
             str(Path(__file__).parent.parent / "scripts" / "generate_action_plan.py"),
             "--help"],
            capture_output=True, text=True,
        )
        cls._help = result.stdout + result.stderr
        cls._code = result.returncode

    def test_help_exits_zero(self):
        self.assertEqual(self._code, 0, f"--help exited {self._code}")

    def test_help_mentions_review_only(self):
        self.assertIn("review-only", self._help.lower())

    def test_help_no_cloud_api(self):
        lower = self._help.lower()
        for phrase in ("api_key", "access_token", "n8n", " mcp", "s3://"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)

    def test_help_no_auto_open(self):
        lower = self._help.lower()
        for phrase in ("open automatically", "apri automaticamente", "auto-open"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)


if __name__ == "__main__":
    unittest.main()
