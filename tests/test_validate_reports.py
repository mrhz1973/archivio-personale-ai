"""Unit tests for scripts/validate_reports.py — uses temporary files/directories only."""

import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.validate_reports import (
    _DANGEROUS_PATTERNS,
    _REVIEW_ONLY_PHRASES,
    _collect_paths,
    _dangerous_wording,
    _has_html_marker,
    _has_lang_it,
    _has_review_only_wording,
    main,
    validate_file,
)


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

LANG_UPPERCASE = """<!DOCTYPE HTML>
<HTML LANG="IT">
<head><meta charset="utf-8"><title>Report</title></head>
<body><h1>Report</h1><p>Solo revisione.</p></body>
</HTML>"""

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

MINIMAL_VALID = (
    '<!DOCTYPE html>\n'
    '<html lang="it"><body><p>Solo revisione.</p></body></html>'
)

NO_HTML_TAG = (
    '<head><meta charset="utf-8"></head>'
    '<body><p>Solo revisione.</p></body>'
)

NO_BODY_BUT_OK = (
    '<!DOCTYPE html>\n'
    '<html lang="it"><head><title>R</title></head></html>'
    '<p>Solo revisione.</p>'
)


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
            shutil.rmtree(d, ignore_errors=True)


def _capture_main(argv):
    """Run main(argv), capture stdout+stderr, return (code, stdout, stderr)."""
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


# ── validate_file tests ────────────────────────────────────────────────────────

class TestValidateFile(TmpMixin, unittest.TestCase):

    def test_valid_italian_html_is_ok(self):
        path = self._write_tmp(VALID_ITALIAN)
        status, messages = validate_file(path)
        self.assertEqual(status, "OK")
        self.assertEqual(messages, [])

    def test_lang_single_quote_accepted(self):  # ARCH-0607
        path = self._write_tmp(LANG_SINGLE_QUOTE)
        status, _ = validate_file(path)
        self.assertEqual(status, "OK")

    def test_lang_double_quote_accepted(self):  # ARCH-0606
        path = self._write_tmp(VALID_ITALIAN)
        status, _ = validate_file(path)
        self.assertEqual(status, "OK")

    def test_missing_lang_it_fails(self):  # ARCH-0608
        path = self._write_tmp(MISSING_LANG)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("lang" in m for m in messages))

    def test_empty_file_fails_with_clear_message(self):  # ARCH-0611
        path = self._write_tmp(EMPTY_CONTENT)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("empty" in m for m in messages),
                        f"expected 'empty' in messages, got: {messages}")

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

    def test_minimal_valid_html_passes(self):  # ARCH-0610
        path = self._write_tmp(MINIMAL_VALID)
        status, messages = validate_file(path)
        self.assertEqual(status, "OK",
                         f"minimal valid HTML should be OK, got {status} ({messages})")

    def test_no_html_tag_fails(self):  # ARCH-0612
        path = self._write_tmp(NO_HTML_TAG)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("html" in m.lower() or "doctype" in m.lower() for m in messages))

    def test_no_body_but_valid_is_warn(self):  # ARCH-0613
        path = self._write_tmp(NO_BODY_BUT_OK)
        status, messages = validate_file(path)
        self.assertEqual(status, "WARN")
        self.assertTrue(any("body" in m for m in messages))

    def test_uppercase_html_lang_accepted(self):
        path = self._write_tmp(LANG_UPPERCASE)
        status, _ = validate_file(path)
        # Uppercase HTML/LANG should still be detected (review-only wording absent → WARN ok)
        self.assertIn(status, ("OK", "WARN"))


# ── lang helper tests ─────────────────────────────────────────────────────────

