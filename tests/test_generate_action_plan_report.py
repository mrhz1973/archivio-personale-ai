"""
ARCH-0540..ARCH-0564 — Tests for generate_action_plan_report.py.
All tests use synthetic data only. No personal files or reports/ touched.
"""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.generate_action_plan_report as gapr


# ── helpers ───────────────────────────────────────────────────────────────────

def _minimal_data(**kwargs):
    base = {
        "summary": {
            "source": "/tmp/test",
            "total_files": 2,
            "root_sort_candidates_count": 1,
            "duplicate_groups_count": 1,
            "duplicate_files_count": 2,
            "keep_in_place_count": 1,
            "potential_reclaimable_bytes": 512,
            "duplicate_priority_counts": {"manual_review": 1},
            "dry_run_only": True,
        },
        "root_sort_candidates": [
            {"relative_path": "photo.jpg", "category": "Images", "confidence": 0.70,
             "proposed_destination_relative_path": "Foto/photo.jpg",
             "status": "requires_manual_approval", "dry_run_only": True},
        ],
        "duplicate_groups": [
            {"sha256": "abc123", "count": 2, "total_size_bytes": 1024,
             "potential_reclaimable_bytes": 512, "status": "review_only",
             "review_priority": "manual_review", "review_priority_reason": "test",
             "dry_run_only": True,
             "files": [
                 {"relative_path": "a/f.pdf", "size_bytes": 512,
                  "category": "Documents", "location_policy": "keep_in_place",
                  "context_bound": True, "top_level_folder": "a"},
                 {"relative_path": "b/f.pdf", "size_bytes": 512,
                  "category": "Documents", "location_policy": "keep_in_place",
                  "context_bound": True, "top_level_folder": "b"},
             ]},
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
        "tool": "generate_action_plan.py",
        "mode": "review_only_action_plan",
        "inventory_tool": "inventory_readonly.py",
        "classifications_tool": "classify_inventory.py",
        "inventory_schema_version": "1.0",
        "classifications_schema_version": "1.0",
    }
    d["summary"]["potential_reclaimable_human"] = "512.0 B"
    return d


# ── ARCH-0542..0545: help ─────────────────────────────────────────────────────

class TestGenerateActionPlanReportHelp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        buf = io.StringIO()
        code = 0
        try:
            with patch("sys.argv", ["generate_action_plan_report.py", "--help"]):
                with redirect_stdout(buf):
                    with redirect_stderr(buf):
                        gapr.main()
        except SystemExit as e:
            code = e.code if e.code is not None else 0
        cls._help = buf.getvalue()
        cls._code = code

    def test_help_exits_zero(self):
        """ARCH-0542: --help exits 0."""
        self.assertEqual(self._code, 0, f"--help exited {self._code}")

    def test_help_mentions_json_input(self):
        """ARCH-0543: help mentions JSON input."""
        self.assertIn("json", self._help.lower())

    def test_help_mentions_html_output(self):
        """ARCH-0543: help mentions HTML output."""
        self.assertIn("html", self._help.lower())

    def test_help_mentions_review_only(self):
        """ARCH-0543: help mentions review-only or static."""
        lower = self._help.lower()
        self.assertTrue("review-only" in lower or "static" in lower)

    def test_help_no_destructive_language(self):
        """ARCH-0544: help has no destructive language."""
        lower = self._help.lower()
        for phrase in ("will delete", "will move", "will rename",
                       "cancella automaticamente", "sposta automaticamente"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)

    def test_help_no_cloud_api(self):
        """ARCH-0545: help has no cloud/API/n8n/MCP."""
        lower = self._help.lower()
        for phrase in ("api_key", "access_token", "n8n", " mcp", "s3://"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lower)


# ── ARCH-0552/0553: metadata rendering ───────────────────────────────────────

class TestBuildHtmlMetadata(unittest.TestCase):

    def test_metadata_fields_rendered(self):
        """ARCH-0552: JSON with metadata renders all key fields."""
        result = gapr.build_html(_full_data())
        self.assertIn("1.0", result)
        self.assertIn("2026-01-01T00:00:00", result)
        self.assertIn("generate_action_plan.py", result)
        self.assertIn("inventory_readonly.py", result)
        self.assertIn("classify_inventory.py", result)

    def test_mode_review_only_shows_italian_label(self):
        """ARCH-0550: mode review_only_action_plan shows Italian label."""
        result = gapr.build_html(_full_data())
        self.assertIn("piano azioni solo revisione", result.lower())

    def test_metadata_section_heading_italian(self):
        """ARCH-0547: metadata section heading is in Italian."""
        result = gapr.build_html(_full_data())
        self.assertIn("Informazioni piano azioni", result)

    def test_no_metadata_produces_valid_html(self):
        """ARCH-0553: JSON without metadata still produces valid HTML."""
        result = gapr.build_html(_minimal_data())
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn('<html lang="it">', result)
        self.assertNotIn("Informazioni piano azioni", result)

    def test_no_metadata_no_exception(self):
        """ARCH-0551: missing metadata does not raise."""
        try:
            gapr.build_html(_minimal_data())
        except Exception as exc:
            self.fail(f"build_html raised {exc} with missing metadata")


# ── ARCH-0556/0557: potential_reclaimable_human ───────────────────────────────

class TestBuildHtmlReclaimable(unittest.TestCase):

    def test_reclaimable_human_shown_when_present(self):
        """ARCH-0554/0556: potential_reclaimable_human is rendered."""
        result = gapr.build_html(_full_data())
        self.assertIn("512.0 B", result)

    def test_reclaimable_fallback_to_bytes(self):
        """ARCH-0555/0557: fallback to potential_reclaimable_bytes when human absent."""
        data = _minimal_data()
        data["summary"]["potential_reclaimable_bytes"] = 2048
        result = gapr.build_html(data)
        self.assertIn("2.0 KB", result)


# ── ARCH-0559: reclaimable/review wording ─────────────────────────────────────

class TestBuildHtmlReviewWording(unittest.TestCase):

    def test_reclaimable_theoretical_wording(self):
        """ARCH-0558/0559: 'spazio recuperabile solo teorico' present."""
        result = gapr.build_html(_minimal_data())
        self.assertIn("solo teorico", result.lower())

    def test_no_deletion_proposed_wording(self):
        """ARCH-0559: 'nessuna cancellazione è proposta' present."""
        result = gapr.build_html(_minimal_data())
        lower = result.lower()
        self.assertIn("nessuna cancellazione", lower)

    def test_manual_review_wording(self):
        """ARCH-0559: 'revisione manuale' present."""
        result = gapr.build_html(_minimal_data())
        self.assertIn("revisione manuale", result.lower())


# ── ARCH-0561: lang="it" ──────────────────────────────────────────────────────

class TestBuildHtmlLang(unittest.TestCase):

    def test_lang_it_present(self):
        """ARCH-0560/0561: HTML has lang='it'."""
        result = gapr.build_html(_minimal_data())
        self.assertIn('lang="it"', result)


# ── ARCH-0563: HTML escaping ──────────────────────────────────────────────────

class TestBuildHtmlEscaping(unittest.TestCase):

    def test_source_escaped(self):
        """ARCH-0562/0563: source with HTML chars is escaped."""
        data = _minimal_data()
        data["summary"]["source"] = "/tmp/<test>&path"
        result = gapr.build_html(data)
        self.assertNotIn("<test>", result)
        self.assertIn("&lt;test&gt;", result)

    def test_metadata_tool_escaped(self):
        """ARCH-0562/0563: metadata.tool with HTML chars is escaped in the metadata table."""
        data = _full_data()
        data["metadata"]["tool"] = "<xss>alert(1)</xss>"
        result = gapr.build_html(data)
        self.assertNotIn("<xss>", result)
        self.assertIn("&lt;xss&gt;", result)

    def test_candidate_path_escaped(self):
        """ARCH-0562/0563: sort candidate relative_path with HTML chars is escaped."""
        data = _minimal_data()
        data["root_sort_candidates"][0]["relative_path"] = "a<b>.jpg"
        result = gapr.build_html(data)
        self.assertNotIn("a<b>", result)
        self.assertIn("a&lt;b&gt;", result)

    def test_duplicate_group_sha_not_raw_script(self):
        """ARCH-0562: duplicate group JSON embedded without raw </script> tag."""
        data = _minimal_data()
        data["duplicate_groups"][0]["sha256"] = "</script><script>alert(1)"
        result = gapr.build_html(data)
        self.assertNotIn("</script><script>", result)


if __name__ == "__main__":
    unittest.main()
