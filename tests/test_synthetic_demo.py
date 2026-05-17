"""
ARCH-0218..ARCH-0221 — Tests for scripts/run_synthetic_demo.py.

Verifies that the synthetic demo:
- produces the expected output files in a temp dir;
- never writes to reports/;
- exits 0 on a clean run;
- exits non-zero when a pipeline step fails.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.run_synthetic_demo as demo

_REPO_ROOT = Path(__file__).parent.parent
_REPORTS_DIR = _REPO_ROOT / "reports"


class TestSyntheticDemoOutputs(unittest.TestCase):
    """ARCH-0220: demo produces inventory JSON, classification JSON, and HTML reports."""

    def test_demo_exits_zero(self):
        code = demo.main([])
        self.assertEqual(code, 0)

    def test_demo_produces_inventory_json(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertTrue((tmpdir / "inventory.json").is_file())

    def test_demo_produces_classifications_json(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertTrue((tmpdir / "classifications.json").is_file())

    def test_demo_produces_proposed_actions_json(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertTrue((tmpdir / "proposed_actions.json").is_file())

    def test_demo_produces_inventory_html(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertTrue((tmpdir / "inventory_report.html").is_file())

    def test_demo_produces_classification_html(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertTrue((tmpdir / "classification_report.html").is_file())

    def test_demo_produces_action_plan_html(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertTrue((tmpdir / "action_plan_report.html").is_file())


class TestSyntheticDemoNoReportsDir(unittest.TestCase):
    """ARCH-0219: demo does not write to reports/."""

    def _snapshot(self):
        if not _REPORTS_DIR.exists():
            return None
        result = set()
        for f in _REPORTS_DIR.rglob("*"):
            if f.is_file():
                stat = f.stat()
                result.add((str(f.relative_to(_REPORTS_DIR)), stat.st_mtime, stat.st_size))
        return frozenset(result)

    def test_demo_does_not_modify_reports_dir(self):
        before = self._snapshot()
        demo.main([])
        self.assertEqual(self._snapshot(), before)


class TestSyntheticDemoFailure(unittest.TestCase):
    """ARCH-0221: demo exits non-zero when a pipeline step fails."""

    def test_demo_nonzero_when_step_fails(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            # Provide a source dir that doesn't exist so inventory_readonly fails
            original_make = demo._make_synthetic_source

            def _bad_source(base):
                bad = base / "no_such_source"
                # Don't create it — inventory_readonly will fail
                return bad

            with patch.object(demo, "_make_synthetic_source", _bad_source):
                code = demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
