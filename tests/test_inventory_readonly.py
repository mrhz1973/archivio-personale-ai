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
        files, errors, skipped = scan_directory(self.root)
        self.assertEqual(len(files), 2)
        self.assertEqual(errors, [])

    def test_sha256_correct(self):
        content = b"test content"
        self._make_file("x.bin", content)
        files, _, _ = scan_directory(self.root)
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(files[0]["sha256"], expected)

    def test_ignored_file_skipped(self):
        self._make_file("real.txt", b"data")
        self._make_file("Thumbs.db", b"thumb")
        self._make_file("~$temp.docx", b"temp")
        self._make_file("desktop.ini", b"ini")
        files, _, skipped = scan_directory(self.root)
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
        files, _, _ = scan_directory(self.root)
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
        files, _, _ = scan_directory(self.root)
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


if __name__ == "__main__":
    unittest.main()
