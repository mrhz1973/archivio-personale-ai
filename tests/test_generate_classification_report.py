"""
ARCH-0490..ARCH-0514 — Tests for generate_classification_report.py.
All tests use synthetic data only. No personal files or reports/ touched.
"""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.generate_classification_report as gcr


# ── helpers ───────────────────────────────────────────────────────────────────

def _minimal_data(**kwargs):
    base = {
        "summary": {
            "source": "/tmp/test",
            "total_files": 2,
            "categories_count": {"Documents": 1, "Images": 1},
            "location_policy_counts": {"classify_only": 1, "keep_in_place": 1},
            "low_confidence_count": 0,
        },
        "classifications": [
            {"relative_path": "a.pdf", "filename": "a.pdf", "extension": ".pdf",
             "size_bytes": 512, "category": "Documents", "confidence": 0.70,
             "signals": ["extension:.pdf"], "location_policy": "classify_only",
             "context_bound": False, "suggested_folder": "Documents",
             "dry_run_only": True},
            {"relative_path": "sub/b.jpg", "filename": "b.jpg", "extension": ".jpg",
             "size_bytes": 256, "category": "Images", "confidence": 0.72,
             "signals": ["extension:.jpg", "context:inside_existing_folder"],
             "location_policy": "keep_in_place", "context_bound": True,
             "suggested_folder": None, "dry_run_only": True},
        ],
        "errors": [],
    }
    base.update(kwargs)
    return base


def _full_data():
    d = _minimal_data()
    d["metadata"] = {
        "schema_version": "1.0",
        "generated_at_iso": "2026-01-01T00:00:00+00:00",
        "tool": "classify_inventory.py",
        "mode": "dry_run_classification",
        "input_tool": "inventory_readonly.py",
        "input_schema_version": "1.0",
    }
    d["summary"]["confidence_buckets"] = {"high": 1, "medium": 1, "low": 0}
    d["summary"]["root_file_count"] = 1
    d["summary"]["context_bound_count"] = 1
    return d


# ── ARCH-0492..0495: help ─────────────────────────────────────────────────────

class TestGenerateClassificationReportHelp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        buf = io.StringIO()
        code = 0
        try:
            with patch("sys.argv", ["generate_classification_report.py", "--help"]):
                with redirect_stdout(buf):
                    with redirect_stderr(buf):
                        gcr.main()
        except SystemExit as e:
            code = e.code if e.code is not None else 0
        cls._help = buf.getvalue()
        cls._code = code

    def test_help_exits_zero(self):
        """ARCH-0492: --help exits 0."""
        self.assertEqual(self._code, 0, f"--help exited {self._code}")

    def test_help_mentions_json_input(self):
        """ARCH-0493: help mentions JSON input."""
        self.assertIn("json", self._help.lower())

    def test_help_mentions_html_output(self):
        """ARCH-0493: help mentions HTML output."""
        self.assertIn("html", self._help.lower())

    def test_help_mentions_review_only(self):
        """ARCH-0493: help mentions review-only or static."""
        lower = self._help.lower()
        self.assertTrue("review-only" in lower or "static" in lower)

    def test_help_no_destructive_language(self):
        """ARCH-0494: help has no destructive language."""
        lower = self._help.lower()
        for phrase in ("will delete", "will move", "will rename",
                       "cancella automaticamente", "sposta automaticamente"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)

    def test_help_no_cloud_api(self):
        """ARCH-0495: help has no cloud/API/n8n/MCP."""
        lower = self._help.lower()
        for phrase in ("api_key", "access_token", "n8n", " mcp", "s3://"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)


# ── ARCH-0502/0503: metadata rendering ───────────────────────────────────────

