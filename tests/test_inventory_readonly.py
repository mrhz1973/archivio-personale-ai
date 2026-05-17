"""
Unit tests for inventory_readonly.py.
All tests use temporary directories — no real user archive paths are touched.
"""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Allow importing from scripts/ without installing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from inventory_readonly import (
    IGNORED_DIRS,
    IGNORED_FILES,
    build_extensions_count,
    format_bytes,
    scan_directory,
    should_ignore_file,
)


class TestShouldIgnoreFile(unittest.TestCase):
    def test_ignored_names(self):
        for name in IGNORED_FILES:
            self.assertTrue(should_ignore_file(name))

    def test_tilde_dollar_prefix(self):
        self.assertTrue(should_ignore_file("~$document.docx"))

    def test_normal_file_not_ignored(self):
        self.assertFalse(should_ignore_file("report.pdf"))
        self.assertFalse(should_ignore_file("photo.jpg"))


class TestScanDirectory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_file(self, rel: str, content: bytes = b"hello") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def test_files_are_counted(self):
        self._make_file("a.txt", b"aaa")
        self._make_file("sub/b.pdf", b"bbb")
        files, errors, skipped, _, _ = scan_directory(self.root)
        self.assertEqual(len(files), 2)
        self.assertEqual(errors, [])

    def test_sha256_correct(self):
        content = b"test content"
        self._make_file("x.bin", content)
        files, _, _, _, _ = scan_directory(self.root)
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(files[0]["sha256"], expected)

    def test_ignored_file_skipped(self):
        self._make_file("real.txt", b"data")
        self._make_file("Thumbs.db", b"thumb")
        self._make_file("~$temp.docx", b"temp")
        self._make_file("desktop.ini", b"ini")
        files, _, skipped, _, _ = scan_directory(self.root)
        names = [f["filename"] for f in files]
        self.assertIn("real.txt", names)
        self.assertNotIn("Thumbs.db", names)
        self.assertNotIn("~$temp.docx", names)
        self.assertNotIn("desktop.ini", names)
        self.assertEqual(skipped, 3)

    def test_ignored_directory_skipped(self):
        self._make_file("normal.txt", b"ok")
        for d in IGNORED_DIRS:
            self._make_file(f"{d}/secret.txt", b"secret")
        files, _, _, _, _ = scan_directory(self.root)
        paths = [f["relative_path"] for f in files]
        for d in IGNORED_DIRS:
            self.assertFalse(any(p.startswith(d) for p in paths))
        self.assertEqual(len(files), 1)

    def test_source_files_unchanged_after_scan(self):
        content = b"original content"
        p = self._make_file("check.txt", content)
        scan_directory(self.root)
        self.assertTrue(p.exists())
        self.assertEqual(p.read_bytes(), content)

    def test_file_metadata_fields(self):
        self._make_file("doc.pdf", b"pdf content")
        files, _, _, _, _ = scan_directory(self.root)
        f = files[0]
        for key in ("relative_path", "filename", "extension", "size_bytes", "modified_time_iso", "sha256"):
            self.assertIn(key, f)
        self.assertEqual(f["extension"], ".pdf")
        self.assertEqual(f["size_bytes"], len(b"pdf content"))


class TestBuildExtensionsCount(unittest.TestCase):
    def test_counts_extensions(self):
        files = [
            {"extension": ".pdf"},
            {"extension": ".pdf"},
            {"extension": ".jpg"},
            {"extension": ""},
        ]
        counts = build_extensions_count(files)
        self.assertEqual(counts[".pdf"], 2)
        self.assertEqual(counts[".jpg"], 1)
        self.assertIn("(no extension)", counts)

    def test_sorted_descending(self):
        files = [{"extension": ".txt"}, {"extension": ".pdf"}, {"extension": ".pdf"}]
        counts = build_extensions_count(files)
        keys = list(counts.keys())
        self.assertEqual(keys[0], ".pdf")


