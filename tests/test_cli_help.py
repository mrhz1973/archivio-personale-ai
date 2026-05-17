"""
ARCH-0166..ARCH-0178 — CLI help consistency and safety content tests.

Verifies that all script --help flags exit 0 and that help text contains
no destructive, cloud/API, or auto-open-report language.
All tests are in-process; no subprocesses, no temp dirs, no personal files.
"""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.inventory_readonly import main as _inv_main
from scripts.classify_inventory import main as _cls_main
from scripts.generate_inventory_report import main as _inv_rep_main
from scripts.generate_classification_report import main as _cls_rep_main
from scripts.generate_action_plan_report import main as _ap_rep_main
import scripts.validate_reports as vr
import scripts.run_validations as rv


# ── helpers ───────────────────────────────────────────────────────────────────

def _argparse_help(main_fn, script_name):
    """Call an argparse-based main() with sys.argv=[script, --help].
    Captures stdout+stderr and catches SystemExit. Returns (exit_code, output)."""
    buf = io.StringIO()
    try:
        with patch("sys.argv", [script_name, "--help"]):
            with redirect_stdout(buf):
                with redirect_stderr(buf):
                    main_fn()
        return 0, buf.getvalue()
    except SystemExit as e:
        return (e.code if e.code is not None else 0), buf.getvalue()


def _argv_help(main_fn):
    """Call a main(argv) function with ['--help'].
    Captures stdout+stderr and catches SystemExit. Returns (exit_code, output)."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            with redirect_stderr(buf):
                rc = main_fn(["--help"])
        return (rc if rc is not None else 0), buf.getvalue()
    except SystemExit as e:
        return (e.code if e.code is not None else 0), buf.getvalue()


def _collect_help():
    """Build the (exit_code, output) map for all scripts."""
    return {
        "inventory_readonly":           _argparse_help(_inv_main, "inventory_readonly.py"),
        "classify_inventory":           _argparse_help(_cls_main, "classify_inventory.py"),
        "generate_inventory_report":    _argparse_help(_inv_rep_main, "generate_inventory_report.py"),
        "generate_classification_report": _argparse_help(_cls_rep_main, "generate_classification_report.py"),
        "generate_action_plan_report":  _argparse_help(_ap_rep_main, "generate_action_plan_report.py"),
        "validate_reports":             _argv_help(vr.main),
        "run_validations":              _argv_help(rv.main),
    }


# ── ARCH-0166..0172, ARCH-0177: --help exits 0 for all scripts ───────────────

class TestHelpExitZero(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._help = _collect_help()

    def _assert_exits_zero(self, script_name):
        code, output = self._help[script_name]
        self.assertEqual(code, 0,
                         f"{script_name} --help exited {code!r}; output:\n{output}")

    def test_inventory_readonly_help_exits_zero(self):              # ARCH-0166
        self._assert_exits_zero("inventory_readonly")

    def test_classify_inventory_help_exits_zero(self):              # ARCH-0167
        self._assert_exits_zero("classify_inventory")

    def test_generate_inventory_report_help_exits_zero(self):       # ARCH-0168
        self._assert_exits_zero("generate_inventory_report")

    def test_generate_classification_report_help_exits_zero(self):  # ARCH-0169
        self._assert_exits_zero("generate_classification_report")

    def test_generate_action_plan_report_help_exits_zero(self):     # ARCH-0170
        self._assert_exits_zero("generate_action_plan_report")

    def test_validate_reports_help_exits_zero(self):                # ARCH-0171
        self._assert_exits_zero("validate_reports")

    def test_run_validations_help_exits_zero(self):                 # ARCH-0172
        self._assert_exits_zero("run_validations")


# ── ARCH-0173: help text has no destructive-action language ──────────────────

class TestHelpNoDestructiveLanguage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._help = _collect_help()

    _FORBIDDEN = (
        "move automatically", "rename automatically", "delete automatically",
        "sposta automaticamente", "cancella automaticamente",
        "move now", "rename now", "delete now",
        "safe to delete", "will delete", "will move",
    )

    def test_all_scripts_no_destructive_language(self):
        for name, (_, output) in self._help.items():
            lower = output.lower()
            for phrase in self._FORBIDDEN:
                with self.subTest(script=name, phrase=phrase):
                    self.assertNotIn(phrase, lower)


# ── ARCH-0174: help text has no cloud/API/n8n/MCP references ─────────────────

class TestHelpNoCloudAPIReferences(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._help = _collect_help()

    _FORBIDDEN = ("api_key", "access_token", "n8n", " mcp", "s3://", "gcs://")

    def test_all_scripts_no_cloud_api(self):
        for name, (_, output) in self._help.items():
            lower = output.lower()
            for phrase in self._FORBIDDEN:
                with self.subTest(script=name, phrase=phrase):
                    self.assertNotIn(phrase, lower)


# ── ARCH-0175: help text has no auto-open-report suggestions ─────────────────

class TestHelpNoAutoOpenReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._help = _collect_help()

    _FORBIDDEN = ("invoke-item", "webbrowser", "open report", "auto-open")

    def test_all_scripts_no_auto_open(self):
        for name, (_, output) in self._help.items():
            lower = output.lower()
            for phrase in self._FORBIDDEN:
                with self.subTest(script=name, phrase=phrase):
                    self.assertNotIn(phrase, lower)


# ── ARCH-0178: missing-input gap coverage (run_validations unknown flag) ──────
# Note: inventory_readonly, classify_inventory, and all report generators are
# already covered in test_cli_smoke.py and test_report_generators_regression.py.

class TestBadFlagExitsNonZero(unittest.TestCase):

    def test_run_validations_unknown_flag_exits_nonzero(self):
        buf = io.StringIO()
        rc = 0
        try:
            with redirect_stderr(buf):
                rv.main(["--no-such-flag"])
        except SystemExit as e:
            rc = e.code if e.code is not None else 1
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
