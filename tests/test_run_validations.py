"""
ARCH-0140..ARCH-0141, ARCH-0148..ARCH-0158 — Tests for scripts/run_validations.py.

All tests use mocking — no real subprocesses, no reports/, no personal files.
"""

import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.run_validations as rv


def _make_result(returncode=0, stdout="", stderr=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


# ── ARCH-0140: runner behaviour — all pass ────────────────────────────────────

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
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        for argv in calls:
            self.assertNotIn("unittest", argv)

    def test_full_mode_runs_unittest(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main([])
        self.assertTrue(any("unittest" in a for a in calls))

    def test_full_mode_runs_py_compile(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main([])
        self.assertTrue(any("py_compile" in a for a in calls))

    def test_validate_reports_help_called_in_quick_mode(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        self.assertTrue(any("validate_reports.py" in str(a) for a in calls))


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
        """Runner must not abort early — all steps are attempted."""
        count = [0]
        def _fake(argv, **kw):
            count[0] += 1
            return _make_result(1)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main([])
        self.assertEqual(count[0], 3)

    def test_quick_mode_returns_one_on_failure(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(1)):
            rc = rv.main(["--quick"])
        self.assertEqual(rc, 1)

    def test_quick_mode_continues_after_failure(self):
        count = [0]
        def _fake(argv, **kw):
            count[0] += 1
            return _make_result(1)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        self.assertEqual(count[0], 2)


# ── ARCH-0148: --list exits 0 without running subprocess ─────────────────────

class TestListMode(unittest.TestCase):

    def test_list_returns_zero(self):
        with patch("scripts.run_validations.subprocess.run") as mock_run:
            rc = rv.main(["--list"])
        self.assertEqual(rc, 0)
        mock_run.assert_not_called()

    def test_list_mentions_all_step_labels(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rv.main(["--list"])
        output = buf.getvalue()
        for label, _, _ in rv._STEPS:
            self.assertIn(label, output)

    def test_list_shows_quick_full_modes(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rv.main(["--list"])
        output = buf.getvalue()
        self.assertIn("quick+full", output)
        self.assertIn("full only", output)


# ── ARCH-0150: quick mode step coverage ──────────────────────────────────────

class TestQuickModeCoverage(unittest.TestCase):

    def test_quick_runs_py_compile(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        self.assertTrue(any("py_compile" in a for a in calls),
                        "py_compile must run in quick mode")

    def test_quick_runs_validate_reports(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        self.assertTrue(any("validate_reports.py" in str(a) for a in calls),
                        "validate_reports --help must run in quick mode")

    def test_quick_skips_only_full_only_steps(self):
        skipped_labels = [l for l, _, s in rv._STEPS if s]
        essential_labels = [l for l, _, s in rv._STEPS if not s]
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        flat_calls = [str(a) for argv in calls for a in argv]
        for label in skipped_labels:
            # "unittest" is the skip_in_quick step; its argv contains "unittest"
            if label == "unittest discover":
                self.assertNotIn("unittest", flat_calls)
        for label in essential_labels:
            if label == "py_compile":
                self.assertTrue(any("py_compile" in c for c in flat_calls))


# ── ARCH-0152: missing compile targets handled clearly ───────────────────────

class TestMissingCompileTargets(unittest.TestCase):

    def test_missing_target_causes_failure(self):
        with patch.object(rv, "_COMPILE_TARGETS", ["scripts/no_such_file.py"]):
            with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
                rc = rv.main([])
        self.assertEqual(rc, 1)

    def test_missing_target_message_mentions_filename(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch.object(rv, "_COMPILE_TARGETS", ["scripts/no_such_file.py"]):
            with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
                with redirect_stdout(buf):
                    rv.main([])
        self.assertIn("no_such_file.py", buf.getvalue())

    def test_other_steps_still_run_when_compile_target_missing(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch.object(rv, "_COMPILE_TARGETS", ["scripts/no_such_file.py"]):
            with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
                rv.main([])
        # validate_reports --help must still run
        self.assertTrue(any("validate_reports.py" in str(a) for a in calls))

    def test_check_compile_targets_returns_missing(self):
        with patch.object(rv, "_COMPILE_TARGETS", ["scripts/no_such_file.py"]):
            missing = rv._check_compile_targets()
        self.assertIn("scripts/no_such_file.py", missing)

    def test_check_compile_targets_empty_when_all_exist(self):
        missing = rv._check_compile_targets()
        self.assertEqual(missing, [])


# ── ARCH-0154: sys.executable used in all subprocess commands ────────────────

class TestSysExecutable(unittest.TestCase):

    def test_all_steps_use_sys_executable(self):
        for label, argv, _ in rv._STEPS:
            self.assertEqual(argv[0], sys.executable,
                             f"Step '{label}' does not start with sys.executable")


# ── ARCH-0156: subprocess calls use cwd set to repo root ─────────────────────

class TestCwdIsRepoRoot(unittest.TestCase):

    def test_subprocess_called_with_repo_cwd(self):
        captured_kwargs = []
        def _fake(argv, **kw):
            captured_kwargs.append(kw)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        for kw in captured_kwargs:
            self.assertEqual(kw.get("cwd"), str(rv._REPO),
                             "subprocess.run must use cwd=_REPO")


# ── ARCH-0157: runner source has no network/cloud/API references ──────────────

class TestRunnerSourceInvariants(unittest.TestCase):

    def setUp(self):
        self._src = inspect.getsource(rv)

    def test_no_network_imports(self):
        for mod in ("urllib", "http.client", "socket", "requests", "httpx"):
            self.assertNotIn(f"import {mod}", self._src,
                             f"runner must not import network module: {mod}")

    def test_no_cloud_api_keywords(self):
        src_lower = self._src.lower()
        for kw in ("api_key", "access_token", "cloud", "s3", "gcs", "azure"):
            self.assertNotIn(kw, src_lower,
                             f"runner must not reference cloud/API keyword: {kw}")

    # ── ARCH-0158: no report-opening commands ─────────────────────────────────

    def test_no_invoke_item(self):
        self.assertNotIn("Invoke-Item", self._src)

    def test_no_start_command(self):
        import re
        self.assertNotRegex(self._src, r"\bstart\b.*\.html")

    def test_no_webbrowser(self):
        self.assertNotIn("webbrowser", self._src)


# ── existing safety invariants (unchanged) ────────────────────────────────────

class TestRunnerSafety(unittest.TestCase):

    def test_no_step_targets_reports_dir(self):
        for label, argv, _ in rv._STEPS:
            for part in argv:
                self.assertNotIn("reports/", str(part),
                                 f"Step '{label}' references reports/")
                self.assertNotIn("reports\\", str(part),
                                 f"Step '{label}' references reports\\")

    def test_compile_targets_are_under_scripts(self):
        for target in rv._COMPILE_TARGETS:
            self.assertTrue(str(target).startswith("scripts/"),
                            f"compile target outside scripts/: {target}")


if __name__ == "__main__":
    unittest.main()
