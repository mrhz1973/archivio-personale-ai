"""
ARCH-0218..ARCH-0221, ARCH-0228..ARCH-0250, ARCH-0269..ARCH-0280 — Tests for scripts/run_synthetic_demo.py.

Verifies that the synthetic demo:
- produces the expected output files in a temp dir;
- never writes to reports/;
- exits 0 on a clean run;
- exits non-zero when a pipeline step fails;
- --list exits 0 and creates no files;
- uses sys.executable for subprocesses;
- runs subprocesses from repo root (cwd);
- fails clearly when an expected script is missing;
- --quick produces inventory JSON, classification JSON, and inventory HTML;
- --keep-temp keeps the directory and prints its path and manifest path;
- without --keep-temp the directory is removed;
- writes demo_manifest.json in full and quick modes;
- manifest contains correct mode, step counts, and generated files;
- manifest does not contain reports/ paths, home dir paths, or secret keywords.
"""

import io
import json
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


def _run_pipeline_fresh(quick=False):
    """Helper: run _run_pipeline in a fresh temp dir, return (code, tmpdir_path)."""
    with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
        tmpdir = Path(tmp)
        code = demo._run_pipeline(tmpdir, keep_temp=False, quick=quick)
        return code, tmpdir


class TestSyntheticDemoOutputs(unittest.TestCase):
    """ARCH-0220: demo produces inventory JSON, classification JSON, and HTML reports."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="archivio_test_demo_")
        self._tmpdir = Path(self._tmp)
        demo._run_pipeline(self._tmpdir, keep_temp=False)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_demo_exits_zero(self):
        code = demo.main([])
        self.assertEqual(code, 0)

    def test_demo_produces_inventory_json(self):
        self.assertTrue((self._tmpdir / "inventory.json").is_file())

    def test_demo_produces_classifications_json(self):
        self.assertTrue((self._tmpdir / "classifications.json").is_file())

    def test_demo_produces_proposed_actions_json(self):
        self.assertTrue((self._tmpdir / "proposed_actions.json").is_file())

    def test_demo_produces_inventory_html(self):
        self.assertTrue((self._tmpdir / "inventory_report.html").is_file())

    def test_demo_produces_classification_html(self):
        self.assertTrue((self._tmpdir / "classification_report.html").is_file())

    def test_demo_produces_action_plan_html(self):
        self.assertTrue((self._tmpdir / "action_plan_report.html").is_file())


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

            def _bad_source(base):
                return base / "no_such_source"

            with patch.object(demo, "_make_synthetic_source", _bad_source):
                code = demo._run_pipeline(tmpdir, keep_temp=False)
            self.assertNotEqual(code, 0)


class TestDemoList(unittest.TestCase):
    """ARCH-0228: --list exits 0, prints step names, creates no temp files."""

    def test_list_exits_zero(self):
        code = demo.main(["--list"])
        self.assertEqual(code, 0)

    def test_list_prints_step_names(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main(["--list"])
        output = buf.getvalue()
        for name in demo._FULL_STEPS_NAMES:
            self.assertIn(name, output)

    def test_list_creates_no_temp_files(self):
        tmp_before = set(Path(tempfile.gettempdir()).glob("archivio_demo_*"))
        demo.main(["--list"])
        tmp_after = set(Path(tempfile.gettempdir()).glob("archivio_demo_*"))
        self.assertEqual(tmp_before, tmp_after)

    def test_quick_list_shows_quick_steps(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main(["--quick", "--list"])
        output = buf.getvalue()
        for name in demo._QUICK_STEPS_NAMES:
            self.assertIn(name, output)


class TestDemoSummary(unittest.TestCase):
    """ARCH-0229/0230/0231: final summary shows totals and tmpdir."""

    def test_summary_on_success_shows_ok(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main([])
        output = buf.getvalue()
        self.assertIn("OK:", output)
        self.assertIn("Failed: 0", output)
        self.assertIn("Steps:", output)
        self.assertIn("Dir:", output)

    def test_summary_on_failure_shows_failures(self):
        buf = io.StringIO()

        def _bad_source(base):
            return base / "no_such_source"

        with patch.object(demo, "_make_synthetic_source", _bad_source):
            with patch("sys.stdout", buf):
                with tempfile.TemporaryDirectory() as tmp:
                    demo._run_pipeline(Path(tmp), keep_temp=False)
        output = buf.getvalue()
        self.assertIn("Failed:", output)


class TestDemoSysExecutable(unittest.TestCase):
    """ARCH-0233: subprocess commands use sys.executable."""

    def test_run_uses_sys_executable(self):
        import subprocess as sp
        original_sp_run = sp.run

        calls = []

        def mock_sp_run(cmd, **kwargs):
            calls.append(cmd)
            return original_sp_run(cmd, **kwargs)

        with patch("scripts.run_synthetic_demo.subprocess") as mock_sp:
            mock_sp.run.side_effect = mock_sp_run
            with tempfile.TemporaryDirectory() as tmp:
                pass

        # Verify _PYTHON constant is sys.executable
        self.assertEqual(demo._PYTHON, sys.executable)

    def test_run_command_starts_with_python(self):
        """Verify that _run prepends _PYTHON to the argv."""
        recorded = []

        def fake_run(cmd, **kwargs):
            recorded.append(cmd[0])
            class R:
                returncode = 0
                stdout = ""
                stderr = ""
            return R()

        with patch("scripts.run_synthetic_demo.subprocess.run", fake_run):
            demo._run("test_step", ["scripts/dummy.py"])

        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0], sys.executable)


class TestDemoCwd(unittest.TestCase):
    """ARCH-0235: subprocesses run from repo root."""

    def test_subprocess_uses_repo_root_cwd(self):
        recorded_cwds = []

        def fake_run(cmd, **kwargs):
            recorded_cwds.append(kwargs.get("cwd"))
            class R:
                returncode = 0
                stdout = ""
                stderr = ""
            return R()

        with patch("scripts.run_synthetic_demo.subprocess.run", fake_run):
            demo._run("test_step", ["scripts/dummy.py"])

        self.assertEqual(len(recorded_cwds), 1)
        self.assertEqual(recorded_cwds[0], str(_REPO_ROOT))


class TestDemoMissingScript(unittest.TestCase):
    """ARCH-0237: demo fails clearly when an expected script is missing."""

    def test_missing_script_returns_nonzero(self):
        with patch.object(demo, "_check_expected_scripts", return_value=["scripts/nonexistent.py"]):
            with tempfile.TemporaryDirectory() as tmp:
                code = demo._run_pipeline(Path(tmp), keep_temp=False)
        self.assertNotEqual(code, 0)

    def test_missing_script_prints_message(self):
        buf = io.StringIO()
        with patch.object(demo, "_check_expected_scripts", return_value=["scripts/nonexistent.py"]):
            with patch("sys.stdout", buf):
                with tempfile.TemporaryDirectory() as tmp:
                    demo._run_pipeline(Path(tmp), keep_temp=False)
        self.assertIn("nonexistent.py", buf.getvalue())


class TestDemoQuick(unittest.TestCase):
    """ARCH-0239: --quick produces at least inventory JSON, classification JSON, inventory HTML."""

    def test_quick_exits_zero(self):
        code = demo.main(["--quick"])
        self.assertEqual(code, 0)

    def test_quick_produces_inventory_json(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, quick=True)
            self.assertTrue((tmpdir / "inventory.json").is_file())

    def test_quick_produces_classifications_json(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, quick=True)
            self.assertTrue((tmpdir / "classifications.json").is_file())

    def test_quick_produces_inventory_html(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_demo_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, quick=True)
            self.assertTrue((tmpdir / "inventory_report.html").is_file())


class TestDemoKeepTemp(unittest.TestCase):
    """ARCH-0249/0250: --keep-temp keeps the directory; without it the directory is removed."""

    def test_keep_temp_prints_path(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main(["--keep-temp"])
        output = buf.getvalue()
        self.assertIn("Temp directory kept at:", output)

        # Extract path from output and verify it exists, then clean up
        for line in output.splitlines():
            if "Temp directory kept at:" in line:
                path = Path(line.split("Temp directory kept at:")[-1].strip())
                self.assertTrue(path.exists())
                import shutil
                shutil.rmtree(path, ignore_errors=True)
                break

    def test_without_keep_temp_dir_is_removed(self):
        created = []
        original_mkdtemp = tempfile.mkdtemp

        def spy_mkdtemp(**kwargs):
            path = original_mkdtemp(**kwargs)
            created.append(path)
            return path

        with patch("scripts.run_synthetic_demo.tempfile.mkdtemp", spy_mkdtemp):
            demo.main([])

        self.assertEqual(len(created), 1)
        self.assertFalse(Path(created[0]).exists())


# ── ARCH-0269..ARCH-0278: manifest tests ─────────────────────────────────────

class TestDemoManifestFullMode(unittest.TestCase):
    """ARCH-0269/0271/0272/0273/0274/0275/0276: manifest in full mode."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="archivio_test_manifest_")
        self._tmpdir = Path(self._tmp)
        demo._run_pipeline(self._tmpdir, keep_temp=False, quick=False)
        manifest_path = self._tmpdir / "demo_manifest.json"
        self._manifest_exists = manifest_path.is_file()
        if self._manifest_exists:
            self._manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            self._manifest = {}

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_manifest_created_in_full_mode(self):
        """ARCH-0269: manifest is written after a full run."""
        self.assertTrue(self._manifest_exists)

    def test_manifest_mode_is_full(self):
        """ARCH-0271: manifest records mode = full."""
        self.assertEqual(self._manifest.get("mode"), "full")

    def test_manifest_contains_step_counts(self):
        """ARCH-0272: manifest contains steps_total, steps_ok, steps_failed."""
        self.assertIn("steps_total", self._manifest)
        self.assertIn("steps_ok", self._manifest)
        self.assertIn("steps_failed", self._manifest)
        self.assertEqual(self._manifest["steps_total"], len(demo._FULL_STEPS_NAMES))
        self.assertEqual(self._manifest["steps_failed"], 0)

    def test_manifest_contains_expected_generated_files(self):
        """ARCH-0273: manifest lists generated files (inventory, classification, action plan)."""
        paths = {f["path"] for f in self._manifest.get("generated_files", [])}
        self.assertTrue(any("inventory" in p for p in paths), f"inventory not in {paths}")
        self.assertTrue(any("classification" in p for p in paths), f"classification not in {paths}")
        self.assertTrue(any("action_plan" in p for p in paths), f"action_plan not in {paths}")

    def test_manifest_path_does_not_reference_reports_dir(self):
        """ARCH-0274: manifest temp_dir and file paths do not reference reports/."""
        text = json.dumps(self._manifest)
        self.assertNotIn("reports/", text)
        self.assertNotIn("reports\\", text)

    def test_manifest_temp_dir_has_no_home_path(self):
        """ARCH-0275: manifest temp_dir is basename only — no user home path."""
        temp_dir_value = self._manifest.get("temp_dir", "")
        # Must be a basename (no path separator)
        self.assertNotIn("/", temp_dir_value)
        self.assertNotIn("\\", temp_dir_value)
        # Must not contain the real home directory name
        home = Path.home().name
        self.assertNotIn(home, temp_dir_value)

    def test_manifest_has_no_secret_keywords(self):
        """ARCH-0276: manifest content contains no api_key/access_token/secret/token keywords."""
        text = json.dumps(self._manifest).lower()
        for keyword in ("api_key", "access_token", "secret", "token"):
            self.assertNotIn(keyword, text, f"Found forbidden keyword '{keyword}' in manifest")

    def test_manifest_steps_list_has_labels(self):
        """Each step entry has a label field."""
        steps = self._manifest.get("steps", [])
        self.assertTrue(len(steps) > 0)
        for step in steps:
            self.assertIn("label", step)
            self.assertIn("returncode", step)
            self.assertIn("status", step)


