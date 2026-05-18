"""
ARCH-0346..ARCH-0351, ARCH-0653..ARCH-0666 — Tests for run_first_time_check.py.
Verifies script safety, behavior, CLI options, and absence of forbidden operations.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO = Path(__file__).parent.parent
_SCRIPT = _REPO / "scripts" / "run_first_time_check.py"


class TestFirstTimeCheckBasic(unittest.TestCase):
    """ARCH-0346: Script passes under normal conditions."""

    def test_passes_with_all_checks_present(self):
        """Run script; expect exit code 0 when all targets exist."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"Stdout: {result.stdout}\nStderr: {result.stderr}")
        self.assertIn("[OK]", result.stdout)
        self.assertIn("Summary:", result.stdout)

    def test_output_format(self):
        """Verify output includes [OK] markers and summary."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().split("\n")
        ok_lines = [l for l in lines if "[OK]" in l]
        self.assertGreater(len(ok_lines), 0, "Expected at least one [OK] line")
        self.assertTrue(any("Summary:" in l for l in lines), "Expected Summary line")


class TestFirstTimeCheckMocking(unittest.TestCase):
    """ARCH-0347, ARCH-0348: Script fails when targets missing (mocked)."""

    def _run_with_mock(self, target_func, return_value):
        """Helper: run script with a mocked check function."""
        code = f"""
import sys
from pathlib import Path
from unittest.mock import patch

_REPO = Path(r"{str(_REPO)}")
sys.path.insert(0, str(_REPO / "scripts"))
sys.argv = ["run_first_time_check.py"]

import run_first_time_check