class TestHasLangIt(unittest.TestCase):

    def test_double_quote(self):  # ARCH-0606
        self.assertTrue(_has_lang_it('<html lang="it">'))

    def test_single_quote(self):  # ARCH-0607
        self.assertTrue(_has_lang_it("<html lang='it'>"))

    def test_uppercase(self):  # ARCH-0605
        self.assertTrue(_has_lang_it('<HTML LANG="IT">'))

    def test_with_whitespace(self):  # ARCH-0605
        self.assertTrue(_has_lang_it('<html lang = "it">'))

    def test_absent_returns_false(self):  # ARCH-0608
        self.assertFalse(_has_lang_it("<html><body>x</body></html>"))

    def test_other_lang_returns_false(self):
        self.assertFalse(_has_lang_it('<html lang="en">'))


# ── html / doctype marker tests ───────────────────────────────────────────────

class TestHasHtmlMarker(unittest.TestCase):

    def test_doctype_only(self):  # ARCH-0609
        self.assertTrue(_has_html_marker("<!DOCTYPE html><body>x</body>"))

    def test_html_tag_only(self):  # ARCH-0609
        self.assertTrue(_has_html_marker("<html lang='it'><body>x</body>"))

    def test_neither_returns_false(self):  # ARCH-0612
        self.assertFalse(_has_html_marker("<body>x</body>"))

    def test_uppercase_doctype(self):
        self.assertTrue(_has_html_marker("<!DOCTYPE HTML><body>x</body>"))


# ── review-only wording tests ─────────────────────────────────────────────────

class TestReviewOnlyWording(unittest.TestCase):

    def test_solo_revisione(self):  # ARCH-0599
        self.assertTrue(_has_review_only_wording("Questo è solo revisione dei file."))

    def test_review_only_en(self):  # ARCH-0599
        self.assertTrue(_has_review_only_wording("This report is review only."))

    def test_review_only_hyphen(self):  # ARCH-0598/0599
        self.assertTrue(_has_review_only_wording("Mode: review-only."))

    def test_nessuna_cancellazione(self):  # ARCH-0599
        self.assertTrue(_has_review_only_wording("Nessuna cancellazione prevista."))

    def test_nessuna_cancellazione_proposta(self):  # ARCH-0598/0599
        self.assertTrue(_has_review_only_wording("Nessuna cancellazione proposta."))

    def test_solo_suggerimenti(self):  # ARCH-0598/0599
        self.assertTrue(_has_review_only_wording("Solo suggerimenti, decide l'utente."))

    def test_returns_false_when_absent(self):  # ARCH-0600
        self.assertFalse(_has_review_only_wording("Statistiche dei file e categorie."))

    def test_at_least_three_italian_variants_recognized(self):  # ARCH-0599
        italian_variants = [
            "Solo revisione",
            "Nessuna cancellazione",
            "Solo suggerimenti",
            "Nessuna cancellazione proposta",
        ]
        recognized = [v for v in italian_variants if _has_review_only_wording(v)]
        self.assertGreaterEqual(
            len(recognized), 3,
            f"expected at least 3 Italian variants recognized, got {len(recognized)}"
        )

    def test_phrases_list_includes_expected_variants(self):  # ARCH-0598
        expected = (
            "solo revisione",
            "review-only",
            "nessuna cancellazione",
            "nessuna cancellazione proposta",
            "solo suggerimenti",
        )
        for phrase in expected:
            self.assertIn(phrase, _REVIEW_ONLY_PHRASES,
                          f"_REVIEW_ONLY_PHRASES missing {phrase!r}")


# ── dangerous wording unit tests ──────────────────────────────────────────────

