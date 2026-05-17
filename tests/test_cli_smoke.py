"""
ARCH-0107..ARCH-0111 — CLI smoke tests for main entry points.

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

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.inventory_readonly import main as _inv_main
from scripts.classify_inventory import main as _cls_main
from scripts.generate_inventory_report import main as _inv_report_main
from scripts.generate_classification_report import main as _cls_report_main
from scripts.generate_action_plan_report import main as _ap_report_main


# ── helpers ────────────────────────────────────────────────────────────────────

def _call(main_fn, argv):
    with patch("sys.argv", argv):
        main_fn()


class _TmpMixin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="cli_smoke_")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _path(self, name):
        return os.path.join(self._tmp, name)

    def _write_json(self, data, name):
        p = self._path(name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return p


# ── ARCH-0107: inventory_readonly CLI smoke ────────────────────────────────────

class TestInventoryReadonlyCLI(_TmpMixin):
    """Smoke test for inventory_readonly.main() using a synthetic source dir."""

    def _make_source(self):
        src = self._path("source")
        os.makedirs(src)
        (Path(src) / "note.txt").write_bytes(b"hello")
        (Path(src) / "doc.pdf").write_bytes(b"pdf content")
        sub = Path(src) / "subfolder"
        sub.mkdir()
        (sub / "image.jpg").write_bytes(b"jpg")
        return src

    def test_cli_produces_json_output(self):
        src = self._make_source()
        out = self._path("inventory.json")
        _call(_inv_main, ["inventory_readonly.py", "--source", src, "--output", out])
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("summary", data)
        self.assertIn("files", data)
        self.assertEqual(data["summary"]["total_files"], 3)

    def test_cli_missing_source_exits_nonzero(self):
        out = self._path("inventory.json")
        with self.assertRaises(SystemExit) as ctx:
            _call(_inv_main, ["inventory_readonly.py", "--source", self._path("no_such_dir"), "--output", out])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_cli_output_not_in_reports_dir(self):
        src = self._make_source()
        out = self._path("inventory.json")
        _call(_inv_main, ["inventory_readonly.py", "--source", src, "--output", out])
        reports_dir = str(Path(__file__).parent.parent / "reports")
        self.assertFalse(out.startswith(reports_dir))

    def test_cli_source_files_unchanged(self):
        src = self._make_source()
        note = Path(src) / "note.txt"
        content_before = note.read_bytes()
        out = self._path("inventory.json")
        _call(_inv_main, ["inventory_readonly.py", "--source", src, "--output", out])
        self.assertEqual(note.read_bytes(), content_before)


# ── ARCH-0108: classify_inventory CLI smoke ───────────────────────────────────

_SYNTHETIC_INVENTORY = {
    "summary": {"source": "C:/Synthetic", "total_files": 2, "total_size_bytes": 200,
                "extensions_count": {".pdf": 1, ".jpg": 1}, "skipped_count": 0, "errors_count": 0},
    "files": [
        {"relative_path": "doc.pdf", "filename": "doc.pdf", "extension": ".pdf", "size_bytes": 100,
         "modified_time_iso": "2025-01-01T00:00:00", "sha256": "aaa"},
        {"relative_path": "subfolder/photo.jpg", "filename": "photo.jpg", "extension": ".jpg",
         "size_bytes": 100, "modified_time_iso": "2025-01-02T00:00:00", "sha256": "bbb"},
    ],
    "errors": [],
}


class TestClassifyInventoryCLI(_TmpMixin):
    """Smoke test for classify_inventory.main() using synthetic inventory JSON."""

    def test_cli_produces_classifications_json(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        _call(_cls_main, ["classify_inventory.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("summary", data)
        self.assertIn("classifications", data)
        self.assertEqual(len(data["classifications"]), 2)

    def test_cli_dry_run_only_flag(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        _call(_cls_main, ["classify_inventory.py", "--input", inp, "--output", out])
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["summary"]["dry_run_only"])
        for item in data["classifications"]:
            self.assertTrue(item["dry_run_only"])

    def test_cli_context_bound_preserved(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        _call(_cls_main, ["classify_inventory.py", "--input", inp, "--output", out])
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        by_path = {c["relative_path"]: c for c in data["classifications"]}
        self.assertEqual(by_path["doc.pdf"]["location_policy"], "classify_only")
        self.assertEqual(by_path["subfolder/photo.jpg"]["location_policy"], "keep_in_place")

    def test_cli_missing_input_exits_nonzero(self):
        out = self._path("out.json")
        with self.assertRaises(SystemExit) as ctx:
            _call(_cls_main, ["classify_inventory.py", "--input", self._path("no_such.json"), "--output", out])
        self.assertNotEqual(ctx.exception.code, 0)


# ── ARCH-0109: generate_inventory_report CLI smoke ────────────────────────────

_SYNTHETIC_INV_REPORT = {
    "summary": {"source": "C:/Synthetic", "total_files": 1, "total_size_bytes": 100,
                "extensions_count": {".txt": 1}, "skipped_count": 0, "errors_count": 0},
    "files": [{"relative_path": "a.txt", "filename": "a.txt", "extension": ".txt",
               "size_bytes": 100, "modified_time_iso": "2025-01-01T00:00:00", "sha256": "ccc"}],
    "errors": [],
}


class TestGenerateInventoryReportCLI(_TmpMixin):
    def test_cli_produces_html(self):
        inp = self._write_json(_SYNTHETIC_INV_REPORT, "inventory.json")
        out = self._path("report.html")
        _call(_inv_report_main, ["generate_inventory_report.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn('lang="it"', content)


# ── ARCH-0110: generate_classification_report CLI smoke ───────────────────────

_SYNTHETIC_CLS_REPORT = {
    "summary": {"source": "C:/Synthetic", "total_files": 1, "low_confidence_count": 0,
                "categories_count": {"Documents": 1}, "location_policy_counts": {"classify_only": 1}},
    "classifications": [{"relative_path": "a.pdf", "category": "Documents", "location_policy": "classify_only",
                         "confidence": 0.90, "signals": ["extension:.pdf"], "suggested_folder": "Documents",
                         "size_bytes": 100}],
}


class TestGenerateClassificationReportCLI(_TmpMixin):
    def test_cli_produces_html(self):
        inp = self._write_json(_SYNTHETIC_CLS_REPORT, "classifications.json")
        out = self._path("report.html")
        _call(_cls_report_main, ["generate_classification_report.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn('lang="it"', content)


# ── ARCH-0111: generate_action_plan_report CLI smoke ─────────────────────────

_SYNTHETIC_AP_REPORT = {
    "summary": {"source": "C:/Synthetic", "total_files": 2, "root_sort_candidates_count": 1,
                "duplicate_groups_count": 0, "duplicate_files_count": 0, "keep_in_place_count": 1,
                "potential_reclaimable_bytes": 0, "duplicate_priority_counts": {}},
    "root_sort_candidates": [
        {"relative_path": "orphan.txt", "category": "Text", "confidence": 0.75,
         "proposed_destination_relative_path": "Testi/orphan.txt", "status": "review_only"}
    ],
    "duplicate_groups": [],
}


class TestGenerateActionPlanReportCLI(_TmpMixin):
    def test_cli_produces_html(self):
        inp = self._write_json(_SYNTHETIC_AP_REPORT, "proposed_actions.json")
        out = self._path("report.html")
        _call(_ap_report_main, ["generate_action_plan_report.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        with open(out, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn('lang="it"', content)


if __name__ == "__main__":
    unittest.main()
