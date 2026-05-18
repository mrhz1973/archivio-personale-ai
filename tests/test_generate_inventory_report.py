"""
ARCH-0430..ARCH-0464 — Tests for generate_inventory_report.py.
All tests use synthetic data only. No personal files or reports/ touched.
"""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.generate_inventory_report as gir


# ── helpers ───────────────────────────────────────────────────────────────────

def _minimal_data(**kwargs):
    """Return a minimal inventory dict; kwargs override top-level keys."""
    base = {
        "summary": {
            "source": "/tmp/test",
            "total_files": 2,
            "total_size_bytes": 1024,
            "extensions_count": {".txt": 2},
            "skipped_count": 0,
            "errors_count": 0,
        },
        "files": [
            {"relative_path": "a.txt", "filename": "a.txt",
             "extension": ".txt", "size_bytes": 512},
            {"relative_path": "b.txt", "filename": "b.txt",
             "extension": ".txt", "size_bytes": 512},
        ],
        "errors": [],
    }
    base.update(kwargs)
    return base


def _full_data():
    """Return a full inventory dict with metadata and new summary fields."""
    d = _minimal_data()
    d["metadata"] = {
        "schema_version": "1.0",
        "generated_at_iso": "2026-01-01T00:00:00+00:00",
        "tool": "inventory_readonly.py",
        "mode": "read_only",
    }
    d["summary"]["total_size_human"] = "1.0 KiB"
    d["summary"]["directories_scanned"] = 3
    d["summary"]["ignored_dirs_count"] = 1
    return d


# ── ARCH-0432/0433/0434/0435: help exits 0 and safe wording ──────────────────

class TestGenerateInventoryReportHelp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        buf = io.StringIO()
        code = 0
        try:
            with patch("sys.argv", ["generate_inventory_report.py", "--help"]):
                with redirect_stdout(buf):
                    with redirect_stderr(buf):
                        gir.main()
        except SystemExit as e:
            code = e.code if e.code is not None else 0
        cls._help = buf.getvalue()
        cls._code = code

    def test_help_exits_zero(self):
        """ARCH-0432: --help exits 0."""
        self.assertEqual(self._code, 0,
                         f"--help exited {self._code}; output:\n{self._help}")

    def test_help_mentions_input_json(self):
        """ARCH-0433: help mentions input JSON."""
        self.assertIn("json", self._help.lower(),
                      "help must mention JSON input")

    def test_help_mentions_output_html(self):
        """ARCH-0433: help mentions output HTML."""
        self.assertIn("html", self._help.lower(),
                      "help must mention HTML output")

    def test_help_no_destructive_language(self):
        """ARCH-0434: help has no destructive action language."""
        lower = self._help.lower()
        for phrase in ("delete automatically", "move automatically",
                       "rename automatically", "will delete", "will move",
                       "cancella automaticamente", "sposta automaticamente"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)

    def test_help_no_cloud_api(self):
        """ARCH-0435: help has no cloud/API/n8n/MCP references."""
        lower = self._help.lower()
        for phrase in ("api_key", "access_token", "n8n", " mcp", "s3://", "gcs://"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)


# ── ARCH-0444/0445: metadata rendering ───────────────────────────────────────

class TestBuildHtmlMetadata(unittest.TestCase):

    def test_metadata_fields_rendered(self):
        """ARCH-0444: JSON with metadata shows schema_version, generated_at_iso, tool, mode."""
        result = gir.build_html(_full_data())
        self.assertIn("1.0", result)
        self.assertIn("2026-01-01T00:00:00", result)
        self.assertIn("inventory_readonly.py", result)
        self.assertIn("sola lettura", result)

    def test_mode_read_only_shows_italian_label(self):
        """ARCH-0442: mode read_only shows 'Modalità: sola lettura'."""
        result = gir.build_html(_full_data())
        self.assertIn("sola lettura", result)

    def test_metadata_section_heading_italian(self):
        """ARCH-0437: metadata section heading is in Italian."""
        result = gir.build_html(_full_data())
        self.assertIn("Informazioni report", result)

    def test_no_metadata_produces_valid_html(self):
        """ARCH-0445: JSON without metadata still produces valid HTML."""
        result = gir.build_html(_minimal_data())
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn('<html lang="it">', result)
        self.assertNotIn("Informazioni report", result)

    def test_no_metadata_no_exception(self):
        """ARCH-0443: missing metadata does not raise."""
        try:
            gir.build_html(_minimal_data())
        except Exception as exc:
            self.fail(f"build_html raised {exc} with missing metadata")