class TestBuildHtmlMetadata(unittest.TestCase):

    def test_metadata_fields_rendered(self):
        """ARCH-0502: JSON with metadata renders all metadata fields."""
        result = gcr.build_html(_full_data())
        self.assertIn("1.0", result)
        self.assertIn("2026-01-01T00:00:00", result)
        self.assertIn("classify_inventory.py", result)
        self.assertIn("inventory_readonly.py", result)

    def test_mode_dry_run_shows_italian_label(self):
        """ARCH-0500: mode dry_run_classification shows Italian label."""
        result = gcr.build_html(_full_data())
        self.assertIn("classificazione dry-run", result.lower())

    def test_metadata_section_heading_italian(self):
        """ARCH-0497: metadata section heading is in Italian."""
        result = gcr.build_html(_full_data())
        self.assertIn("Informazioni classificazione", result)

    def test_no_metadata_produces_valid_html(self):
        """ARCH-0503: JSON without metadata still produces valid HTML."""
        result = gcr.build_html(_minimal_data())
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn('<html lang="it">', result)
        self.assertNotIn("Informazioni classificazione", result)

    def test_no_metadata_no_exception(self):
        """ARCH-0501: missing metadata does not raise."""
        try:
            gcr.build_html(_minimal_data())
        except Exception as exc:
            self.fail(f"build_html raised {exc} with missing metadata")


# ── ARCH-0505: confidence_buckets ─────────────────────────────────────────────

class TestBuildHtmlConfidenceBuckets(unittest.TestCase):

    def test_confidence_buckets_rendered(self):
        """ARCH-0505: confidence buckets high/medium/low shown in HTML."""
        result = gcr.build_html(_full_data())
        self.assertIn("Confidenza alta", result)
        self.assertIn("Confidenza media", result)
        self.assertIn("Confidenza bassa", result)

    def test_confidence_buckets_absent_no_error(self):
        """ARCH-0505: missing confidence_buckets silently omitted."""
        result = gcr.build_html(_minimal_data())
        self.assertNotIn("Confidenza alta", result)


# ── ARCH-0508: root_file_count / context_bound_count ─────────────────────────

class TestBuildHtmlRootContext(unittest.TestCase):

    def test_root_file_count_rendered(self):
        """ARCH-0506/0508: root_file_count shown in HTML."""
        result = gcr.build_html(_full_data())
        self.assertIn("File in radice", result)

    def test_context_bound_count_rendered(self):
        """ARCH-0507/0508: context_bound_count shown in HTML."""
        result = gcr.build_html(_full_data())
        self.assertIn("File context-bound", result)

    def test_absent_stats_silently_omitted(self):
        """ARCH-0508: missing counts are silently omitted."""
        result = gcr.build_html(_minimal_data())
        self.assertNotIn("File in radice", result)
        self.assertNotIn("File context-bound", result)


# ── ARCH-0510: lang="it" ──────────────────────────────────────────────────────

class TestBuildHtmlLang(unittest.TestCase):

    def test_lang_it_present(self):
        """ARCH-0509/0510: HTML has lang='it'."""
        result = gcr.build_html(_minimal_data())
        self.assertIn('lang="it"', result)


# ── ARCH-0512: HTML escaping ──────────────────────────────────────────────────

class TestBuildHtmlEscaping(unittest.TestCase):

    def test_source_path_escaped(self):
        """ARCH-0511/0512: source with HTML special chars is escaped."""
        data = _minimal_data()
        data["summary"]["source"] = "/tmp/<test>&path"
        result = gcr.build_html(data)
        self.assertNotIn("<test>", result)
        self.assertIn("&lt;test&gt;", result)

    def test_metadata_tool_escaped(self):
        """ARCH-0511/0512: metadata.tool with HTML chars is escaped."""
        data = _full_data()
        data["metadata"]["tool"] = "<script>alert(1)</script>"
        result = gcr.build_html(data)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_category_name_escaped(self):
        """ARCH-0511/0512: category name with HTML chars is escaped."""
        data = _minimal_data()
        data["summary"]["categories_count"] = {"Doc<ument>s": 1}
        result = gcr.build_html(data)
        self.assertNotIn("Doc<ument>s", result)
        self.assertIn("Doc&lt;ument&gt;s", result)

    def test_classification_path_escaped(self):
        """ARCH-0511/0512: relative_path with HTML chars is escaped."""
        data = _minimal_data()
        data["classifications"][0]["relative_path"] = "a<b>.pdf"
        result = gcr.build_html(data)
        self.assertNotIn("a<b>", result)
        self.assertIn("a&lt;b&gt;", result)


if __name__ == "__main__":
    unittest.main()
