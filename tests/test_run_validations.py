"""
ARCH-0140..ARCH-0141 — Tests for scripts/run_validations.py.

All tests use mocking — no real subprocesses, no reports/, no personal files.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.run_validations as rv


def _make_result(returncode=0, stdout="", stderr=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


# ── ARCH-0140: runner behaviour under mocked subprocess ───────────────────────

class TestRunnerAllPass(unittest.TestCase):

    def test_returns_zero_when_all_steps_succeed(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            rc = rv.main([])
        self.assertEqual(rc, 0)

    def test_quick_mode_returns_zero(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            rc = rv.main(["--quick"])
        self.assertEqual(rc, 0)

    def test_quick_mode_skips_unittest(self):
        calls = []
        def _fake_run(argv, **kwargs):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake_run):
            rv.main(["--quick"])
        # None of the argv lists should contain "unittest"
        for argv in calls:
            self.assertNotIn("unittest", argv)

    def test_full_mode_runs_unittest(self):
        calls = []
        def _fake_run(argv, **kwargs):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake_run):
            rv.main([])
        found = any("unittest" in argv for argv in calls)
        self.assertTrue(found, "unittest discover must be called in full mode")

    def test_full_mode_runs_py_compile(self):
        calls = []
        def _fake_run(argv, **kwargs):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake_run):
            rv.main([])
        found = any("py_compile" in argv for argv in calls)
        self.assertTrue(found, "py_compile must be called in full mode")

    def test_validate_reports_help_called_in_quick_mode(self):
        calls = []
        def _fake_run(argv, **kwargs):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake_run):
            rv.main(["--quick"])
        found = any("validate_reports.py" in str(argv) for argv in calls)
        self.assertTrue(found, "validate_reports --help must run in quick mode")


# ── ARCH-0141: runner fails when a step returns non-zero ──────────────────────

class TestRunnerFailure(unittest.TestCase):

    def test_returns_one_when_first_step_fails(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(1)):
            rc = rv.main([])
        self.assertEqual(rc, 1)

    def test_returns_one_when_any_step_fails(self):
        results = [_make_result(0), _make_result(2), _make_result(0)]
        with patch("scripts.run_validations.subprocess.run", side_effect=results):
            rc = rv.main([])
        self.assertEqual(rc, 1)

    def test_continues_after_one_failure(self):
        """Runner must not abort early — it runs all steps and reports all failures."""
        call_count = [0]
        def _fake_run(argv, **kwargs):
            call_count[0] += 1
            return _make_result(1)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake_run):
            rv.main([])
        # Full mode has 3 steps; all must be attempted even if first fails
        self.assertEqual(call_count[0], 3)

    def test_quick_mode_returns_one_on_failure(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(1)):
            rc = rv.main(["--quick"])
        self.assertEqual(rc, 1)

    def test_quick_mode_continues_after_failure(self):
        call_count = [0]
        def _fake_run(argv, **kwargs):
            call_count[0] += 1
            return _make_result(1)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake_run):
            rv.main(["--quick"])
        # Quick mode has 2 steps (py_compile + validate_reports)
        self.assertEqual(call_count[0], 2)


# ── safety: runner must not reference reports/ paths ─────────────────────────

class TestRunnerSafety(unittest.TestCase):

    def test_no_step_targets_reports_dir(self):
        for label, argv, _ in rv._STEPS:
            for part in argv:
                self.assertNotIn("reports/", str(part),
                                 f"Step '{label}' references reports/ dir: {argv}")
                self.assertNotIn("reports\\", str(part),
                                 f"Step '{label}' references reports\\ dir: {argv}")

    def test_compile_targets_are_under_scripts(self):
        for target in rv._COMPILE_TARGETS:
            self.assertTrue(
                str(target).startswith("scripts/"),
                f"compile target outside scripts/: {target}"
            )


if __name__ == "__main__":
    unittest.main()
