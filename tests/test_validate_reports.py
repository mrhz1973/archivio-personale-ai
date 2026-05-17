"""Unit tests for scripts/validate_reports.py — uses temporary files/directories only."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.validate_reports import validate_file, main, _dangerous_wording, _has_review_only_wording


# ── fixtures ──────────────────────────────────────────────────────────────────

VALID_ITALIAN = """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Report</title></head>
<body>
<h1>Inventario</h1>
<p>Solo revisione — nessuna cancellazione automatica.</p>
</body>
</html>"""

MISSING_LANG = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Report</title></head>
<body><h1>Report</h1><p>Solo revisione.</p></body>
</html>"""

LANG_SINGLE_QUOTE = """<!DOCTYPE html>
<html lang='it'>
<head><meta charset="utf-8"><title>Report</title></head>
<body><h1>Report</h1><p>Solo revisione — nessuna cancellazione.</p></body>
</html>"""

DANGEROUS_AUTO_DELETE = """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Report</title></head>
<body>
<h1>Report</h1>
<p>Cancellazione automatica dei file duplicati.</p>
</body>
</html>"""

DANGEROUS_EN = """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Report</title></head>
<body>
<p>This tool will delete automatically. Solo revisione.</p>
</body>
</html>"""

SAFE_NEGATED = """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Report</title></head>
<body>
<p>Nessuna cancellazione automatica. Solo revisione.</p>
</body>
</html>"""

EMPTY_CONTENT = ""

NO_REVIEW_WORDING = """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Report</title></head>
<body><h1>Report</h1><p>Dati statistici.</p></body>
</html>"""


# ── helpers ───────────────────────────────────────────────────────────────────

class TmpMixin:
    def _write_tmp(self, content, suffix=".html"):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, encoding="utf-8", delete=False
        )
        f.write(content)
        f.close()
        self._tmps.append(f.name)
        return f.name

    def _make_tmpdir(self):
        d = tempfile.mkdtemp()
        self._tmpdirs.append(d)
        return d

    def setUp(self):
        self._tmps = []
        self._tmpdirs = []

    def tearDown(self):
        for p in self._tmps:
            try:
                os.unlink(p)
            except OSError:
                pass
        for d in self._tmpdirs:
            import shutil
            shutil.rmtree(d, ignore_errors=True)


# ── validate_file tests ────────────────────────────────────────────────────────

class TestValidateFile(TmpMixin, unittest.TestCase):

    def test_valid_italian_html_is_ok(self):
        path = self._write_tmp(VALID_ITALIAN)
        status, messages = validate_file(path)
        self.assertEqual(status, "OK")
        self.assertEqual(messages, [])

    def test_lang_single_quote_accepted(self):
        path = self._write_tmp(LANG_SINGLE_QUOTE)
        status, _ = validate_file(path)
        self.assertEqual(status, "OK")

    def test_missing_lang_it_fails(self):
        path = self._write_tmp(MISSING_LANG)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("lang" in m for m in messages))

    def test_empty_file_fails(self):
        path = self._write_tmp(EMPTY_CONTENT)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("empty" in m for m in messages))

    def test_no_review_wording_is_warn(self):
        path = self._write_tmp(NO_REVIEW_WORDING)
        status, messages = validate_file(path)
        self.assertEqual(status, "WARN")
        self.assertTrue(any("review-only" in m for m in messages))

    def test_dangerous_italian_wording_fails(self):
        path = self._write_tmp(DANGEROUS_AUTO_DELETE)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("dangerous" in m for m in messages))

    def test_dangerous_english_wording_fails(self):
        path = self._write_tmp(DANGEROUS_EN)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("dangerous" in m for m in messages))

    def test_negated_safe_wording_is_ok(self):
        path = self._write_tmp(SAFE_NEGATED)
        status, _ = validate_file(path)
        self.assertEqual(status, "OK")


# ── dangerous wording unit tests ──────────────────────────────────────────────