class TestDemoManifestQuickMode(unittest.TestCase):
    """ARCH-0270/0271: manifest is created in quick mode with correct mode field."""

    def test_manifest_created_in_quick_mode(self):
        """ARCH-0270: manifest is written after a quick run."""
        with tempfile.TemporaryDirectory(prefix="archivio_test_manifest_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, quick=True)
            self.assertTrue((tmpdir / "demo_manifest.json").is_file())

    def test_manifest_mode_is_quick(self):
        """ARCH-0271: manifest records mode = quick."""
        with tempfile.TemporaryDirectory(prefix="archivio_test_manifest_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, quick=True)
            manifest = json.loads((tmpdir / "demo_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest.get("mode"), "quick")


class TestDemoNoManifest(unittest.TestCase):
    """ARCH-0282/0283: --no-manifest skips manifest but keeps pipeline working."""

    def test_no_manifest_does_not_create_manifest(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_nomanifest_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, no_manifest=True)
            self.assertFalse((tmpdir / "demo_manifest.json").exists())

    def test_no_manifest_exit_code_zero(self):
        code = demo.main(["--no-manifest"])
        self.assertEqual(code, 0)

    def test_no_manifest_produces_inventory_json(self):
        with tempfile.TemporaryDirectory(prefix="archivio_test_nomanifest_") as tmp:
            tmpdir = Path(tmp)
            demo._run_pipeline(tmpdir, keep_temp=False, no_manifest=True)
            self.assertTrue((tmpdir / "inventory.json").is_file())


class TestDemoQuiet(unittest.TestCase):
    """ARCH-0279/0280: --quiet reduces output but keeps exit code and manifest."""

    def test_quiet_exit_code_zero(self):
        """ARCH-0280: --quiet still exits 0 on success."""
        code = demo.main(["--quiet"])
        self.assertEqual(code, 0)

    def test_quiet_manifest_still_created(self):
        """ARCH-0280: manifest is written even with --quiet."""
        created = []
        original_mkdtemp = tempfile.mkdtemp

        def spy_mkdtemp(**kwargs):
            path = original_mkdtemp(**kwargs)
            created.append(path)
            return path

        with patch("scripts.run_synthetic_demo.tempfile.mkdtemp", spy_mkdtemp):
            demo.main(["--quiet", "--keep-temp"])

        self.assertEqual(len(created), 1)
        manifest = Path(created[0]) / "demo_manifest.json"
        self.assertTrue(manifest.exists())
        import shutil
        shutil.rmtree(created[0], ignore_errors=True)

    def test_quiet_suppresses_header(self):
        """ARCH-0279: --quiet output does not include the === header line."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main(["--quiet"])
        output = buf.getvalue()
        self.assertNotIn("===", output)

    def test_quiet_still_prints_summary(self):
        """ARCH-0279: --quiet still prints the step count summary."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main(["--quiet"])
        output = buf.getvalue()
        self.assertIn("Steps:", output)


class TestDemoKeepTempManifestPath(unittest.TestCase):
    """ARCH-0278: --keep-temp prints both the temp dir path and the manifest path."""

    def test_keep_temp_prints_manifest_path(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            demo.main(["--keep-temp"])
        output = buf.getvalue()

        # Must mention the manifest file
        self.assertIn("demo_manifest.json", output)

        # Clean up kept temp dir
        import shutil
        for line in output.splitlines():
            if "Temp directory kept at:" in line:
                path = Path(line.split("Temp directory kept at:")[-1].strip())
                shutil.rmtree(path, ignore_errors=True)
                break


if __name__ == "__main__":
    unittest.main()
