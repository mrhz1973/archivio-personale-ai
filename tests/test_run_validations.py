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
        # One result per step in _STEPS; second one fails
        results = [_make_result(0 if i != 1 else 2) for i in range(len(rv._STEPS))]
        with patch("scripts.run_validations.subprocess.run", side_effect=results):
            rc = rv.main([])
        self.assertEqual(rc, 1)

    def test_continues_after_one_failure(self):
        """Runner must not abort early — all steps are attempted."""
        full_count = sum(1 for _, _, skip in rv._STEPS if not skip) + sum(1 for _, _, skip in rv._STEPS if skip)
        count = [0]
        def _fake(argv, **kw):
            count[0] += 1
            return _make_result(1)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main([])
        self.assertEqual(count[0], len(rv._STEPS))

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


# ── ARCH-0243/0244/0245: synthetic demo integration ───────────────────────────

class TestSyntheticDemoIntegration(unittest.TestCase):
    """Verify run_validations.py includes or excludes the synthetic demo correctly."""

    def test_full_mode_includes_synthetic_demo(self):
        """ARCH-0243: full mode runs the synthetic demo step."""
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main([])
        flat = [str(a) for argv in calls for a in argv]
        self.assertTrue(any("run_synthetic_demo" in c for c in flat),
                        "synthetic demo must run in full mode")

    def test_quick_mode_excludes_synthetic_demo(self):
        """ARCH-0244: quick mode skips the synthetic demo step."""
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        flat = [str(a) for argv in calls for a in argv]
        self.assertFalse(any("run_synthetic_demo" in c for c in flat),
                         "synthetic demo must not run in quick mode")

    def test_list_mentions_synthetic_demo_without_running(self):
        """ARCH-0245: --list shows synthetic demo, no subprocess."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run") as mock_run:
            with redirect_stdout(buf):
                rv.main(["--list"])
        mock_run.assert_not_called()
        self.assertIn("synthetic demo", buf.getvalue())


# ── ARCH-0306..0309: summary output ──────────────────────────────────────────

class TestSummaryOutput(unittest.TestCase):

    def _capture(self, args):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rc = rv.main(args)
        return rc, buf.getvalue()

    def test_full_mode_summary_line(self):
        """ARCH-0307: full mode prints Summary (full):"""
        rc, out = self._capture([])
        self.assertEqual(rc, 0)
        self.assertIn("Summary (full):", out)

    def test_quick_mode_summary_line(self):
        """ARCH-0308: quick mode prints Summary (quick):"""
        rc, out = self._capture(["--quick"])
        self.assertEqual(rc, 0)
        self.assertIn("Summary (quick):", out)

    def test_summary_shows_failed_count_on_failure(self):
        """ARCH-0309: failure summary shows failed count."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(1)):
            with redirect_stdout(buf):
                rc = rv.main([])
        self.assertEqual(rc, 1)
        out = buf.getvalue()
        self.assertIn("failed", out)
        self.assertIn("Failed:", out)

    def test_summary_shows_ok_count(self):
        rc, out = self._capture([])
        self.assertIn(" OK", out)

    def test_summary_shows_skipped_in_quick(self):
        rc, out = self._capture(["--quick"])
        self.assertIn("skipped", out)


# ── ARCH-0311..0312: --list correctness (already in TestListMode/TestSyntheticDemoIntegration) ──

# No new tests needed; existing tests cover ARCH-0311 and ARCH-0312.


# ── ARCH-0315: --quiet flag ───────────────────────────────────────────────────

class TestQuietFlag(unittest.TestCase):

    def _capture(self, args):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rc = rv.main(args)
        return rc, buf.getvalue()

    def test_quiet_returns_zero_on_success(self):
        rc, _ = self._capture(["--quiet"])
        self.assertEqual(rc, 0)

    def test_quiet_suppresses_run_lines(self):
        _, out = self._capture(["--quiet"])
        self.assertNotIn("[RUN]", out)

    def test_quiet_suppresses_ok_lines(self):
        _, out = self._capture(["--quiet"])
        self.assertNotIn("[OK]", out)

    def test_quiet_still_prints_summary(self):
        _, out = self._capture(["--quiet"])
        self.assertIn("Summary", out)

    def test_quiet_prints_fail_on_failure(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(1)):
            with redirect_stdout(buf):
                rc = rv.main(["--quiet"])
        self.assertEqual(rc, 1)
        self.assertIn("[FAIL]", buf.getvalue())

    def test_quiet_returns_one_on_failure(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(1)):
            rc = rv.main(["--quiet"])
        self.assertEqual(rc, 1)