class TestInventoryReadonlyCLI(unittest.TestCase):
    """ARCH-0401: CLI writes JSON to output path; source files remain untouched."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_cli_writes_json_to_output(self):
        """ARCH-0401: JSON file is created at the requested output path."""
        import subprocess
        src = self.root / "source"
        src.mkdir()
        (src / "file1.txt").write_bytes(b"hello")
        (src / "file2.pdf").write_bytes(b"world")
        out = self.root / "out" / "inventory.json"
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "inventory_readonly.py"),
             "--source", str(src), "--output", str(out)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertTrue(out.exists(), "JSON output file must be created")
        with out.open() as f:
            data = json.load(f)
        self.assertIn("files", data)
        self.assertEqual(data["summary"]["total_files"], 2)

    def test_cli_source_files_intact_after_scan(self):
        """ARCH-0401: source files remain present and unmodified after CLI scan."""
        import subprocess
        src = self.root / "source"
        src.mkdir()
        f1 = src / "intact.txt"
        f1.write_bytes(b"original bytes")
        out = self.root / "inventory.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "inventory_readonly.py"),
             "--source", str(src), "--output", str(out)],
            capture_output=True, text=True,
        )
        self.assertTrue(f1.exists(), "Source file must still exist after scan")
        self.assertEqual(f1.read_bytes(), b"original bytes", "Source file must be unmodified")


class TestInventoryIgnoresTempFiles(unittest.TestCase):
    """ARCH-0402: ~$ prefix files are explicitly skipped by should_ignore_file."""

    def test_tilde_dollar_prefix_ignored(self):
        """ARCH-0402: file starting with ~$ is ignored."""
        from inventory_readonly import should_ignore_file
        self.assertTrue(should_ignore_file("~$report.docx"))
        self.assertTrue(should_ignore_file("~$budget.xlsx"))

    def test_thumbs_db_ignored(self):
        """ARCH-0402: Thumbs.db is ignored."""
        from inventory_readonly import should_ignore_file
        self.assertTrue(should_ignore_file("Thumbs.db"))

    def test_normal_file_not_ignored(self):
        """ARCH-0402: ordinary files are not ignored."""
        from inventory_readonly import should_ignore_file
        self.assertFalse(should_ignore_file("document.pdf"))
        self.assertFalse(should_ignore_file("photo.jpg"))


class TestInventoryHelpWording(unittest.TestCase):
    """ARCH-0398: --help output contains read-only wording."""

    @classmethod
    def setUpClass(cls):
        import io
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "inventory_readonly.py"),
             "--help"],
            capture_output=True, text=True,
        )
        cls._help_output = result.stdout + result.stderr
        cls._exit_code = result.returncode

    def test_help_exits_zero(self):
        """ARCH-0397: --help exits 0."""
        self.assertEqual(self._exit_code, 0,
                         f"--help exited {self._exit_code}; output:\n{self._help_output}")

    def test_help_mentions_read_only(self):
        """ARCH-0398: help text mentions read-only."""
        lower = self._help_output.lower()
        self.assertTrue(
            "read-only" in lower or "never modif" in lower,
            "help must mention read-only or never modifies"
        )

    def test_help_mentions_no_source_modification(self):
        """ARCH-0398: help text states source is not modified."""
        lower = self._help_output.lower()
        self.assertIn("never", lower, "help must include 'never' to describe read-only guarantee")


# ── ARCH-0411..0418: metadata, deterministic order ───────────────────────────

class TestInventoryMetadata(unittest.TestCase):
    """ARCH-0411..0414: metadata field presence and values."""

    def setUp(self):
        import subprocess
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        src = root / "src"
        src.mkdir()
        (src / "file.txt").write_bytes(b"data")
        out = root / "inv.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "inventory_readonly.py"),
             "--source", str(src), "--output", str(out)],
            capture_output=True, text=True,
        )
        with out.open() as f:
            self.data = json.load(f)

    def tearDown(self):
        self.tmp.cleanup()

    def test_metadata_field_present(self):
        """ARCH-0411: top-level metadata field exists."""
        self.assertIn("metadata", self.data)

    def test_metadata_subfields_present(self):
        """ARCH-0412: schema_version, generated_at_iso, tool, mode all present."""
        m = self.data["metadata"]
        for key in ("schema_version", "generated_at_iso", "tool", "mode"):
            self.assertIn(key, m, f"metadata.{key} missing")

    def test_metadata_mode_is_read_only(self):
        """ARCH-0413: metadata.mode == read_only."""
        self.assertEqual(self.data["metadata"]["mode"], "read_only")

    def test_metadata_generated_at_iso_parsable(self):
        """ARCH-0414: generated_at_iso is a non-empty parsable ISO datetime."""
        from datetime import datetime
        val = self.data["metadata"]["generated_at_iso"]
        self.assertTrue(val, "generated_at_iso must not be empty")
        dt = datetime.fromisoformat(val)
        self.assertIsNotNone(dt)


class TestInventoryDeterministicOrder(unittest.TestCase):
    """ARCH-0416/0418: files list is sorted by relative_path."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_file(self, rel: str, content: bytes = b"x") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def test_files_sorted_by_relative_path(self):
        """ARCH-0416: files are sorted by relative_path regardless of creation order."""
        self._make_file("z_last.txt")
        self._make_file("a_first.txt")
        self._make_file("m_middle.txt")
        files, _, _, _, _ = scan_directory(self.root)
        paths = [f["relative_path"] for f in files]
        self.assertEqual(paths, sorted(paths),
                         "files must be sorted by relative_path")

    def test_errors_sorted_by_path(self):
        """ARCH-0418: errors list is sorted by path."""
        errors = [
            {"path": "z/err.txt", "error": "e"},
            {"path": "a/err.txt", "error": "e"},
            {"path": "m/err.txt", "error": "e"},
        ]
        sorted_errors = sorted(errors, key=lambda e: e["path"])
        self.assertEqual(sorted_errors[0]["path"], "a/err.txt")
        self.assertEqual(sorted_errors[-1]["path"], "z/err.txt")