class TestDangerousWording(unittest.TestCase):

    def test_plain_cancellazione_automatica_detected(self):  # ARCH-0602
        result = _dangerous_wording("La cancellazione automatica avviene.")
        self.assertIn("cancellazione automatica", result)

    def test_eliminazione_automatica_detected(self):  # ARCH-0602
        result = _dangerous_wording("Eliminazione automatica dei file.")
        self.assertIn("eliminazione automatica", result)

    def test_spostamento_automatico_detected(self):  # ARCH-0602
        result = _dangerous_wording("Spostamento automatico dei duplicati.")
        self.assertIn("spostamento automatico", result)

    def test_rinomina_automatica_detected(self):  # ARCH-0602
        result = _dangerous_wording("Rinomina automatica dei file.")
        self.assertIn("rinomina automatica", result)

    def test_delete_automatically_detected(self):  # ARCH-0602
        result = _dangerous_wording("The tool will delete automatically.")
        self.assertIn("delete automatically", result)

    def test_move_automatically_detected(self):  # ARCH-0602
        result = _dangerous_wording("The tool will move automatically.")
        self.assertIn("move automatically", result)

    def test_rename_automatically_detected(self):  # ARCH-0602
        result = _dangerous_wording("The tool will rename automatically.")
        self.assertIn("rename automatically", result)

    def test_safe_to_delete_detected(self):  # ARCH-0602
        result = _dangerous_wording("These files are safe to delete.")
        self.assertIn("safe to delete", result)

    def test_nessuna_cancellazione_automatica_safe(self):  # ARCH-0603
        result = _dangerous_wording("Nessuna cancellazione automatica.")
        self.assertEqual(result, [])

    def test_non_sposta_automaticamente_safe(self):  # ARCH-0603
        result = _dangerous_wording("Non prevede spostamento automatico.")
        self.assertEqual(result, [])

    def test_senza_rinomina_automatica_safe(self):  # ARCH-0603
        result = _dangerous_wording("Riepilogo senza rinomina automatica dei file.")
        self.assertEqual(result, [])

    def test_no_delete_automatically_safe(self):  # ARCH-0603
        result = _dangerous_wording("This tool will no delete automatically.")
        self.assertEqual(result, [])

    def test_not_delete_automatically_safe(self):  # ARCH-0603
        result = _dangerous_wording("The tool does not delete automatically.")
        self.assertEqual(result, [])

    def test_distant_negation_does_not_mask(self):  # ARCH-0604
        # Negation more than 80 chars before the dangerous match must NOT mask it.
        far_prefix = "Nessuna operazione qui. " + ("padding " * 30)
        text = far_prefix + " cancellazione automatica dei duplicati."
        result = _dangerous_wording(text)
        self.assertIn("cancellazione automatica", result,
                      "distant 'nessuna' must not negate later dangerous wording")

    def test_distant_negation_en_does_not_mask(self):  # ARCH-0604
        far_prefix = "Without any action. " + ("filler text " * 20)
        text = far_prefix + " delete automatically all files."
        result = _dangerous_wording(text)
        self.assertIn("delete automatically", result)

    def test_dangerous_patterns_cover_each_category(self):  # ARCH-0601
        # Sanity: each dangerous category should be represented by a distinct
        # description in _DANGEROUS_PATTERNS.
        descriptions = {desc for _, desc in _DANGEROUS_PATTERNS}
        for required in (
            "cancellazione automatica",
            "eliminazione automatica",
            "spostamento automatico",
            "rinomina automatica",
            "delete automatically",
            "move automatically",
            "rename automatically",
            "safe to delete",
        ):
            self.assertIn(required, descriptions,
                          f"_DANGEROUS_PATTERNS missing category {required!r}")


# ── _collect_paths tests ──────────────────────────────────────────────────────

