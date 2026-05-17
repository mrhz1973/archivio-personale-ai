"""
ARCH-0096..ARCH-0102 — Report generator regression tests.

All tests use synthetic data and temporary directories only.
No personal files, no reports/ directory, no real archive data.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Allow importing from scripts/ as modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_inventory_report import main as _inventory_main
from scripts.generate_classification_report import main as _classification_main
from scripts.generate_action_plan_report import main as _action_plan_main
import scripts.validate_reports as vr


def inventory_main(args):
    with patch("sys.argv", ["generate_inventory_report.py"] + list(args)):
        _inventory_main()


def classification_main(args):
    with patch("sys.argv", ["generate_classification_report.py"] + list(args)):
        _classification_main()


def action_plan_main(args):
    with patch("sys.argv", ["generate_action_plan_report.py"] + list(args)):
        _action_plan_main()


# ── synthetic fixtures ─────────────────────────────────────────────────────────

SYNTHETIC_INVENTORY = {
    "summary": {
        "source": "C:/Synthetic_Test",
        "total_files": 2,
        "total_size_bytes": 2048,
        "extensions_count": {".txt": 1, ".pdf": 1},
        "skipped_count": 0,
        "errors_count": 0,
    },
    "files": [
        {
            "relative_path": "note.txt",
            "filename": "note.txt",
            "extension": ".txt",
            "size_bytes": 1024,
            "modified_time_iso": "2025-01-01T00:00:00",
            "sha256": "aaa111",
        },
        {
            "relative_path": "doc.pdf",
            "filename": "doc.pdf",
            "extension": ".pdf",
            "size_bytes": 1024,
            "modified_time_iso": "2025-01-02T00:00:00",
            "sha256": "bbb222",
        },
    ],
    "errors": [],
}

SYNTHETIC_CLASSIFICATION = {
    "summary": {
        "source": "C:/Synthetic_Test",
        "total_files": 2,
        "low_confidence_count": 0,
        "categories_count": {"Documents": 1, "Text": 1},
        "location_policy_counts": {"classify_only": 2},
    },
    "classifications": [
        {
            "relative_path": "note.txt",
            "category": "Text",
            "location_policy": "classify_only",
            "confidence": 0.85,
            "signals": ["ext:.txt"],
            "suggested_folder": "Testi",
            "size_bytes": 1024,
        },
        {
            "relative_path": "doc.pdf",
            "category": "Documents",
            "location_policy": "classify_only",
            "confidence": 0.90,
            "signals": ["ext:.pdf"],
            "suggested_folder": "Documenti",
            "size_bytes": 1024,
        },
    ],
}

SYNTHETIC_ACTION_PLAN = {
    "summary": {
        "source": "C:/Synthetic_Test",
        "total_files": 4,
        "root_sort_candidates_count": 1,
        "duplicate_groups_count": 1,
        "duplicate_files_count": 2,
        "keep_in_place_count": 2,
        "potential_reclaimable_bytes": 1024,
        "duplicate_priority_counts": {"review_only": 1},
    },
    "root_sort_candidates": [
        {
            "relative_path": "orphan.txt",
            "category": "Text",
            "confidence": 0.75,
            "proposed_destination_relative_path": "Testi/orphan.txt",
            "status": "review_only",
        }
    ],
    "duplicate_groups": [
        {
            "sha256": "deadbeef00000000",
            "count": 2,
            "total_size_bytes": 2048,
            "potential_reclaimable_bytes": 1024,
            "status": "review_only",
            "review_priority": "review_only",
            "review_priority_reason": "synthetic test",
            "dry_run_only": True,
            "files": [
                {
                    "relative_path": "a/copy.pdf",
                    "top_level_folder": "a",
                    "location_policy": "keep_in_place",
                    "context_bound": True,
                    "size_bytes": 1024,
                },
                {
                    "relative_path": "b/copy.pdf",
                    "top_level_folder": "b",
                    "location_policy": "keep_in_place",
                    "context_bound": True,
                    "size_bytes": 1024,
                },
            ],
        }
    ],
}


# ── base test mixin ────────────────────────────────────────────────────────────

class TmpDirMixin(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="archivio_test_")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _write_json(self, data, name):
        path = os.path.join(self._tmpdir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    def _out(self, name):
        return os.path.join(self._tmpdir, name)

    def _read_html(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


# ── ARCH-0096: generate to temp dir ───────────────────────────────────────────

class TestGenerateToTempDir(TmpDirMixin):

    def test_inventory_report_written_to_tmpdir(self):
        src = self._write_json(SYNTHETIC_INVENTORY, "inventory.json")
        out = self._out("inventory_report.html")
        inventory_main(["--input", src, "--output", out])
        self.assertTrue(os.path.isfile(out))
        self.assertGreater(os.path.getsize(out), 0)

    def test_classification_report_written_to_tmpdir(self):
        src = self._write_json(SYNTHETIC_CLASSIFICATION, "classifications.json")
        out = self._out("classification_report.html")
        classification_main(["--input", src, "--output", out])
        self.assertTrue(os.path.isfile(out))
        self.assertGreater(os.path.getsize(out), 0)

    def test_action_plan_report_written_to_tmpdir(self):
        src = self._write_json(SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out = self._out("action_plan_report.html")
        action_plan_main(["--input", src, "--output", out])
        self.assertTrue(os.path.isfile(out))
        self.assertGreater(os.path.getsize(out), 0)


# ── ARCH-0097: inventory report HTML validity and lang="it" ───────────────────

class TestInventoryReportContent(TmpDirMixin):

    def setUp(self):
        super().setUp()
        src = self._write_json(SYNTHETIC_INVENTORY, "inventory.json")
        out = self._out("inventory_report.html")
        inventory_main(["--input", src, "--output", out])
        self._html = self._read_html(out)
        self._path = out

    def test_lang_it_present(self):
        self.assertIn('lang="it"', self._html)

    def test_doctype_present(self):
        self.assertIn("<!DOCTYPE html>", self._html)

    def test_body_present(self):
        self.assertIn("<body>", self._html)
        self.assertIn("</body>", self._html)

    def test_italian_heading_present(self):
        self.assertIn("Report Inventario", self._html)

    def test_synthetic_source_present(self):
        self.assertIn("Synthetic_Test", self._html)

    def test_validate_reports_passes(self):
        code = vr.main([self._path])
        self.assertEqual(code, 0)


# ── ARCH-0098: classification report HTML validity and lang="it" ──────────────

class TestClassificationReportContent(TmpDirMixin):

    def setUp(self):
        super().setUp()
        src = self._write_json(SYNTHETIC_CLASSIFICATION, "classifications.json")
        out = self._out("classification_report.html")
        classification_main(["--input", src, "--output", out])
        self._html = self._read_html(out)
        self._path = out

    def test_lang_it_present(self):
        self.assertIn('lang="it"', self._html)

    def test_doctype_present(self):
        self.assertIn("<!DOCTYPE html>", self._html)

    def test_body_present(self):
        self.assertIn("<body>", self._html)
        self.assertIn("</body>", self._html)

    def test_italian_heading_present(self):
        self.assertIn("Report Classificazione", self._html)

    def test_dry_run_notice_present(self):
        self.assertIn("Solo dry-run", self._html)

    def test_validate_reports_passes(self):
        code = vr.main([self._path])
        self.assertEqual(code, 0)


# ── ARCH-0099: action plan review-only wording, no destructive phrasing ───────

class TestActionPlanReportContent(TmpDirMixin):

    def setUp(self):
        super().setUp()
        src = self._write_json(SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out = self._out("action_plan_report.html")
        action_plan_main(["--input", src, "--output", out])
        self._html = self._read_html(out)
        self._path = out

    def test_lang_it_present(self):
        self.assertIn('lang="it"', self._html)

    def test_review_only_wording_present(self):
        self.assertIn("Solo revisione", self._html)

    def test_no_destructive_delete_instruction(self):
        html_lower = self._html.lower()
        self.assertNotIn("cancellazione automatica", html_lower)
        self.assertNotIn("safe to delete", html_lower)
        self.assertNotIn("delete automatically", html_lower)

    def test_no_move_instruction(self):
        self.assertNotIn("sposta automaticamente", self._html.lower())

    def test_reclaimable_is_theoretical(self):
        self.assertIn("teorico", self._html.lower())

    def test_validate_reports_passes(self):
        code = vr.main([self._path])
        self.assertEqual(code, 0)


# ── ARCH-0100: validate_reports on all three temp-generated reports ───────────

class TestValidateReportsOnGenerated(TmpDirMixin):

    def test_all_three_reports_pass_validation(self):
        inv_src = self._write_json(SYNTHETIC_INVENTORY, "inventory.json")
        cls_src = self._write_json(SYNTHETIC_CLASSIFICATION, "classifications.json")
        act_src = self._write_json(SYNTHETIC_ACTION_PLAN, "proposed_actions.json")

        inv_out = self._out("inventory_report.html")
        cls_out = self._out("classification_report.html")
        act_out = self._out("action_plan_report.html")

        inventory_main(["--input", inv_src, "--output", inv_out])
        classification_main(["--input", cls_src, "--output", cls_out])
        action_plan_main(["--input", act_src, "--output", act_out])

        code = vr.main([inv_out, cls_out, act_out])
        self.assertEqual(code, 0)

    def test_validate_tmpdir_containing_all_three(self):
        inv_src = self._write_json(SYNTHETIC_INVENTORY, "inventory.json")
        cls_src = self._write_json(SYNTHETIC_CLASSIFICATION, "classifications.json")
        act_src = self._write_json(SYNTHETIC_ACTION_PLAN, "proposed_actions.json")

        inventory_main(["--input", inv_src, "--output", self._out("inventory_report.html")])
        classification_main(["--input", cls_src, "--output", self._out("classification_report.html")])
        action_plan_main(["--input", act_src, "--output", self._out("action_plan_report.html")])

        code = vr.main([self._tmpdir])
        self.assertEqual(code, 0)


# ── ARCH-0101: no dependency on reports/ or personal files ────────────────────

class TestNoPersonalFileDependency(TmpDirMixin):

    def test_inventory_runs_without_reports_dir(self):
        reports_dir = Path(__file__).parent.parent / "reports"
        src = self._write_json(SYNTHETIC_INVENTORY, "inventory.json")
        out = self._out("inventory_report.html")
        inventory_main(["--input", src, "--output", out])
        # Output must be in tmpdir, not in reports/
        self.assertFalse(str(out).startswith(str(reports_dir)))
        self.assertTrue(os.path.isfile(out))

    def test_classification_runs_without_reports_dir(self):
        reports_dir = Path(__file__).parent.parent / "reports"
        src = self._write_json(SYNTHETIC_CLASSIFICATION, "classifications.json")
        out = self._out("classification_report.html")
        classification_main(["--input", src, "--output", out])
        self.assertFalse(str(out).startswith(str(reports_dir)))
        self.assertTrue(os.path.isfile(out))

    def test_action_plan_runs_without_reports_dir(self):
        reports_dir = Path(__file__).parent.parent / "reports"
        src = self._write_json(SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out = self._out("action_plan_report.html")
        action_plan_main(["--input", src, "--output", out])
        self.assertFalse(str(out).startswith(str(reports_dir)))
        self.assertTrue(os.path.isfile(out))


# ── ARCH-0102: missing input error handling ───────────────────────────────────

class TestMissingInputHandling(TmpDirMixin):

    def _exits_nonzero(self, runner, nonexistent_path, out_path):
        try:
            runner(["--input", nonexistent_path, "--output", out_path])
            return False
        except SystemExit as e:
            return e.code != 0

    def test_inventory_missing_input_exits_nonzero(self):
        nonexistent = os.path.join(self._tmpdir, "no_such_file.json")
        out = self._out("out.html")
        self.assertTrue(self._exits_nonzero(inventory_main, nonexistent, out))

    def test_classification_missing_input_exits_nonzero(self):
        nonexistent = os.path.join(self._tmpdir, "no_such_file.json")
        out = self._out("out.html")
        self.assertTrue(self._exits_nonzero(classification_main, nonexistent, out))

    def test_action_plan_missing_input_exits_nonzero(self):
        nonexistent = os.path.join(self._tmpdir, "no_such_file.json")
        out = self._out("out.html")
        self.assertTrue(self._exits_nonzero(action_plan_main, nonexistent, out))


if __name__ == "__main__":
    unittest.main()