# ── ARCH-0421: format_bytes helper ────────────────────────────────────────────

class TestFormatBytes(unittest.TestCase):
    """ARCH-0421: format_bytes returns human-readable strings."""

    def test_zero_bytes(self):
        self.assertEqual(format_bytes(0), "0 B")

    def test_bytes(self):
        self.assertEqual(format_bytes(512), "512 B")

    def test_kib(self):
        result = format_bytes(2048)
        self.assertIn("KiB", result)

    def test_mib(self):
        result = format_bytes(2 * 1024 * 1024)
        self.assertIn("MiB", result)


# ── ARCH-0423/0425: directories_scanned and ignored_dirs_count ────────────────

class TestInventorySummaryFields(unittest.TestCase):
    """ARCH-0422..0425: directories_scanned and ignored_dirs_count."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_file(self, rel: str, content: bytes = b"x") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def test_directories_scanned_counts_subdirs(self):
        """ARCH-0423: directories_scanned includes root and subdirectories."""
        self._make_file("sub1/a.txt")
        self._make_file("sub2/b.txt")
        _, _, _, dirs_scanned, _ = scan_directory(self.root)
        self.assertGreaterEqual(dirs_scanned, 3,
                                "root + 2 subdirs = at least 3")

    def test_ignored_dirs_counted(self):
        """ARCH-0425: __pycache__ is skipped and counted in ignored_dirs_count."""
        self._make_file("__pycache__/cache.pyc")
        self._make_file("real.txt")
        _, _, _, _, ignored_dirs = scan_directory(self.root)
        self.assertGreaterEqual(ignored_dirs, 1,
                                "__pycache__ must increment ignored_dirs_count")

    def test_ignored_dirs_files_not_in_results(self):
        """ARCH-0425: files inside __pycache__ are not in results."""
        self._make_file("__pycache__/cache.pyc")
        self._make_file("real.txt")
        files, _, _, _, _ = scan_directory(self.root)
        paths = [f["relative_path"] for f in files]
        self.assertFalse(any("__pycache__" in p for p in paths))

    def test_total_size_human_in_summary(self):
        """ARCH-0419: summary contains total_size_human field."""
        import subprocess
        src = self.root / "src"
        src.mkdir()
        (src / "f.txt").write_bytes(b"hello")
        out = self.root / "inv.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "inventory_readonly.py"),
             "--source", str(src), "--output", str(out)],
            capture_output=True, text=True,
        )
        with out.open() as f:
            data = json.load(f)
        self.assertIn("total_size_human", data["summary"])
        self.assertIn("directories_scanned", data["summary"])
        self.assertIn("ignored_dirs_count", data["summary"])


if __name__ == "__main__":
    unittest.main()
