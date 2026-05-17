"""Unit tests for scripts/validate_reports.py using temporary files only."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.validate_reports import check_file, main, ACTION_PLAN_MARKERS


MINIMAL_ACTION_PLAN = """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Piano Azioni</title></head>
<body>
<script id="dup-data" type="application/json">[]</script>
<script>var data = JSON.parse(document.getElementById('dup-data').textContent);</script>
<tbody id="dup-tbody"></tbody>
<button id="btn-reset-filters">Reset</button>
<div id="dup-empty-state"></div>
<p>Solo revisione — Nessuna cancellazione automatica. Impatto teorico stimato.</p>
</body>
</html>"""


class TestValidateReports(unittest.TestCase):

    def _write_tmp(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8", delete=False)
        f.write(content)
        f.close()
        return f.name

    def tearDown(self):
        pass  # temp files cleaned per test

    def test_valid_action_plan_passes(self):
        path = self._write_tmp(MINIMAL_ACTION_PLAN)
        try:
            result = check_file("action_plan_report", path, ACTION_PLAN_MARKERS)
            self.assertTrue(result)
        finally:
            os.unlink(path)

    def test_missing_dup_data_marker_fails(self):
        broken = MINIMAL_ACTION_PLAN.replace('id="dup-data"', 'id="other"')
        path = self._write_tmp(broken)
        try:
            result = check_file("action_plan_report", path, ACTION_PLAN_MARKERS)
            self.assertFalse(result)
        finally:
            os.unlink(path)

    def test_missing_italian_wording_fails(self):
        broken = MINIMAL_ACTION_PLAN.replace("Solo revisione", "Review only")
        path = self._write_tmp(broken)
        try:
            result = check_file("action_plan_report", path, ACTION_PLAN_MARKERS)
            self.assertFalse(result)
        finally:
            os.unlink(path)

    def test_missing_optional_report_is_skipped(self):
        result = check_file("inventory_report", "/nonexistent/path/report.html", ['<html lang="it">'])
        self.assertTrue(result)  # missing optional report is not a failure

    def test_main_with_nonexistent_paths_returns_zero(self):
        # all three paths missing — all skipped — passes
        code = main(["/no/inv.html", "/no/cls.html", "/no/act.html"])
        self.assertEqual(code, 0)

    def test_main_with_valid_action_plan(self):
        path = self._write_tmp(MINIMAL_ACTION_PLAN)
        try:
            code = main(["/no/inv.html", "/no/cls.html", path])
            self.assertEqual(code, 0)
        finally:
            os.unlink(path)

    def test_main_with_broken_action_plan(self):
        broken = MINIMAL_ACTION_PLAN.replace('id="dup-tbody"', 'id="other"')
        path = self._write_tmp(broken)
        try:
            code = main(["/no/inv.html", "/no/cls.html", path])
            self.assertEqual(code, 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
