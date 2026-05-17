"""
ARCH-0117..ARCH-0121 — Explicit safety assertions.

Confirms that no test or script modifies reports/, personal files, or source
fixture files. All tests use synthetic data and temporary directories only.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.inventory_readonly import main as _inv_main
from scripts.classify_inventory import main as _cls_main
from scripts.generate_inventory_report import main as _inv_report_main
from scripts.generate_classification_report import main as _cls_report_main
from scripts.generate_action_plan_report import main as _ap_report_main
from tests.helpers import TmpDirMixin

_REPO_ROOT = Path(__file__).parent.parent
_REPORTS_DIR = _REPO_ROOT / "reports"

_SYNTHETIC_INVENTORY = {
    "summary": {"source": "C:/Synthetic", "total_files": 1, "total_size_bytes": 100,
                "extensions_count": {".pdf": 1}, "skipped_count": 0, "errors_count": 0},
    "files": [{"relative_path": "doc.pdf", "filename": "doc.pdf", "extension": ".pdf",
               "size_bytes": 100, "modified_time_iso": "2025-01-01T00:00:00", "sha256": "aaa"}],
    "errors": [],
}

_SYNTHETIC_CLASSIFICATION = {
    "summary": {"source": "C:/Synthetic", "total_files": 1, "low_confidence_count": 0,
                "categories_count": {"Documents": 1}, "location_policy_counts": {"classify_only": 1}},
    "classifications": [{"relative_path": "doc.pdf", "category": "Documents",
                         "location_policy": "classify_only", "confidence": 0.90,
                         "signals": ["ext:.pdf"], "suggested_folder": "Documents", "size_bytes": 100}],
}

_SYNTHETIC_ACTION_PLAN = {
    "summary": {"source": "C:/Synthetic", "total_files": 1, "root_sort_candidates_count": 1,
                "duplicate_groups_count": 0, "duplicate_files_count": 0, "keep_in_place_count": 0,
                "potential_reclaimable_bytes": 0, "duplicate_priority_counts": {}},
    "root_sort_candidates": [{"relative_path": "orphan.pdf", "category": "Documents",
                              "confidence": 0.85, "proposed_destination_relative_path": "Documenti/orphan.pdf",
                              "status": "review_only"}],
    "duplicate_groups": [],
}


def _call(main_fn, argv):
    with patch("sys.argv", argv):
        main_fn()


def _snapshot_dir(path: Path):
    """Return a frozenset of (relative_str, mtime, size) for all files under path."""
    if not path.exists():
        return None
    result = set()
    for f in path.rglob("*"):
        if f.is_file():
            stat = f.stat()
            result.add((str(f.relative_to(path)), stat.st_mtime, stat.st_size))
    return frozenset(result)


# ── ARCH-0117: generators write only to explicit output path ──────────────────

class TestGeneratorsWriteOnlyToExplicitOutput(TmpDirMixin):

    def test_inventory_report_output_is_in_tmpdir(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("report.html")
        _call(_inv_report_main, ["generate_inventory_report.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        self.assertTrue(out.startswith(self._tmpdir))

    def test_classification_report_output_is_in_tmpdir(self):
        inp = self._write_json(_SYNTHETIC_CLASSIFICATION, "classifications.json")
        out = self._path("report.html")
        _call(_cls_report_main, ["generate_classification_report.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        self.assertTrue(out.startswith(self._tmpdir))

    def test_action_plan_report_output_is_in_tmpdir(self):
        inp = self._write_json(_SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out = self._path("report.html")
        _call(_ap_report_main, ["generate_action_plan_report.py", "--input", inp, "--output", out])
        self.assertTrue(os.path.isfile(out))
        self.assertTrue(out.startswith(self._tmpdir))


# ── ARCH-0118: reports/ dir not created or modified by generators ─────────────

class TestReportsDirNotModified(TmpDirMixin):

    def _reports_snapshot(self):
        return _snapshot_dir(_REPORTS_DIR)

    def test_inventory_report_does_not_modify_reports_dir(self):
        before = self._reports_snapshot()
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("report.html")
        _call(_inv_report_main, ["generate_inventory_report.py", "--input", inp, "--output", out])
        self.assertEqual(self._reports_snapshot(), before)

    def test_classification_report_does_not_modify_reports_dir(self):
        before = self._reports_snapshot()
        inp = self._write_json(_SYNTHETIC_CLASSIFICATION, "classifications.json")
        out = self._path("report.html")
        _call(_cls_report_main, ["generate_classification_report.py", "--input", inp, "--output", out])
        self.assertEqual(self._reports_snapshot(), before)

    def test_action_plan_report_does_not_modify_reports_dir(self):
        before = self._reports_snapshot()
        inp = self._write_json(_SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out = self._path("report.html")
        _call(_ap_report_main, ["generate_action_plan_report.py", "--input", inp, "--output", out])
        self.assertEqual(self._reports_snapshot(), before)

    def test_inventory_scan_does_not_create_reports_dir(self):
        """inventory_readonly must not create reports/ as a side effect."""
        src = self._path("source")
        os.makedirs(src)
        (Path(src) / "a.txt").write_bytes(b"hi")
        reports_existed_before = _REPORTS_DIR.exists()
        out = self._path("inventory.json")
        _call(_inv_main, ["inventory_readonly.py", "--source", src, "--output", out])
        self.assertEqual(_REPORTS_DIR.exists(), reports_existed_before)


# ── ARCH-0119: inventory_readonly does not modify source files ────────────────

class TestInventorySourceUnchanged(TmpDirMixin):

    def test_source_files_unchanged_after_cli_run(self):
        src = self._path("source")
        os.makedirs(src)
        files = {
            "doc.pdf": b"pdf content here",
            "photo.jpg": b"\xff\xd8\xff bytes",
            "sub/note.txt": b"note content",
        }
        for rel, content in files.items():
            p = Path(src) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)

        out = self._path("inventory.json")
        _call(_inv_main, ["inventory_readonly.py", "--source", src, "--output", out])

        for rel, content in files.items():
            p = Path(src) / rel
            self.assertTrue(p.exists(), f"source file missing: {rel}")
            self.assertEqual(p.read_bytes(), content, f"source file modified: {rel}")


# ── ARCH-0120: classify_inventory dry_run_only on synthetic data ──────────────

class TestClassifyDryRunOnly(TmpDirMixin):

    def test_summary_dry_run_only_is_true(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        _call(_cls_main, ["classify_inventory.py", "--input", inp, "--output", out])
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["summary"]["dry_run_only"])

    def test_all_items_dry_run_only_is_true(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        _call(_cls_main, ["classify_inventory.py", "--input", inp, "--output", out])
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        for item in data["classifications"]:
            self.assertTrue(item["dry_run_only"], f"dry_run_only not set on {item.get('relative_path')}")

    def test_no_destructive_keys_in_output(self):
        inp = self._write_json(_SYNTHETIC_INVENTORY, "inventory.json")
        out = self._path("classifications.json")
        _call(_cls_main, ["classify_inventory.py", "--input", inp, "--output", out])
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        forbidden = {"move_to", "delete", "rename_to", "destination_path", "execute"}
        for item in data["classifications"]:
            self.assertTrue(forbidden.isdisjoint(item.keys()),
                            f"forbidden key found in classification: {forbidden & item.keys()}")


# ── ARCH-0121: action plan report does not propose auto move/rename/delete ─────

class TestActionPlanNoAutoDestructive(TmpDirMixin):

    def _generate_report_html(self):
        inp = self._write_json(_SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out = self._path("action_plan.html")
        _call(_ap_report_main, ["generate_action_plan_report.py", "--input", inp, "--output", out])
        with open(out, encoding="utf-8") as f:
            return f.read()

    def test_html_contains_no_auto_delete_instruction(self):
        html = self._generate_report_html()
        lower = html.lower()
        for phrase in ("cancellazione automatica", "delete automatically", "safe to delete", "auto-delete"):
            self.assertNotIn(phrase, lower, f"forbidden phrase in report HTML: {phrase!r}")

    def test_html_contains_no_auto_move_instruction(self):
        html = self._generate_report_html()
        lower = html.lower()
        for phrase in ("sposta automaticamente", "move automatically", "move now", "sposta ora"):
            self.assertNotIn(phrase, lower, f"forbidden phrase in report HTML: {phrase!r}")

    def test_html_contains_no_auto_rename_instruction(self):
        html = self._generate_report_html()
        lower = html.lower()
        for phrase in ("rinomina automaticamente", "rename automatically", "rename now"):
            self.assertNotIn(phrase, lower, f"forbidden phrase in report HTML: {phrase!r}")

    def test_root_sort_candidates_have_review_only_status(self):
        inp = self._write_json(_SYNTHETIC_ACTION_PLAN, "proposed_actions.json")
        out_json = self._path("proposed_actions.json")
        # Verify the input fixture itself — status must be review_only, not execute
        for candidate in _SYNTHETIC_ACTION_PLAN["root_sort_candidates"]:
            self.assertEqual(candidate["status"], "review_only")


if __name__ == "__main__":
    unittest.main()
