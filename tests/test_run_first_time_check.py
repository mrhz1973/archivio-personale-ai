"""
ARCH-0346..ARCH-0351 — Tests for run_first_time_check.py.
Verifies script safety, behavior, and absence of forbidden operations.
"""

import subprocess
import sys
import tempfile
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

    def _run_with_mock(self, target_module, target_func, side_effect):
        """Helper: run script with a mocked check function."""
        code = f"""
import sys
from pathlib import Path
from unittest.mock import patch

_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import run_first_time_check

with patch("run_first_time_check.{target_func}", side_effect={side_effect}):
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
        # Mock the check to return an error message
        side_effect = lambda: "run_validations.py not found"
        result = self._run_with_mock(
            "run_first_time_check",
            "_check_script_exists",
            side_effect,
        )
        self.assertEqual(result.returncode, 1, f"Expected exit 1, got {result.returncode}")
        self.assertIn("[FAIL]", result.stdout)

    def test_fails_when_readme_missing(self):
        """ARCH-0348: Script reports fail when README.md missing."""
        side_effect = lambda: "README.md not found"
        result = self._run_with_mock(
            "run_first_time_check",
            "_check_doc_exists",
            side_effect,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("[FAIL]", result.stdout)


class TestFirstTimeCheckSafety(unittest.TestCase):
    """ARCH-0349..ARCH-0351: Verify safety constraints."""

    def _read_script_source(self):
        """Load source of run_first_time_check.py."""
        return _SCRIPT.read_text()

    def test_no_reports_in_targets(self):
        """ARCH-0349: Script does not reference 'reports/' in checked targets."""
        source = self._read_script_source()
        # The _CHECKS tuple should not include 'reports/' paths
        # Verify by checking that the explicit path list excludes it
        self.assertNotIn("reports/", source.split("_CHECKS")[1].split("def main")[0])

    def test_no_open_file_or_browser_operations(self):
        """ARCH-0350: Source does not contain start, Invoke-Item, webbrowser."""
        source = self._read_script_source()
        forbidden_keywords = ["start ", "Invoke-Item", "webbrowser", "os.startfile"]
        for keyword in forbidden_keywords:
            self.assertNotIn(keyword, source, f"Script contains forbidden keyword: {keyword}")

    def test_no_api_cloud_secrets(self):
        """ARCH-0351: Source does not contain API/cloud/n8n/MCP/secrets keywords."""
        source = self._read_script_source()
        forbidden_keywords = [
            "API",
            "cloud",
            "n8n",
            "MCP",
            "token",
            "secret",
            "credentials",
            "azure",
            "aws",
            "gcp",
        ]
        # Case-insensitive check for most keywords
        source_lower = source.lower()
        for keyword in forbidden_keywords:
            self.assertNotIn(
                keyword.lower(),
                source_lower,
                f"Script contains forbidden keyword: {keyword}",
            )


class TestFirstTimeCheckConsistency(unittest.TestCase):
    """Verify integration with repo structure."""

    def test_expected_scripts_exist(self):
        """Verify that scripts checked by the test actually exist."""
        expected = [
            _REPO / "scripts" / "run_validations.py",
            _REPO / "scripts" / "run_synthetic_demo.py",
        ]
        for path in expected:
            self.assertTrue(path.exists(), f"Expected script missing: {path}")

    def test_expected_docs_exist(self):
        """Verify that docs checked by the test actually exist."""
        expected = [
            _REPO / "docs" / "COMMANDS.md",
            _REPO / "README.md",
        ]
        for path in expected:
            self.assertTrue(path.exists(), f"Expected doc missing: {path}")


if __name__ == "__main__":
    unittest.main()
