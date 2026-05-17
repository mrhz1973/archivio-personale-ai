"""Shared test helpers and synthetic fixtures. All data is synthetic/temp only."""

import json
import os
import shutil
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Shared minimal synthetic fixtures
# All paths use "C:/Synthetic" (not a real personal path).
# These are reused by test_cli_smoke.py, test_safety_assertions.py, and
# test_fixture_invariants.py to avoid duplicating fixture definitions.
# ---------------------------------------------------------------------------

SYNTHETIC_INVENTORY = {
    "summary": {
        "source": "C:/Synthetic",
        "total_files": 2,
        "total_size_bytes": 200,
        "extensions_count": {".pdf": 1, ".jpg": 1},
        "skipped_count": 0,
        "errors_count": 0,
    },
    "files": [
        {
            "relative_path": "doc.pdf",
            "filename": "doc.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
            "modified_time_iso": "2025-01-01T00:00:00",
            "sha256": "aaa",
        },
        {
            "relative_path": "subfolder/photo.jpg",
            "filename": "photo.jpg",
            "extension": ".jpg",
            "size_bytes": 100,
            "modified_time_iso": "2025-01-02T00:00:00",
            "sha256": "bbb",
        },
    ],
    "errors": [],
}

SYNTHETIC_CLASSIFICATION = {
    "summary": {
        "source": "C:/Synthetic",
        "total_files": 1,
        "low_confidence_count": 0,
        "categories_count": {"Documents": 1},
        "location_policy_counts": {"classify_only": 1},
    },
    "classifications": [
        {
            "relative_path": "doc.pdf",
            "category": "Documents",
            "location_policy": "classify_only",
            "confidence": 0.90,
            "signals": ["ext:.pdf"],
            "suggested_folder": "Documents",
            "size_bytes": 100,
        }
    ],
}

SYNTHETIC_ACTION_PLAN = {
    "summary": {
        "source": "C:/Synthetic",
        "total_files": 1,
        "root_sort_candidates_count": 1,
        "duplicate_groups_count": 0,
        "duplicate_files_count": 0,
        "keep_in_place_count": 0,
        "potential_reclaimable_bytes": 0,
        "duplicate_priority_counts": {},
    },
    "root_sort_candidates": [
        {
            "relative_path": "orphan.pdf",
            "category": "Documents",
            "confidence": 0.85,
            "proposed_destination_relative_path": "Documenti/orphan.pdf",
            "status": "review_only",
        }
    ],
    "duplicate_groups": [],
}


class TmpDirMixin(unittest.TestCase):
    """Mixin providing a per-test temp directory with cleanup."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="archivio_test_")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _path(self, name):
        return os.path.join(self._tmpdir, name)

    def _out(self, name):
        return self._path(name)

    def _write_json(self, data, name):
        p = self._path(name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return p
