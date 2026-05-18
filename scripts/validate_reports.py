"""
Read-only structural validator for generated report HTML files.

This script is strictly read-only: it reads existing HTML files, validates their
structure and safety wording, and prints results to stdout. It never opens a
browser, never modifies or creates files, never creates directories, and never
uses the network or external APIs. It does not write any report.

Standard library only. Non-destructive.

Usage:
    python scripts/validate_reports.py                        # check default reports
    python scripts/validate_reports.py report.html            # explicit file(s)
    python scripts/validate_reports.py reports/               # all *.html in directory (recursive)
    python scripts/validate_reports.py reports/ extra.html    # mix
    python scripts/validate_reports.py --help                 # show this help

Exit codes:
    0 — no errors
    1 — one or more validation errors
    2 — invalid CLI usage or explicit path not found
"""

import os
import re
import sys

_HELP = """\
Usage: python scripts/validate_reports.py [PATH ...] [--help]

What this validator does:
  - Reads existing HTML reports (read-only).
  - Validates HTML structure and Italian safety wording.
  - Prints per-file results and a final summary to stdout.

What this validator does NOT do:
  - Does not open a browser.
  - Does not modify, create, or delete files.
  - Does not create directories or write any report.
  - Does not use the network, cloud, or external APIs.

Arguments:
  (no args)          Check default reports (inventory, classification, action plan).
  PATH               One or more .html files or directories (recursive, deterministic).
  -h, --help         Show this message and exit.

Exit codes:
  0  no errors
  1  one or more validation errors
  2  invalid CLI usage or explicit path not found
"""

DEFAULT_PATHS = [
    "reports/inventory_report.html",
    "reports/classification_report.html",
    "reports/action_plan_report.html",
]

# Presence of any of these (case-insensitive) satisfies the review-only wording
# check. Variants in use across the Italian HTML reports.
_REVIEW_ONLY_PHRASES = [
    "solo revisione",
    "review only",
    "review-only",
    "nessuna cancellazione",
    "nessuna cancellazione proposta",
    "nessuna cancellazione automatica",
    "solo suggerimenti",
    "no delete",
]

# Dangerous patterns: suggest automatic destructive action.
# Tuple: (compiled regex, human description). Each category has its own entry
# so callers (and tests) can verify they are detected independently.
_DANGEROUS_PATTERNS = [
    (re.compile(r"cancellazione\s+automatica", re.IGNORECASE), "cancellazione automatica"),
    (re.compile(r"eliminazione\s+automatica", re.IGNORECASE), "eliminazione automatica"),
    (re.compile(r"spostamento\s+automatico", re.IGNORECASE), "spostamento automatico"),
    (re.compile(r"rinomina\s+automatica", re.IGNORECASE), "rinomina automatica"),
    (re.compile(r"delete\s+automatically", re.IGNORECASE), "delete automatically"),
    (re.compile(r"move\s+automatically", re.IGNORECASE), "move automatically"),
    (re.compile(r"rename\s+automatically", re.IGNORECASE), "rename automatically"),
    (re.compile(r"safe\s+to\s+delete", re.IGNORECASE), "safe to delete"),
]

# Negation words that, when appearing within 80 chars before a dangerous match,
# indicate the phrasing is safe (e.g. "nessuna cancellazione automatica").
_NEGATION = re.compile(r"\b(nessuna?|no|non|senza|not|without)\b", re.IGNORECASE)
_NEGATION_WINDOW = 80

# Robust check for lang="it" / lang='it' (case-insensitive, optional whitespace).
_LANG_IT = re.compile(r"""lang\s*=\s*['"]\s*it\s*['"]""", re.IGNORECASE)


def _is_negated(content, match):
    prefix = content[max(0, match.start() - _NEGATION_WINDOW) : match.start()]
    return bool(_NEGATION.search(prefix))


def _dangerous_wording(content):
    """Return list of dangerous wording descriptions found and not negated."""
    found = []
    for pattern, desc in _DANGEROUS_PATTERNS:
        for m in pattern.finditer(content):
            if not _is_negated(content, m):
                found.append(desc)
                break  # one report per pattern type
    return found


def _has_review_only_wording(content):
    lower = content.lower()
    return any(phrase in lower for phrase in _REVIEW_ONLY_PHRASES)