# ── ARCH-0318: --no-demo flag ─────────────────────────────────────────────────

class TestNoDemoFlag(unittest.TestCase):

    def test_no_demo_skips_synthetic_demo(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--no-demo"])
        flat = [str(a) for argv in calls for a in argv]
        self.assertFalse(any("run_synthetic_demo" in c for c in flat),
                         "--no-demo must skip synthetic demo")

    def test_no_demo_runs_unittest(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--no-demo"])
        flat = [str(a) for argv in calls for a in argv]
        self.assertTrue(any("unittest" in c for c in flat),
                        "--no-demo must not skip unittest")

    def test_no_demo_runs_py_compile(self):
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--no-demo"])
        flat = [str(a) for argv in calls for a in argv]
        self.assertTrue(any("py_compile" in c for c in flat),
                        "--no-demo must not skip py_compile")

    def test_no_demo_returns_zero_when_others_pass(self):
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            rc = rv.main(["--no-demo"])
        self.assertEqual(rc, 0)

    def test_no_demo_summary_shows_skipped(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rv.main(["--no-demo"])
        self.assertIn("skipped", buf.getvalue())


# ── ARCH-0370..0372: first-run check integration ─────────────────────────────

class TestFirstRunCheckIntegration(unittest.TestCase):
    """ARCH-0370..0372: first-run check is full-only and listed correctly."""

    def test_full_mode_includes_first_run_check(self):
        """ARCH-0370: full mode runs the first-run check step."""
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main([])
        flat = [str(a) for argv in calls for a in argv]
        self.assertTrue(any("run_first_time_check" in c for c in flat),
                        "first-run check must run in full mode")

    def test_quick_mode_excludes_first_run_check(self):
        """ARCH-0371: quick mode skips the first-run check step."""
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--quick"])
        flat = [str(a) for argv in calls for a in argv]
        self.assertFalse(any("run_first_time_check" in c for c in flat),
                         "first-run check must not run in quick mode")

    def test_list_mentions_first_run_check_without_running(self):
        """ARCH-0372: --list shows first-run check, no subprocess."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run") as mock_run:
            with redirect_stdout(buf):
                rv.main(["--list"])
        mock_run.assert_not_called()
        self.assertIn("first-run check", buf.getvalue())

    def test_list_shows_first_run_check_as_full_only(self):
        """ARCH-0372: --list marks first-run check as full only."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run"):
            with redirect_stdout(buf):
                rv.main(["--list"])
        output = buf.getvalue()
        lines = [l for l in output.splitlines() if "first-run check" in l]
        self.assertTrue(lines, "first-run check not found in --list output")
        self.assertIn("full only", lines[0],
                      "first-run check should be labelled 'full only' in --list")


# ── ARCH-0388..0391: quick/no-demo skip output clarity ───────────────────────

class TestQuickSkipOutput(unittest.TestCase):
    """ARCH-0389/0390: --quick prints [SKIP] for all full-only steps."""

    def _capture_quick(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rv.main(["--quick"])
        return buf.getvalue()

    def test_quick_skip_message_first_run_check(self):
        """ARCH-0389: --quick prints [SKIP] for first-run check."""
        out = self._capture_quick()
        self.assertIn("[SKIP] first-run check", out,
                      "--quick must print [SKIP] for first-run check")

    def test_quick_skip_message_unittest(self):
        """ARCH-0390: --quick prints [SKIP] for unittest discover."""
        out = self._capture_quick()
        self.assertIn("[SKIP] unittest discover", out,
                      "--quick must print [SKIP] for unittest discover")

    def test_quick_skip_message_synthetic_demo(self):
        """ARCH-0390: --quick prints [SKIP] for synthetic demo."""
        out = self._capture_quick()
        self.assertIn("[SKIP] synthetic demo", out,
                      "--quick must print [SKIP] for synthetic demo")


class TestNoDemoFirstRunCheck(unittest.TestCase):
    """ARCH-0391: --no-demo skips only synthetic demo, not first-run check."""

    def test_no_demo_runs_first_run_check(self):
        """ARCH-0391: --no-demo must not skip first-run check."""
        calls = []
        def _fake(argv, **kw):
            calls.append(argv)
            return _make_result(0)
        with patch("scripts.run_validations.subprocess.run", side_effect=_fake):
            rv.main(["--no-demo"])
        flat = [str(a) for argv in calls for a in argv]
        self.assertTrue(any("run_first_time_check" in c for c in flat),
                        "--no-demo must not skip first-run check")

    def test_no_demo_does_not_print_skip_for_first_run_check(self):
        """ARCH-0391: --no-demo output must not show [SKIP] for first-run check."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rv.main(["--no-demo"])
        self.assertNotIn("[SKIP] first-run check", buf.getvalue(),
                         "--no-demo must not skip first-run check")


# ── ARCH-0633..0637: help safety wording and forbidden language ──────────────


def _capture_runner_help():
    """Invoke run_validations.main(['--help']) and capture stdout+stderr.

    Returns (exit_code, output). argparse calls sys.exit(0) on --help.
    """
    import io
    from contextlib import redirect_stderr, redirect_stdout
    buf = io.StringIO()
    code = 0
    try:
        with redirect_stdout(buf):
            with redirect_stderr(buf):
                rc = rv.main(["--help"])
        code = rc if rc is not None else 0
    except SystemExit as e:
        code = e.code if e.code is not None else 0
    return code, buf.getvalue()


class TestHelpExitsZero(unittest.TestCase):
    """ARCH-0633: --help must exit 0."""

    def test_help_exits_zero(self):
        code, _ = _capture_runner_help()
        self.assertEqual(code, 0)


class TestHelpSafetyWording(unittest.TestCase):
    """ARCH-0634: --help must contain the project's safety wording."""

    @classmethod
    def setUpClass(cls):
        _, cls._output = _capture_runner_help()
        cls._lower = cls._output.lower()

    def test_help_mentions_local_validations(self):
        self.assertIn("local", self._lower)
        self.assertIn("validations", self._lower)

    def test_help_mentions_no_network(self):
        self.assertIn("no network", self._lower)

    def test_help_mentions_no_report_opening(self):
        self.assertIn("no report opening", self._lower)

    def test_help_mentions_no_personal_files(self):
        self.assertIn("no personal files", self._lower)


class TestHelpNoOperativeCloudAPI(unittest.TestCase):
    """ARCH-0635: --help must not present API/cloud/n8n/MCP as operative actions."""

    @classmethod
    def setUpClass(cls):
        _, cls._output = _capture_runner_help()
        cls._lower = cls._output.lower()

    def test_help_no_n8n(self):
        self.assertNotIn("n8n", self._lower)

    def test_help_no_mcp_token(self):
        self.assertNotIn(" mcp", self._lower)
        self.assertNotIn("mcp ", self._lower)

    def test_help_no_api_key_or_token(self):
        self.assertNotIn("api_key", self._lower)
        self.assertNotIn("access_token", self._lower)

    def test_help_no_operative_cloud_phrasing(self):
        forbidden_phrases = (
            "use api", "via api", "call api", "api call",
            "n8n workflow", "cloud service", "mcp server",
            "upload to cloud", "send to cloud",
            "s3://", "gcs://",
        )
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, self._lower,
                             f"help must not present '{phrase}' as an operative action")


class TestHelpNoAutoOpen(unittest.TestCase):
    """ARCH-0636: --help must not suggest auto-opening reports/files/browser."""

    @classmethod
    def setUpClass(cls):
        _, cls._output = _capture_runner_help()
        cls._lower = cls._output.lower()

    def test_help_no_invoke_item(self):
        self.assertNotIn("invoke-item", self._lower)

    def test_help_no_webbrowser(self):
        self.assertNotIn("webbrowser", self._lower)

    def test_help_no_auto_open_phrases(self):
        for phrase in ("open report", "open browser", "auto-open",
                       "apri report", "apri browser", "apertura automatica"):
            self.assertNotIn(phrase, self._lower,
                             f"help must not suggest '{phrase}'")

    def test_help_no_start_open_html(self):
        import re
        self.assertNotRegex(self._output, r"\bstart\s+\S+\.(html|json|pdf)")


class TestHelpNoUnnegatedDestructiveLanguage(unittest.TestCase):
    """ARCH-0637: destructive verbs only allowed in explicit negation context."""

    @classmethod
    def setUpClass(cls):
        _, cls._output = _capture_runner_help()
        cls._lower = cls._output.lower()

    _FORBIDDEN = ("delete", "move", "rename", "cancellare", "spostare", "rinominare")
    _NEGATION_MARKERS = (
        "no ", "not ", "never ", "non ", "nessun", "senza ",
        "doesn't ", "won't ", "can't ", "cannot ", "no-", "non-",
    )

    def test_no_bare_destructive_verbs(self):
        import re
        for word in self._FORBIDDEN:
            for match in re.finditer(rf"\b{word}\b", self._lower):
                pos = match.start()
                prefix = self._lower[max(0, pos - 20):pos]
                negated = any(neg in prefix for neg in self._NEGATION_MARKERS)
                self.assertTrue(
                    negated,
                    f"unnegated destructive word {word!r} in help at pos {pos}; "
                    f"context: {prefix + word!r}",
                )


# ── ARCH-0639..0642: --list output details ───────────────────────────────────


class TestListModeExitAndNoExecution(unittest.TestCase):
    """ARCH-0639: --list exits 0 and never runs a subprocess."""

    def test_list_exits_zero_and_no_subprocess(self):
        with patch("scripts.run_validations.subprocess.run") as mock_run:
            rc = rv.main(["--list"])
        self.assertEqual(rc, 0)
        mock_run.assert_not_called()

    def test_list_states_no_execution(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run"):
            with redirect_stdout(buf):
                rv.main(["--list"])
        self.assertIn("no checks are executed", buf.getvalue().lower())


class TestListStepModes(unittest.TestCase):
    """ARCH-0640..0642: --list must label each step with its run mode."""

    @classmethod
    def setUpClass(cls):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run"):
            with redirect_stdout(buf):
                rv.main(["--list"])
        cls._output = buf.getvalue()
        cls._lines = cls._output.splitlines()

    def _line_for(self, label):
        matches = [l for l in self._lines if label in l]
        self.assertTrue(matches, f"label not found in --list output: {label}")
        return matches[0]

    def test_list_shows_first_run_check_as_full_only(self):
        """ARCH-0640: first-run check must be labelled 'full only'."""
        self.assertIn("full only", self._line_for("first-run check"))

    def test_list_shows_py_compile_as_quick_full(self):
        """ARCH-0641: py_compile must be labelled 'quick+full'."""
        self.assertIn("quick+full", self._line_for("py_compile"))

    def test_list_shows_validate_reports_as_quick_full(self):
        """ARCH-0641: validate_reports --help must be labelled 'quick+full'."""
        self.assertIn("quick+full", self._line_for("validate_reports --help"))

    def test_list_shows_unittest_discover_as_full_only(self):
        """ARCH-0642: unittest discover must be labelled 'full only'."""
        self.assertIn("full only", self._line_for("unittest discover"))

    def test_list_shows_synthetic_demo_as_full_only(self):
        """ARCH-0642: synthetic demo must be labelled 'full only'."""
        self.assertIn("full only", self._line_for("synthetic demo"))


# ── ARCH-0643..0644: --quick / --no-demo skip output (explicit batch labels) ─


class TestQuickSkipsFullOnlySteps(unittest.TestCase):
    """ARCH-0643: --quick must signal [SKIP] for every full-only step."""

    @classmethod
    def setUpClass(cls):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rv.main(["--quick"])
        cls._output = buf.getvalue()

    def test_quick_skips_first_run_check(self):
        self.assertIn("[SKIP] first-run check", self._output)

    def test_quick_skips_unittest_discover(self):
        self.assertIn("[SKIP] unittest discover", self._output)

    def test_quick_skips_synthetic_demo(self):
        self.assertIn("[SKIP] synthetic demo", self._output)


class TestNoDemoSkipsOnlySyntheticDemo(unittest.TestCase):
    """ARCH-0644: --no-demo must skip only synthetic demo, never first-run check."""

    @classmethod
    def setUpClass(cls):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rv.main(["--no-demo"])
        cls._output = buf.getvalue()

    def test_no_demo_skips_synthetic_demo(self):
        self.assertIn("[SKIP] synthetic demo", self._output)

    def test_no_demo_does_not_skip_first_run_check(self):
        self.assertNotIn("[SKIP] first-run check", self._output)

    def test_no_demo_does_not_skip_unittest(self):
        self.assertNotIn("[SKIP] unittest discover", self._output)


# ── ARCH-0645..0646: final summary is explicit and always printed ────────────


class TestSummaryExplicitAndPrinted(unittest.TestCase):
    """ARCH-0645/0646: summary always prints mode, run, OK, failed, skipped."""

    def _capture(self, args):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("scripts.run_validations.subprocess.run", return_value=_make_result(0)):
            with redirect_stdout(buf):
                rc = rv.main(args)
        return rc, buf.getvalue()

    def test_summary_printed_in_quick_mode(self):
        """ARCH-0646: --quick prints the final summary line."""
        rc, out = self._capture(["--quick"])
        self.assertEqual(rc, 0)
        self.assertIn("Summary (quick):", out)

    def test_summary_quick_contains_all_required_fields(self):
        """ARCH-0645: quick summary lists mode, run, OK, failed, skipped."""
        _, out = self._capture(["--quick"])
        summary_line = next(l for l in out.splitlines() if l.startswith("Summary "))
        for token in ("(quick)", " run", " OK", " failed", " skipped"):
            self.assertIn(token, summary_line,
                          f"summary line missing {token!r}: {summary_line!r}")

    def test_summary_full_contains_all_required_fields(self):
        """ARCH-0645: full summary lists mode, run, OK, failed, skipped."""
        _, out = self._capture([])
        summary_line = next(l for l in out.splitlines() if l.startswith("Summary "))
        for token in ("(full)", " run", " OK", " failed", " skipped"):
            self.assertIn(token, summary_line,
                          f"summary line missing {token!r}: {summary_line!r}")


# ── ARCH-0647: extended static source invariants ─────────────────────────────


class TestRunnerSourceInvariantsExtended(unittest.TestCase):
    """ARCH-0647: runner source must not reference network/browser/open primitives."""

    def setUp(self):
        self._src = inspect.getsource(rv)
        self._lower = self._src.lower()

    def test_no_webbrowser_module(self):
        self.assertNotIn("webbrowser", self._lower)

    def test_no_requests_module(self):
        self.assertNotIn("import requests", self._lower)
        self.assertNotIn("from requests", self._lower)

    def test_no_urllib(self):
        self.assertNotIn("urllib", self._lower)

    def test_no_socket_module(self):
        self.assertNotIn("import socket", self._lower)
        self.assertNotIn("from socket", self._lower)

    def test_no_os_startfile(self):
        self.assertNotIn("os.startfile", self._lower)
        self.assertNotIn("startfile(", self._lower)

    def test_no_invoke_item(self):
        # case-sensitive: PowerShell cmdlet name
        self.assertNotIn("Invoke-Item", self._src)

    def test_no_start_process(self):
        self.assertNotIn("start-process", self._lower)
        self.assertNotIn("subprocess.popen", self._lower)

    def test_no_start_open_html(self):
        import re
        self.assertNotRegex(self._src, r"\bstart\s+\S+\.(html|json|pdf)")


if __name__ == "__main__":
    unittest.main()