class TestCollectPaths(TmpMixin, unittest.TestCase):

    def test_empty_argv_uses_defaults(self):
        entries, empty_dirs, err = _collect_paths([])
        self.assertIsNone(err)
        self.assertEqual(empty_dirs, [])
        self.assertGreater(len(entries), 0)
        # entries from defaults are not explicit
        self.assertFalse(any(is_explicit for _, is_explicit in entries))

    def test_explicit_missing_path_returns_error(self):  # ARCH-0617
        entries, empty_dirs, err = _collect_paths(["/no/such/file.html"])
        self.assertEqual(entries, [])
        self.assertEqual(empty_dirs, [])
        self.assertIsNotNone(err)
        self.assertIn("not found", err)

    def test_empty_directory_reports_empty_dir(self):  # ARCH-0616
        d = self._make_tmpdir()
        entries, empty_dirs, err = _collect_paths([d])
        self.assertIsNone(err)
        self.assertEqual(entries, [])
        self.assertEqual(empty_dirs, [d])

    def test_directory_order_is_stable_and_sorted(self):  # ARCH-0615
        d = self._make_tmpdir()
        # Create files in non-alphabetical order
        names = ["zeta.html", "alpha.html", "mid.html"]
        for n in names:
            with open(os.path.join(d, n), "w", encoding="utf-8") as f:
                f.write(VALID_ITALIAN)
        # Plus a subdirectory with files
        sub = os.path.join(d, "sub")
        os.makedirs(sub)
        for n in ("gamma.html", "beta.html"):
            with open(os.path.join(sub, n), "w", encoding="utf-8") as f:
                f.write(VALID_ITALIAN)

        first, _, _ = _collect_paths([d])
        second, _, _ = _collect_paths([d])
        self.assertEqual(first, second, "_collect_paths must be deterministic")

        # Within the root dir, names sorted alphabetically; subdir comes after files
        rels = [os.path.basename(p) for p, _ in first]
        # Files in root sorted; subdir files come after due to os.walk order
        # Root-level slice (first three) must be sorted
        root_files = [r for r in rels if r in names]
        self.assertEqual(root_files, sorted(names))

    def test_mixed_file_and_directory_args_deterministic(self):  # ARCH-0614/0615
        d = self._make_tmpdir()
        for n in ("c.html", "a.html", "b.html"):
            with open(os.path.join(d, n), "w", encoding="utf-8") as f:
                f.write(VALID_ITALIAN)
        standalone = self._write_tmp(VALID_ITALIAN)
        first, _, _ = _collect_paths([standalone, d])
        second, _, _ = _collect_paths([standalone, d])
        self.assertEqual(first, second)
        # Standalone file first (argv order), then dir contents sorted
        self.assertEqual(first[0][0], standalone)
        dir_names = [os.path.basename(p) for p, _ in first[1:]]
        self.assertEqual(dir_names, sorted(dir_names))


# ── CLI / main tests ───────────────────────────────────────────────────────────

