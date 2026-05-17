"""
Validate generated report HTML files structurally without opening a browser.
Standard library only. Read-only, non-destructive.

Usage:
    python scripts/validate_reports.py [inventory_report] [classification_report] [action_plan_report]

Defaults:
    reports/inventory_report.html
    reports/classification_report.html
    reports/action_plan_report.html
"""

import sys
import os

DEFAULT_PATHS = {
    "inventory": "reports/inventory_report.html",
    "classification": "reports/classification_report.html",
    "action_plan": "reports/action_plan_report.html",
}

ACTION_PLAN_MARKERS = [
    '<html lang="it">',
    'id="dup-data"',
    'type="application/json"',
    'JSON.parse',
    'id="dup-tbody"',
    'id="btn-reset-filters"',
    'id="dup-empty-state"',
    "Solo revisione",
    "Nessuna cancellazione",
    "teorico",
]

INVENTORY_MARKERS = [
    '<html lang="it">',
]

CLASSIFICATION_MARKERS = [
    '<html lang="it">',
]


def check_file(label, path, markers):
    if not os.path.exists(path):
        print(f"[SKIP] {label}: file not found at '{path}'")
        return True  # missing optional report is not a failure

    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    failures = []
    for marker in markers:
        if marker not in content:
            failures.append(marker)

    if failures:
        print(f"[FAIL] {label}: missing markers:")
        for m in failures:
            print(f"       - {m!r}")
        return False

    print(f"[OK]   {label}: all markers present")
    return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    paths = list(argv) + [""] * 3
    inventory_path = paths[0] or DEFAULT_PATHS["inventory"]
    classification_path = paths[1] or DEFAULT_PATHS["classification"]
    action_plan_path = paths[2] or DEFAULT_PATHS["action_plan"]

    results = []
    results.append(check_file("inventory_report", inventory_path, INVENTORY_MARKERS))
    results.append(check_file("classification_report", classification_path, CLASSIFICATION_MARKERS))
    results.append(check_file("action_plan_report", action_plan_path, ACTION_PLAN_MARKERS))

    if all(results):
        print("\nValidation passed.")
        return 0
    else:
        print("\nValidation FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
