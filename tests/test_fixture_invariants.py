"""
ARCH-0193..ARCH-0197 — Shared fixture invariant tests.

Confirms that shared synthetic fixtures in tests/helpers.py contain only
synthetic/temp paths, no personal data, no reports/ references, and that
the safety-critical flags (review_only, dry_run_only) remain set.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.classify_inventory import main as _cls_main
from tests.helpers import (
    TmpDirMixin,
    SYNTHETIC_INVENTORY,
    SYNTHETIC_CLASSIFICATION,
    SYNTHETIC_ACTION_PLAN,
)

_REPO_ROOT = Path(__file__).parent.parent
_REPORTS_DIR = str(_REPO_ROOT / "reports")

_ALL_FIXTURES = [SYNTHETIC_INVENTORY, SYNTHETIC_CLASSIFICATION, SYNTHETIC_ACTION_PLAN]


def _all_strings(obj):
    """Recursively yield all string values in a nested dict/list."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _all_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _all_strings(item)


# ── ARCH-0193: fixtures must not contain real personal paths ──────────────────

class TestFixturesNoPersonalPaths(unittest.TestCase):

    def _check_no_personal_path(self, fixture):
        real_home = str(Path.home())
        for s in _all_strings(fixture):
            self.assertFalse(
                s.startswith(real_home),
                f"fixture string looks like a real personal path: {s!r}",
            )

    def test_inventory_no_personal_paths(self):
        self._check_no_personal_path(SYNTHETIC_INVENTORY)

    def test_classification_no_personal_paths(self):
        self._check_no_personal_path(SYNTHETIC_CLASSIFICATION)

    def test_action_plan_no_personal_paths(self):
        self._check_no_personal_path(SYNTHETIC_ACTION_PLAN)


# ── ARCH-0194: fixtures must not reference reports/ as output ─────────────────

class TestFixturesNoReportsDir(unittest.TestCase):

    def _check_no_reports_ref(self, fixture):
        for s in _all_strings(fixture):
            self.assertNotIn(
                "reports/",
                s,
                f"fixture string references reports/: {s!r}",
            )
            self.assertNotIn(
                "reports\\",
                s,
                f"fixture string references reports\\: {s!r}",
            )

    def test_inventory_no_reports_reference(self):
        self._check_no_reports_ref(SYNTHETIC_INVENTORY)

    def test_classification_no_reports_reference(self):
        self._check_no_reports_ref(SYNTHETIC_CLASSIFICATION)

    def test_action_plan_no_reports_reference(self):
        self._check_no_reports_ref(SYNTHETIC_ACTION_PLAN)


# ── ARCH-0195: fixture source paths must be synthetic ────────────────────────

class TestFixturesSyntheticSourcePaths(unittest.TestCase):

    _ALLOWED_PREFIXES = ("C:/Synthetic", "temp", "tmp", "/tmp")

    def _is_synthetic(self, path_str):
        return any(path_str.startswith(p) for p in self._ALLOWED_PREFIXES)

    def test_inventory_source_is_synthetic(self):
        source = SYNTHETIC_INVENTORY["summary"]["source"]
        self.assertTrue(self._is_synthetic(source), f"inventory source not synthetic: {source!r}")

    def test_classification_source_is_synthetic(self):
        source = SYNTHETIC_CLASSIFICATION["summary"]["source"]
        self.assertTrue(self._is_synthetic(source), f"classification source not synthetic: {source!r}")

    def test_action_plan_source_is_synthetic(self):
        source = SYNTHETIC_ACTION_PLAN["summary"]["source"]
        self.assertTrue(self._is_synthetic(source), f"action plan source not synthetic: {source!r}")


# ── ARCH-0196: action plan fixture root_sort_candidates must be review_only ───

class TestActionPlanFixtureReviewOnly(unittest.TestCase):

    def test_root_sort_candidates_status_review_only(self):
        for candidate in SYNTHETIC_ACTION_PLAN["root_sort_candidates"]:
            self.assertEqual(
                candidate.get("status"),
                "review_only",
                f"candidate status is not review_only: {candidate.get('relative_path')!r}",
            )

    def test_duplicate_groups_status_review_only(self):
        for group in SYNTHETIC_ACTION_PLAN["duplicate_groups"]:
            self.assertIn(
                group.get("status"),
                ("review_only", None),
                f"duplicate group status is not review_only: {group.get('sha256')!r}",
            )


# ── ARCH-0197: classify_inventory produces dry_run_only on shared fixture ─────

class TestClassificationDryRunOnlyInvariant(TmpDirMixin):

    def test_shared_inventory_produces_dry_run_only_classifications(self):
        inp = self._write_json(SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        with patch("sys.argv", ["classify_inventory.py", "--input", inp, "--output", out]):
            _cls_main()
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["summary"]["dry_run_only"])
        for item in data["classifications"]:
            self.assertTrue(
                item.get("dry_run_only"),
                f"dry_run_only not set on {item.get('relative_path')!r}",
            )


if __name__ == "__main__":
    unittest.main()