class TestMain(TmpMixin, unittest.TestCase):

    def test_explicit_nonexistent_path_returns_2(self):  # ARCH-0617
        code, _, _ = _capture_main(["/nonexistent/path/report.html"])
        self.assertEqual(code, 2)

    def test_valid_file_returns_0(self):  # ARCH-0618
        path = self._write_tmp(VALID_ITALIAN)
        code, _, _ = _capture_main([path])
        self.assertEqual(code, 0)

    def test_failing_file_returns_1(self):
        path = self._write_tmp(MISSING_LANG)
        code, _, _ = _capture_main([path])
        self.assertEqual(code, 1)

    def test_default_mode_no_reports_returns_0(self):
        import scripts.validate_reports as vr
        original = vr.DEFAULT_PATHS[:]
        vr.DEFAULT_PATHS[:] = ["/no/a.html", "/no/b.html", "/no/c.html"]
        try:
            code, _, _ = _capture_main([])
            self.assertEqual(code, 0)
        finally:
            vr.DEFAULT_PATHS[:] = original

    def test_directory_recursive_finds_html(self):  # ARCH-0619
        d = self._make_tmpdir()
        subdir = os.path.join(d, "sub")
        os.makedirs(subdir)
        p1 = os.path.join(d, "report1.html")
        p2 = os.path.join(subdir, "report2.html")
        for p in (p1, p2):
            with open(p, "w", encoding="utf-8") as f:
                f.write(VALID_ITALIAN)
        code, _, _ = _capture_main([d])
        self.assertEqual(code, 0)

    def test_directory_with_failing_html_returns_1(self):
        d = self._make_tmpdir()
        p = os.path.join(d, "bad.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(MISSING_LANG)
        code, _, _ = _capture_main([d])
        self.assertEqual(code, 1)

    def test_directory_with_dangerous_html_returns_1(self):  # ARCH-0620
        d = self._make_tmpdir()
        p = os.path.join(d, "bad.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(DANGEROUS_AUTO_DELETE)
        code, _, _ = _capture_main([d])
        self.assertEqual(code, 1)

    def test_mix_file_and_directory(self):
        d = self._make_tmpdir()
        dir_file = os.path.join(d, "dir_report.html")
        with open(dir_file, "w", encoding="utf-8") as f:
            f.write(VALID_ITALIAN)
        standalone = self._write_tmp(VALID_ITALIAN)
        code, _, _ = _capture_main([standalone, d])
        self.assertEqual(code, 0)

    def test_summary_counts_all_ok(self):  # ARCH-0622
        """Two valid files → Checked:2 OK:2 Warnings:0 Errors:0 + 'Validation passed.'"""
        p1 = self._write_tmp(VALID_ITALIAN)
        p2 = self._write_tmp(VALID_ITALIAN)
        code, output, _ = _capture_main([p1, p2])
        self.assertEqual(code, 0)
        self.assertIn("Checked: 2", output)
        self.assertIn("OK: 2", output)
        self.assertIn("Warnings: 0", output)
        self.assertIn("Errors: 0", output)
        self.assertIn("Validation passed.", output)

    def test_summary_counts_with_errors(self):  # ARCH-0622
        good = self._write_tmp(VALID_ITALIAN)
        bad = self._write_tmp(MISSING_LANG)
        code, output, _ = _capture_main([good, bad])
        self.assertEqual(code, 1)
        self.assertIn("Checked: 2", output)
        self.assertIn("OK: 1", output)
        self.assertIn("Errors: 1", output)
        self.assertIn("Validation FAILED.", output)

    def test_summary_printed_on_warn_only(self):  # ARCH-0622
        path = self._write_tmp(NO_REVIEW_WORDING)
        code, output, _ = _capture_main([path])
        # No errors → code 0, but Warnings count should be 1 and summary printed
        self.assertEqual(code, 0)
        self.assertIn("Checked: 1", output)
        self.assertIn("Warnings: 1", output)
        self.assertIn("Validation passed.", output)

    def test_directory_valid_but_no_html_returns_0(self):
        d = self._make_tmpdir()
        with open(os.path.join(d, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("not html")
        code, output, _ = _capture_main([d])
        self.assertEqual(code, 0)
        self.assertIn("no HTML files found", output)

    def test_safe_negated_wording_not_dangerous(self):
        path = self._write_tmp(SAFE_NEGATED)
        status, messages = validate_file(path)
        self.assertFalse(any("dangerous" in m for m in messages))

    def test_safe_to_delete_without_context_fails(self):
        content = (
            '<!DOCTYPE html><html lang="it"><body>'
            "<p>These files are safe to delete. Solo revisione.</p>"
            "</body></html>"
        )
        path = self._write_tmp(content)
        status, messages = validate_file(path)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("dangerous" in m for m in messages))

    def test_help_flag_returns_0(self):  # ARCH-0593
        code, _, _ = _capture_main(["--help"])
        self.assertEqual(code, 0)

    def test_help_short_flag_returns_0(self):  # ARCH-0593
        code, _, _ = _capture_main(["-h"])
        self.assertEqual(code, 0)

    def test_help_output_contains_usage(self):
        code, output, _ = _capture_main(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("Usage", output)
        self.assertIn("Exit codes", output)

    def test_help_output_contains_read_only_wording(self):  # ARCH-0594
        _, output, _ = _capture_main(["--help"])
        lower = output.lower()
        self.assertIn("read-only", lower)
        # no browser
        self.assertTrue("does not open a browser" in lower or "no browser" in lower,
                        f"help must mention no-browser; got:\n{output}")
        # no file modification
        self.assertIn("does not modify", lower)

    def test_help_output_no_api_cloud_n8n_mcp(self):  # ARCH-0595
        _, output, _ = _capture_main(["--help"])
        lower = output.lower()
        forbidden_as_operations = (
            "api_key", "access_token", "n8n", "mcp server",
            "cloud upload", "s3://", "gcs://",
        )
        for phrase in forbidden_as_operations:
            self.assertNotIn(phrase, lower,
                             f"help must not contain {phrase!r} as allowed action")

    def test_help_output_does_not_suggest_auto_open(self):  # ARCH-0596
        _, output, _ = _capture_main(["--help"])
        lower = output.lower()
        for phrase in ("invoke-item", "webbrowser", "auto-open", "start ./reports"):
            self.assertNotIn(phrase, lower,
                             f"help must not suggest {phrase!r}")

    def test_help_output_no_undenied_destructive_language(self):  # ARCH-0597
        _, output, _ = _capture_main(["--help"])
        lower = output.lower()
        # Destructive verbs must only appear in a denied context (e.g. "does not modify, create, or delete files")
        # Check that any occurrence of these verbs is preceded by a negation in the same line.
        destructive_terms = ("delete", "move", "rename", "cancellare", "spostare", "rinominare")
        negation_re = re.compile(
            r"\b(not|no|never|does not|do not|without|senza|non|nessuna?)\b",
            re.IGNORECASE,
        )
        for line in output.splitlines():
            lline = line.lower()
            for term in destructive_terms:
                if term in lline:
                    self.assertRegex(
                        line, negation_re,
                        f"destructive term {term!r} not negated in help line: {line!r}"
                    )

    def test_directory_recursive_deterministic_order(self):
        d = self._make_tmpdir()
        subdir = os.path.join(d, "b_sub")
        os.makedirs(subdir)
        for name in ("z_report.html", "a_report.html", os.path.join("b_sub", "m_report.html")):
            p = os.path.join(d, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(VALID_ITALIAN)

        def _collect():
            _, output, _ = _capture_main([d])
            return [ln.split(None, 1)[1].strip()
                    for ln in output.splitlines() if ln.startswith("[OK]")]

        first = _collect()
        second = _collect()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)


# ── static safety: validator source must not import side-effect modules ───────

class TestValidatorSourceSafety(unittest.TestCase):
    """ARCH-0624: validate_reports.py must not import/use side-effecting modules."""

    @classmethod
    def setUpClass(cls):
        src_path = Path(__file__).parent.parent / "scripts" / "validate_reports.py"
        cls._src = src_path.read_text(encoding="utf-8")

    def _assert_not_imported(self, module):
        # Match `import X`, `from X import`, but allow X inside string/comment-only mentions.
        bad = re.compile(rf"^\s*(import|from)\s+{re.escape(module)}\b", re.MULTILINE)
        self.assertIsNone(bad.search(self._src),
                          f"validate_reports.py must not import {module!r}")

    def test_no_webbrowser_import(self):
        self._assert_not_imported("webbrowser")

    def test_no_subprocess_import(self):
        self._assert_not_imported("subprocess")

    def test_no_requests_import(self):
        self._assert_not_imported("requests")

    def test_no_urllib_import(self):
        self._assert_not_imported("urllib")
        self._assert_not_imported("urllib.request")
        self._assert_not_imported("urllib.parse")

    def test_no_socket_import(self):
        self._assert_not_imported("socket")

    def test_no_open_write_calls(self):
        # Reject open(..., "w") / open(..., 'w') and write/append modes.
        bad = re.compile(r"""open\s*\([^)]*['"][wa][b+t]*['"]""")
        self.assertIsNone(bad.search(self._src),
                          "validate_reports.py must not call open(..., 'w'|'a')")

    def test_no_mkdir_calls(self):
        for pattern in (r"\bos\.mkdir\b", r"\bos\.makedirs\b", r"\.mkdir\("):
            self.assertIsNone(re.search(pattern, self._src),
                              f"validate_reports.py must not call {pattern}")

    def test_no_shell_open_commands(self):
        # Match shell open helpers as code calls, not as strings inside denial text.
        for word in ("Invoke-Item", "os.startfile"):
            self.assertNotIn(word, self._src,
                             f"validate_reports.py must not reference {word!r}")
        # 'start' is a common word — only reject obvious shell-open uses.
        self.assertIsNone(re.search(r"subprocess\.[^(]+\(['\"]start\b", self._src))


if __name__ == "__main__":
    unittest.main()
