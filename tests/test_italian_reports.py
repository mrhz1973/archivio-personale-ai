"""
Focused tests verifying Italian UI output for all three HTML report generators.
Tests check: lang="it", key Italian titles, safety wording, no destructive buttons.
All tests use in-memory data only.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_inventory_report import build_html as inventory_html
from generate_classification_report import build_html as classification_html
from generate_action_plan_report import build_html as action_plan_html


MINIMAL_INVENTORY = {
    "summary": {
        "source": "C:/Test",
        "total_files": 1,
        "total_size_bytes": 100,
        "extensions_count": {".pdf": 1},
        "skipped_count": 0,
        "errors_count": 0,
    },
    "files": [
        {
            "relative_path": "doc.pdf",
            "filename": "doc.pdf",
            "extension": ".pdf",
            "size_bytes": 100,
            "modified_time_iso": "2024-01-01T00:00:00",
            "sha256": "abc123",
        }
    ],
    "errors": [],
}

MINIMAL_CLASSIFICATION = {
    "summary": {
        "source": "C:/Test",
        "total_files": 1,
        "low_confidence_count": 0,
        "categories_count": {"Documents": 1},
        "location_policy_counts": {"classify_only": 1},
    },
    "classifications": [
        {
            "relative_path": "doc.pdf",
            "category": "Documents",
            "location_policy": "classify_only",
            "confidence": 0.9,
            "signals": ["ext:.pdf"],
            "suggested_folder": "Documents",
            "size_bytes": 100,
        }
    ],
}

MINIMAL_ACTION_PLAN = {
    "summary": {
        "source": "C:/Test",
        "total_files": 2,
        "root_sort_candidates_count": 0,
        "duplicate_groups_count": 1,
        "duplicate_files_count": 2,
        "keep_in_place_count": 2,
        "potential_reclaimable_bytes": 100,
        "duplicate_priority_counts": {"review_only": 1},
    },
    "root_sort_candidates": [],
    "duplicate_groups": [
        {
            "sha256": "deadbeef",
            "count": 2,
            "total_size_bytes": 200,
            "potential_reclaimable_bytes": 100,
            "status": "review_only",
            "review_priority": "review_only",
            "review_priority_reason": "test",
            "dry_run_only": True,
            "files": [
                {
                    "relative_path": "a/file.pdf",
                    "top_level_folder": "a",
                    "location_policy": "keep_in_place",
                    "context_bound": True,
                    "size_bytes": 100,
                },
                {
                    "relative_path": "b/file.pdf",
                    "top_level_folder": "b",
                    "location_policy": "keep_in_place",
                    "context_bound": True,
                    "size_bytes": 100,
                },
            ],
        }
    ],
}


class TestInventoryReportItalian(unittest.TestCase):
    def setUp(self):
        self.html = inventory_html(MINIMAL_INVENTORY)

    def test_lang_it(self):
        self.assertIn('lang="it"', self.html)

    def test_italian_title(self):
        self.assertIn("Report Inventario", self.html)

    def test_italian_headings(self):
        self.assertIn("Riepilogo", self.html)
        self.assertIn("File totali", self.html)
        self.assertIn("Estensioni", self.html)
        self.assertIn("File più grandi", self.html)

    def test_no_english_title(self):
        self.assertNotIn("Inventory Report", self.html)

    def test_no_destructive_text(self):
        for word in ("delete", "move", "rename", "overwrite"):
            self.assertNotIn(word, self.html.lower())


class TestClassificationReportItalian(unittest.TestCase):
    def setUp(self):
        self.html = classification_html(MINIMAL_CLASSIFICATION)

    def test_lang_it(self):
        self.assertIn('lang="it"', self.html)

    def test_italian_title(self):
        self.assertIn("Report Classificazione", self.html)

    def test_safety_wording_italian(self):
        self.assertIn("Solo dry-run", self.html)
        self.assertIn("Nessun file è stato spostato", self.html)

    def test_italian_headings(self):
        self.assertIn("Riepilogo", self.html)
        self.assertIn("Politica posizione", self.html)
        self.assertIn("Categoria", self.html)

    def test_no_english_title(self):
        self.assertNotIn("Classification Report", self.html)


class TestActionPlanReportItalian(unittest.TestCase):
    def setUp(self):
        self.html = action_plan_html(MINIMAL_ACTION_PLAN)

    def test_lang_it(self):
        self.assertIn('lang="it"', self.html)

    def test_italian_title(self):
        self.assertIn("Report Azioni Proposte", self.html)

    def test_safety_wording_italian(self):
        self.assertIn("Solo revisione", self.html)
        self.assertIn("Nessuna cancellazione", self.html)
        self.assertIn("spazio", self.html.lower())

    def test_italian_headings(self):
        self.assertIn("Riepilogo", self.html)
        self.assertIn("Gruppi duplicati esatti", self.html)
        self.assertIn("Come usare questo report", self.html)

    def test_italian_table_headers(self):
        self.assertIn("Priorità revisione / Motivo", self.html)
        self.assertIn("Conteggio", self.html)
        self.assertIn("Dimensione totale", self.html)

    def test_italian_filters(self):
        self.assertIn("Cerca nei percorsi", self.html)
        self.assertIn("mostra solo gruppi con file dentro cartelle/progetti", self.html)
        self.assertIn("mostra solo gruppi presenti in più cartelle principali", self.html)
        self.assertIn("mostra solo gruppi dove tutti i file hanno lo stesso nome", self.html)

    def test_no_english_title(self):
        self.assertNotIn("Proposed Actions Report", self.html)


if __name__ == "__main__":
    unittest.main()
