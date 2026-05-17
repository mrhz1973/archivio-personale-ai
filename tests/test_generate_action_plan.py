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
    build_sort_candidates,
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


if __name__ == "__main__":
    unittest.main()