with patch("run_first_time_check.{target_func}", return_value={repr(return_value)}):
    sys.exit(run_first_time_check.main())
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        return result

    def test_fails_when_script_missing(self):
        """ARCH-0347: Script reports fail when run_validations.py missing."""
        result = self._run_with_mock(
            "_check_script_exists",
            "run_validations.py not found",
        )
        self.assertEqual(result.returncode, 1, f"Expected exit 1, got {result.returncode}")
        self.assertIn("[FAIL]", result.stdout)

    def test_fails_when_readme_missing(self):
        """ARCH-0348: Script reports fail when README.md missing."""
        result = self._run_with_mock(
            "_check_doc_exists",
            "README.md not found",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("[FAIL]", result.stdout)


class TestFirstTimeCheckSafety(unittest.TestCase):
    """ARCH-0349..ARCH-0351: Verify safety constraints."""

    def _read_script_source(self):
        return _SCRIPT.read_text()

    def test_no_reports_in_targets(self):
        """ARCH-0349: Script does not reference 'reports/' in checked targets."""
        source = self._read_script_source()
        self.assertNotIn("reports/", source.split("_CHECKS")[1].split("def main")[0])

    def test_no_open_file_or_browser_operations(self):
        """ARCH-0350: Source does not contain start, Invoke-Item, webbrowser."""
        source = self._read_script_source()
        for keyword in ["start ", "Invoke-Item", "webbrowser", "os.startfile"]:
            self.assertNotIn(keyword, source, f"Script contains forbidden keyword: {keyword}")

    def test_no_api_cloud_secrets(self):
        """ARCH-0351: Source does not contain API/cloud/n8n/MCP/secrets keywords."""
        source = self._read_script_source()
        source_lower = source.lower()
        for keyword in ["api", "cloud", "n8n", "mcp", "token", "secret", "credentials", "azure", "aws", "gcp"]:
            self.assertNotIn(keyword, source_lower, f"Script contains forbidden keyword: {keyword}")


class TestFirstTimeCheckCLIHelp(unittest.TestCase):
    """ARCH-0653..ARCH-0657: Verify --help output."""

    def _get_help(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--help"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        return result

    def test_help_exits_zero(self):
        """ARCH-0653: --help exits 0."""
        result = self._get_help()
        self.assertEqual(result.returncode, 0, f"Expected exit 0, got {result.returncode}")

    def test_help_contains_safety_wording(self):
        """ARCH-0654: --help contains safety wording."""
        result = self._get_help()
        combined = (result.stdout + result.stderr).lower()
        for term in ["local", "no network", "no personal files", "reports/ reads", "no file modification"]:
            self.assertIn(term.lower(), combined, f"Help missing safety term: {term!r}")

    def test_help_no_api_cloud_operational(self):
        """ARCH-0655: --help does not reference API/cloud/n8n/MCP as operational actions."""
        result = self._get_help()
        combined = (result.stdout + result.stderr).lower()
        for term in ["api", "cloud", "n8n", "mcp"]:
            self.assertNotIn(term, combined, f"Help contains forbidden operational term: {term!r}")

    def test_help_no_auto_open(self):
        """ARCH-0656: --help does not suggest auto-opening reports/files/browser."""
        result = self._get_help()
        combined = (result.stdout + result.stderr).lower()
        for term in ["webbrowser", "invoke-item", "os.startfile", "open report", "open browser"]:
            self.assertNotIn(term, combined, f"Help contains auto-open hint: {term!r}")

    def test_help_no_destructive_language(self):
        """ARCH-0657: --help does not contain unnegatd destructive language."""
        result = self._get_help()
        combined = (result.stdout + result.stderr).lower()
        for term in ["delete", "move", "rename", "cancellare", "spostare", "rinominare"]:
            self.assertNotIn(term, combined, f"Help contains destructive term: {term!r}")


class TestFirstTimeCheckListMode(unittest.TestCase):
    """ARCH-0659..ARCH-0660: Verify --list behavior."""

    def test_list_exits_zero(self):
        """ARCH-0659: --list exits 0."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--list"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_list_shows_all_checks(self):
        """ARCH-0659: --list prints all planned checks."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--list"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = result.stdout
        self.assertIn("Planned first-run checks", output)
        self.assertIn("Python", output)
        self.assertIn("run_validations.py", output)
        self.assertIn("README.md", output)

    def test_list_no_operational_output(self):
        """ARCH-0660: --list does not print [OK], [FAIL], or Summary."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--list"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertNotIn("[OK]", result.stdout)
        self.assertNotIn("[FAIL]", result.stdout)
        self.assertNotIn("Summary:", result.stdout)


class TestFirstTimeCheckSummary(unittest.TestCase):
    """ARCH-0662..ARCH-0663: Summary is always printed."""

    def test_summary_printed_on_ok(self):
        """ARCH-0662: Summary line is printed when all checks pass."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT)],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Summary:", result.stdout)
        self.assertIn("passed", result.stdout)

    def test_summary_printed_on_fail(self):
        """ARCH-0663: Summary line is printed when a check fails (patched _CHECKS)."""
        code = f"""
import sys
from pathlib import Path
from unittest.mock import patch

_REPO = Path(r"{str(_REPO)}")
sys.path.insert(0, str(_REPO / "scripts"))
sys.argv = ["run_first_time_check.py"]

import run_first_time_check

synthetic_checks = [("Synthetic fail", lambda: "synthetic failure for test")]
with patch("run_first_time_check._CHECKS", synthetic_checks):
    sys.exit(run_first_time_check.main())
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Summary:", result.stdout)
        self.assertIn("FAILED", result.stdout)
        self.assertIn("[FAIL]", result.stdout)


class TestFirstTimeCheckUnits(unittest.TestCase):
    """ARCH-0664..ARCH-0665: Unit tests for check functions."""

    def setUp(self):
        sys.path.insert(0, str(_REPO / "scripts"))
        import run_first_time_check
        self.mod = run_first_time_check

    def test_check_python_version_current(self):
        """ARCH-0664: _check_python_version returns True for current interpreter."""
        result = self.mod._check_python_version()
        self.assertTrue(result is True, f"Expected True, got: {result!r}")

    def test_check_python_version_fail(self):
        """ARCH-0664: _check_python_version returns error string for old Python."""
        import collections
        VersionInfo = collections.namedtuple(
            "version_info", ["major", "minor", "micro", "releaselevel", "serial"]
        )
        mock_vi = VersionInfo(3, 7, 0, "final", 0)
        with patch.object(sys, "version_info", mock_vi):
            result = self.mod._check_python_version()
            self.assertIsInstance(result, str)
            self.assertIn("3.7", result)

    def test_check_script_exists_real(self):
        """ARCH-0665: _check_script_exists returns True for existing script."""
        result = self.mod._check_script_exists("scripts/run_validations.py")
        self.assertTrue(result is True, f"Expected True, got: {result!r}")

    def test_check_script_exists_missing(self):
        """ARCH-0665: _check_script_exists returns error string for missing path."""
        result = self.mod._check_script_exists("scripts/__nonexistent__.py")
        self.assertIsInstance(result, str)
        self.assertIn("not found", result)

    def test_check_doc_exists_real(self):
        """ARCH-0665: _check_doc_exists returns True for existing doc."""
        result = self.mod._check_doc_exists("README.md")
        self.assertTrue(result is True, f"Expected True, got: {result!r}")

    def test_check_doc_exists_missing(self):
        """ARCH-0665: _check_doc_exists returns error string for missing doc."""
        result = self.mod._check_doc_exists("docs/__nonexistent__.md")
        self.assertIsInstance(result, str)
        self.assertIn("not found", result)

    def test_check_doc_exists_monkeypatch_repo(self):
        """ARCH-0665: _check_doc_exists respects _REPO; works with patched path."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "docs").mkdir()
            (tmp / "docs" / "COMMANDS.md").write_text("x")
            original = self.mod._REPO
            try:
                self.mod._REPO = tmp
                result = self.mod._check_doc_exists("docs/COMMANDS.md")
                self.assertTrue(result is True)
                result2 = self.mod._check_doc_exists("docs/MISSING.md")
                self.assertIsInstance(result2, str)
            finally:
                self.mod._REPO = original


class TestFirstTimeCheckStaticSource(unittest.TestCase):
    """ARCH-0666: Static source check — forbidden imports/operations absent."""

    def _src(self):
        return _SCRIPT.read_text()

    def test_no_webbrowser(self):
        self.assertNotIn("webbrowser", self._src())

    def test_no_subprocess(self):
        self.assertNotIn("subprocess", self._src())

    def test_no_requests(self):
        self.assertNotIn("requests", self._src())

    def test_no_urllib(self):
        self.assertNotIn("urllib", self._src())

    def test_no_socket(self):
        self.assertNotIn("socket", self._src())

    def test_no_os_startfile(self):
        self.assertNotIn("os.startfile", self._src())

    def test_no_invoke_item(self):
        self.assertNotIn("Invoke-Item", self._src())

    def test_no_open_write(self):
        self.assertNotIn('open(', self._src())

    def test_no_mkdir(self):
        self.assertNotIn("mkdir", self._src())


class TestFirstTimeCheckCLIOptions(unittest.TestCase):
    """ARCH-0356..ARCH-0360: Test --list and --quiet options."""

    def test_list_does_not_run_checks(self):
        """ARCH-0359: --list outputs check labels only, no [OK]/[FAIL]."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--list"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertNotIn("[OK]", result.stdout)
        self.assertNotIn("[FAIL]", result.stdout)
        self.assertNotIn("Summary:", result.stdout)
        lines = result.stdout.strip().split("\n")
        self.assertGreater(len(lines), 0)

    def test_quiet_suppresses_ok_lines(self):
        """ARCH-0360: --quiet suppresses [OK] lines but keeps Summary."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--quiet"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertNotIn("[OK]", result.stdout)
        self.assertIn("Summary:", result.stdout)

    def test_quiet_keeps_summary(self):
        """ARCH-0360: --quiet keeps Summary even with failures (via subprocess)."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "--quiet"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertIn("Summary:", result.stdout)


class TestFirstTimeCheckConsistency(unittest.TestCase):
    """Verify integration with repo structure."""

    def test_expected_scripts_exist(self):
        for path in [_REPO / "scripts" / "run_validations.py", _REPO / "scripts" / "run_synthetic_demo.py"]:
            self.assertTrue(path.exists(), f"Expected script missing: {path}")

    def test_expected_docs_exist(self):
        for path in [_REPO / "docs" / "COMMANDS.md", _REPO / "README.md"]:
            self.assertTrue(path.exists(), f"Expected doc missing: {path}")


class TestFirstTimeCheckDocumentation(unittest.TestCase):
    """ARCH-0362: Verify documentation mentions --list option."""

    def test_list_option_documented(self):
        readme = _REPO / "README.md"
        commands = _REPO / "docs" / "COMMANDS.md"
        combined = (readme.read_text() if readme.exists() else "") + (commands.read_text() if commands.exists() else "")
        self.assertIn("--list", combined)


if __name__ == "__main__":
    unittest.main()