def _has_lang_it(content):
    """Robust, case-insensitive check for lang attribute equal to 'it'."""
    return bool(_LANG_IT.search(content))


def _has_html_marker(content):
    """Accept either <!DOCTYPE html> or an <html ...> tag (case-insensitive)."""
    lower = content.lower()
    return "<html" in lower or "<!doctype html" in lower


def validate_file(path):
    """
    Validate a single HTML file (read-only).
    Returns (status, messages) where status is 'OK', 'WARN', or 'FAIL'.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        return "FAIL", [f"cannot read file: {e}"]

    if not content.strip():
        return "FAIL", ["file is empty"]

    status = "OK"
    messages = []

    if not _has_html_marker(content):
        messages.append("missing <html element or <!DOCTYPE html>")
        status = "FAIL"

    if not _has_lang_it(content):
        messages.append('missing lang="it"')
        status = "FAIL"

    if "<body" not in content.lower():
        messages.append("missing <body element")
        if status == "OK":
            status = "WARN"

    dangerous = _dangerous_wording(content)
    for d in dangerous:
        messages.append(f"dangerous wording: {d!r}")
    if dangerous:
        status = "FAIL"

    if not _has_review_only_wording(content):
        messages.append("recommended review-only wording absent")
        if status == "OK":
            status = "WARN"

    return status, messages


def _walk_html_files(directory):
    """Yield HTML files under directory in a stable, sorted order."""
    collected = []
    for dirpath, dirs, filenames in os.walk(directory):
        dirs.sort()
        for fn in sorted(filenames):
            if fn.lower().endswith(".html"):
                collected.append(os.path.join(dirpath, fn))
    return collected


def _collect_paths(argv):
    """
    Parse CLI arguments into a list of (path, is_explicit) tuples.
    Returns (entries, empty_dirs, error_message).
    empty_dirs lists directories that were found but contained no HTML files.
    error_message is non-None when CLI is invalid or an explicit path is missing.

    Ordering: directory contents are sorted deterministically (filenames and
    subdirs alphabetically). Multiple arguments are processed in the order they
    were passed; repeated calls with the same argv produce identical output.
    """
    if not argv:
        return [(p, False) for p in DEFAULT_PATHS], [], None

    entries = []
    empty_dirs = []
    for arg in argv:
        if os.path.isfile(arg):
            entries.append((arg, True))
        elif os.path.isdir(arg):
            found = _walk_html_files(arg)
            if found:
                entries.extend((p, True) for p in found)
            else:
                empty_dirs.append(arg)
        else:
            return [], [], f"path not found: '{arg}'"

    return entries, empty_dirs, None


def _print_summary(total, ok, warnings, errors, error_list):
    """Print the final summary block. Always called, both on OK and FAIL."""
    print()
    print(f"Checked: {total}  OK: {ok}  Warnings: {warnings}  Errors: {errors}")

    if error_list:
        print()
        print("Errors:")
        for path, msgs in error_list:
            print(f"  {path}")
            for m in msgs:
                print(f"    - {m}")
        print()
        print("Validation FAILED.")
    else:
        print()
        print("Validation passed.")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if "-h" in argv or "--help" in argv:
        print(_HELP, end="")
        return 0

    entries, empty_dirs, err = _collect_paths(argv)
    if err:
        print(f"[ERROR] {err}", file=sys.stderr)
        return 2

    for d in empty_dirs:
        print(f"[INFO]  no HTML files found in: {d}")

    total = ok = warnings = errors = 0
    error_list = []

    for path, is_explicit in entries:
        if not os.path.exists(path):
            if is_explicit:
                print(f"[ERROR] path not found: '{path}'", file=sys.stderr)
                return 2
            print(f"[SKIP]  {path}")
            continue

        total += 1
        status, messages = validate_file(path)

        if status == "OK":
            ok += 1
            print(f"[OK]    {path}")
        elif status == "WARN":
            warnings += 1
            print(f"[WARN]  {path}")
            for m in messages:
                print(f"        - {m}")
        else:
            errors += 1
            error_list.append((path, messages))
            print(f"[FAIL]  {path}")
            for m in messages:
                print(f"        - {m}")

    _print_summary(total, ok, warnings, errors, error_list)
    return 1 if error_list else 0


if __name__ == "__main__":
    sys.exit(main())