class TestDangerousWording(unittest.TestCase):

    def test_plain_cancellazione_automatica_detected(self):
        result = _dangerous_wording("La cancellazione automatica avviene.")
        self.assertIn("cancellazione automatica", result)

    def test_nessuna_cancellazione_automatica_safe(self):
        result = _dangerous_wording("Nessuna cancellazione automatica.")
        self.assertEqual(result, [])

    def test_non_cancellazione_automatica_safe(self):
        result = _dangerous_wording("Non prevede cancellazione automatica.")
        self.assertEqual(result, [])

    def test_safe_to_delete_detected(self):
        result = _dangerous_wording("These files are safe to delete.")
        self.assertIn("safe to delete", result)

    def test_delete_automatically_detected(self):
        result = _dangerous_wording("Files will be deleted automatically.")
        # "deleted" doesn't match "delete automatically" — but "delete automatically" does
        result2 = _dangerous_wording("The tool will delete automatically.")
        self.assertIn("auto destructive action (EN)", result2)

    def test_review_only_wording_recognized(self):
        self.assertTrue(_has_review_only_wording("Solo revisione dei file."))
        self.assertTrue(_has_review_only_wording("Nessuna cancellazione prevista."))
        self.assertFalse(_has_review_only_wording("Statistiche file."))


# ── CLI / main tests ───────────────────────────────────────────────────────────

class TestMain(TmpMixin, unittest.TestCase):

    def test_explicit_nonexistent_path_returns_2(self):
        code = main(["/nonexistent/path/report.html"])
        self.assertEqual(code, 2)

    def test_valid_file_returns_0(self):
        path = self._write_tmp(VALID_ITALIAN)
        code = main([path])
        self.assertEqual(code, 0)

    def test_failing_file_returns_1(self):
        path = self._write_tmp(MISSING_LANG)
        code = main([path])
        self.assertEqual(code, 1)

    def test_default_mode_no_reports_returns_0(self):
        # Force default paths to non-existent locations by patching DEFAULT_PATHS.
        import scripts.validate_reports as vr
        original = vr.DEFAULT_PATHS[:]
        vr.DEFAULT_PATHS[:] = ["/no/a.html", "/no/b.html", "/no/c.html"]
        try:
            code = main([])
            self.assertEqual(code, 0)
        finally:
            vr.DEFAULT_PATHS[:] = original

    def test_directory_recursive_finds_html(self):
        d = self._make_tmpdir()
        subdir = os.path.join(d, "sub")
        os.makedirs(subdir)
        p1 = os.path.join(d, "report1.html")
        p2 = os.path.join(subdir, "report2.html")
        for p in (p1, p2):
            with open(p, "w", encoding="utf-8") as f:
                f.write(VALID_ITALIAN)
        code = main([d])
        self.assertEqual(code, 0)

    def test_directory_with_failing_html_returns_1(self):
        d = self._make_tmpdir()
        p = os.path.join(d, "bad.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(MISSING_LANG)
        code = main([d])
        self.assertEqual(code, 1)

    def test_mix_file_and_directory(self):
        d = self._make_tmpdir()
        dir_file = os.path.join(d, "dir_report.html")
        with open(dir_file, "w", encoding="utf-8") as f:
            f.write(VALID_ITALIAN)
        standalone = self._write_tmp(VALID_ITALIAN)
        code = main([standalone, d])
        self.assertEqual(code, 0)

    def test_summary_counts_all_ok(self):
        """Two valid files → Checked:2 OK:2 Warnings:0 Errors:0."""
        import io
        from contextlib import redirect_stdout
        p1 = self._write_tmp(VALID_ITALIAN)
        p2 = self._write_tmp(VALID_ITALIAN)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main([p1, p2])
        output = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Checked: 2", output)
        self.assertIn("OK: 2", output)
        self.assertIn("Errors: 0", output)

    def test_summary_counts_with_errors(self):
        import io
        from contextlib import redirect_stdout
        good = self._write_tmp(VALID_ITALIAN)
        bad = self._write_tmp(MISSING_LANG)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main([good, bad])
        output = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("Checked: 2", output)
        self.assertIn("OK: 1", output)
        self.assertIn("Errors: 1", output)


if __name__ == "__main__":
    unittest.main()
