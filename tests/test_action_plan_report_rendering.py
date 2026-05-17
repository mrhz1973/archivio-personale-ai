"""
Regression tests for duplicate table rendering in generate_action_plan_report.
Verifies that HTML contains the structure required to display duplicate groups
and that the JS data embedding approach is robust.
All tests use in-memory data only.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_action_plan_report import build_html


_DATA_TWO_GROUPS = {
    "summary": {
        "source": "C:/Test",
        "total_files": 4,
        "root_sort_candidates_count": 0,
        "duplicate_groups_count": 2,
        "duplicate_files_count": 4,
        "keep_in_place_count": 2,
        "potential_reclaimable_bytes": 300,
        "duplicate_priority_counts": {"review_only": 1, "higher_review_value": 1},
    },
    "root_sort_candidates": [],
    "duplicate_groups": [
        {
            "sha256": "abc123def456abc1",
            "count": 2,
            "total_size_bytes": 200,
            "potential_reclaimable_bytes": 100,
            "status": "review_only",
            "review_priority": "review_only",
            "review_priority_reason": "test reason",
            "dry_run_only": True,
            "files": [
                {
                    "relative_path": "folder_a/document.pdf",
                    "top_level_folder": "folder_a",
                    "location_policy": "keep_in_place",
                    "context_bound": True,
                    "size_bytes": 100,
                },
                {
                    "relative_path": "folder_b/document.pdf",
                    "top_level_folder": "folder_b",
                    "location_policy": "keep_in_place",
                    "context_bound": True,
                    "size_bytes": 100,
                },
            ],
        },
        {
            "sha256": "deadbeef12345678",
            "count": 2,
            "total_size_bytes": 400,
            "potential_reclaimable_bytes": 200,
            "status": "review_only",
            "review_priority": "higher_review_value",
            "review_priority_reason": "same name, different folders",
            "dry_run_only": True,
            "files": [
                {
                    "relative_path": "root_file.docx",
                    "top_level_folder": "",
                    "location_policy": "classify_only",
                    "context_bound": False,
                    "size_bytes": 200,
                },
                {
                    "relative_path": "subfolder/root_file.docx",
                    "top_level_folder": "subfolder",
                    "location_policy": "classify_only",
                    "context_bound": False,
                    "size_bytes": 200,
                },
            ],
        },
    ],
}


class TestDuplicateTableStructure(unittest.TestCase):
    def setUp(self):
        self.html = build_html(_DATA_TWO_GROUPS)

    def test_dup_tbody_present(self):
        self.assertIn('id="dup-tbody"', self.html)

    def test_dup_data_element_present(self):
        """Data must be embedded in a dedicated element, not as a raw inline JS variable."""
        self.assertIn('id="dup-data"', self.html)

    def test_js_parses_from_element(self):
        """JS must use JSON.parse on the data element, not embed the variable inline."""
        self.assertIn("JSON.parse", self.html)
        self.assertIn("dup-data", self.html)

    def test_embedded_json_contains_sha256_values(self):
        self.assertIn("abc123def456abc1", self.html)
        self.assertIn("deadbeef12345678", self.html)

    def test_embedded_json_contains_file_paths(self):
        self.assertIn("folder_a/document.pdf", self.html)
        self.assertIn("folder_b/document.pdf", self.html)
        self.assertIn("subfolder/root_file.docx", self.html)

    def test_empty_state_element_present(self):
        self.assertIn('id="dup-empty-state"', self.html)
        self.assertIn("Nessun gruppo duplicato", self.html)

    def test_reset_filters_button_present(self):
        self.assertIn("Azzera filtri", self.html)
        self.assertIn('id="btn-reset-filters"', self.html)


class TestMissingOptionalFields(unittest.TestCase):
    def test_missing_all_optional_fields(self):
        """build_html must not raise when optional duplicate file fields are absent."""
        data = {
            "summary": {
                "source": "C:/Test",
                "total_files": 2,
                "root_sort_candidates_count": 0,
                "duplicate_groups_count": 1,
                "duplicate_files_count": 2,
                "keep_in_place_count": 0,
                "potential_reclaimable_bytes": 0,
                "duplicate_priority_counts": {},
            },
            "root_sort_candidates": [],
            "duplicate_groups": [
                {
                    "sha256": "minimalsha256hash",
                    "count": 2,
                    "files": [
                        {"relative_path": "file_a.txt"},
                        {"relative_path": "file_b.txt"},
                    ],
                }
            ],
        }
        html = build_html(data)
        self.assertIn("minimalsha256hash", html)
        self.assertIn("file_a.txt", html)
        self.assertIn("file_b.txt", html)

    def test_missing_top_level_folder(self):
        data = {
            "summary": {
                "source": "C:/Test",
                "total_files": 2,
                "root_sort_candidates_count": 0,
                "duplicate_groups_count": 1,
                "duplicate_files_count": 2,
                "keep_in_place_count": 0,
                "potential_reclaimable_bytes": 0,
                "duplicate_priority_counts": {},
            },
            "root_sort_candidates": [],
            "duplicate_groups": [
                {
                    "sha256": "sha256notopfolder",
                    "count": 2,
                    "files": [
                        {"relative_path": "a.txt", "size_bytes": 10, "context_bound": False},
                        {"relative_path": "b.txt", "size_bytes": 10, "context_bound": False},
                    ],
                }
            ],
        }
        html = build_html(data)
        self.assertIn("sha256notopfolder", html)
        self.assertNotIn("undefined", html)


class TestSafetyWordingPreserved(unittest.TestCase):
    def setUp(self):
        self.html = build_html(_DATA_TWO_GROUPS)

    def test_solo_revisione_present(self):
        self.assertIn("Solo revisione", self.html)

    def test_nessuna_cancellazione_present(self):
        self.assertIn("Nessuna cancellazione", self.html)

    def test_spazio_teorico_present(self):
        self.assertIn("teorico", self.html.lower())

    def test_cautela_extra_present(self):
        self.assertIn("cautela extra", self.html)

    def test_no_destructive_action_wording(self):
        for word in ("cancella ora", "sposta ora", "elimina", "delete now"):
            self.assertNotIn(word, self.html.lower())


if __name__ == "__main__":
    unittest.main()
