"""Shared test helpers. All helpers use temporary directories only."""

import json
import os
import shutil
import tempfile
import unittest


class TmpDirMixin(unittest.TestCase):
    """Mixin providing a per-test temp directory with cleanup."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="archivio_test_")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _path(self, name):
        return os.path.join(self._tmpdir, name)

    def _out(self, name):
        return self._path(name)

    def _write_json(self, data, name):
        p = self._path(name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return p