# ── ARCH-0448/0449: total_size_human fallback ─────────────────────────────────

class TestBuildHtmlSizeDisplay(unittest.TestCase):

    def test_total_size_human_shown_when_present(self):
        """ARCH-0448: total_size_human used when present."""
        result = gir.build_html(_full_data())
        self.assertIn("1.0 KiB", result)

    def test_fallback_to_total_size_bytes(self):
        """ARCH-0449: fmt_size fallback when total_size_human absent."""
        data = _minimal_data()
        data["summary"]["total_size_bytes"] = 512
        result = gir.build_html(data)
        self.assertIn("512", result)


# ── ARCH-0452: directories_scanned / ignored_dirs_count ──────────────────────

class TestBuildHtmlDirectoryStats(unittest.TestCase):

    def test_directories_scanned_shown(self):
        """ARCH-0452: directories_scanned rendered in summary."""
        result = gir.build_html(_full_data())
        self.assertIn("Directory scansionate", result)
        self.assertIn("3", result)

    def test_ignored_dirs_count_shown(self):
        """ARCH-0452: ignored_dirs_count rendered in summary."""
        result = gir.build_html(_full_data())
        self.assertIn("Directory ignorate", result)
        self.assertIn("1", result)

    def test_absent_dirs_not_rendered(self):
        """ARCH-0452: missing directory stats are silently omitted."""
        result = gir.build_html(_minimal_data())
        self.assertNotIn("Directory scansionate", result)
        self.assertNotIn("Directory ignorate", result)


# ── ARCH-0454: safety note ────────────────────────────────────────────────────

class TestBuildHtmlSafetyNote(unittest.TestCase):

    def test_safety_note_present(self):
        """ARCH-0453/0454: safety note mentions review-only, no auto-actions."""
        result = gir.build_html(_minimal_data())
        lower = result.lower()
        self.assertIn("solo revisione", lower)
        self.assertIn("nessuna cancellazione", lower)
        self.assertIn("nessuno spostamento automatico", lower)
        self.assertIn("nessuna rinomina automatica", lower)


# ── ARCH-0455/0456: lang="it" ─────────────────────────────────────────────────

class TestBuildHtmlLang(unittest.TestCase):

    def test_lang_it_present(self):
        """ARCH-0455/0456: HTML has lang='it'."""
        result = gir.build_html(_minimal_data())
        self.assertIn('lang="it"', result)


# ── ARCH-0458: HTML escaping ──────────────────────────────────────────────────

class TestBuildHtmlEscaping(unittest.TestCase):

    def test_source_path_escaped(self):
        """ARCH-0457/0458: source with HTML special chars is escaped."""
        data = _minimal_data()
        data["summary"]["source"] = "/tmp/<test>&path"
        result = gir.build_html(data)
        self.assertNotIn("<test>", result)
        self.assertIn("&lt;test&gt;", result)

    def test_metadata_tool_escaped(self):
        """ARCH-0457/0458: metadata.tool with HTML chars is escaped."""
        data = _full_data()
        data["metadata"]["tool"] = "<script>alert(1)</script>"
        result = gir.build_html(data)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_file_path_escaped(self):
        """ARCH-0457/0458: file relative_path with HTML chars is escaped."""
        data = _minimal_data()
        data["files"][0]["relative_path"] = "a<b>.txt"
        result = gir.build_html(data)
        self.assertNotIn("a<b>", result)
        self.assertIn("a&lt;b&gt;", result)


# ── ARCH-0459/0460: section title and no auto-action language ────────────────

class TestBuildHtmlReviewTitle(unittest.TestCase):

    def test_largest_files_section_is_review_list(self):
        """ARCH-0459: section title clarifies it is a review list."""
        result = gir.build_html(_minimal_data())
        self.assertIn("lista di revisione", result.lower())

    def test_no_automatic_action_language(self):
        """ARCH-0460: HTML does not suggest automatic actions on files."""
        result = gir.build_html(_full_data())
        lower = result.lower()
        for phrase in ("cancella automaticamente", "sposta automaticamente",
                       "rinomina automaticamente", "will delete", "will move"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)


if __name__ == "__main__":
    unittest.main()
