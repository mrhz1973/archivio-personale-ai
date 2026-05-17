"""
Validate generated report HTML files structurally without opening a browser.
Standard library only. Read-only, non-destructive.

Usage:
    python scripts/validate_reports.py                        # check default reports
    python scripts/validate_reports.py report.html           # explicit file(s)
    python scripts/validate_reports.py reports/              # all *.html in directory (recursive)
    python scripts/validate_reports.py reports/ extra.html   # mix

Exit codes:
    0 — no errors
    1 — one or more validation errors
    2 — invalid CLI usage or explicit path not found
"""

import os
import re
import sys

DEFAULT_PATHS = [
    "reports/inventory_report.html",
    "reports/classification_report.html",
    "reports/action_plan_report.html",
]

# Presence of any of these (case-insensitive) satisfies review-only wording check.
_REVIEW_ONLY_PHRASES = [
    "solo revisione",
    "nessuna cancellazione",
    "review only",
    "no delete",
]

# Dangerous patterns: suggest automatic destructive action.
# Tuple: (compiled regex, human description)
_DANGEROUS_PATTERNS = [
    (re.compile(r"cancellazione\s+automatica", re.IGNORECASE), "cancellazione automatica"),
    (re.compile(r"eliminazione\s+automatica", re.IGNORECASE), "eliminazione automatica"),
    (re.compile(r"spostamento\s+automatico", re.IGNORECASE), "spostamento automatico"),
    (re.compile(r"rinomina\s+automatica", re.IGNORECASE), "rinomina automatica"),
    (re.compile(r"(delete|move|rename)\s+automatically", re.IGNORECASE), "auto destructive action (EN)"),
    (re.compile(r"safe\s+to\s+delete", re.IGNORECASE), "safe to delete"),
]

# Negation words that, when appearing within 80 chars before a dangerous match,
# indicate the phrasing is safe (e.g. "nessuna cancellazione automatica").
_NEGATION = re.compile(r"\b(nessuna?|no|non|senza|not|without)\b", re.IGNORECASE)


def _is_negated(content, match):
    prefix = content[max(0, match.start() - 80) : match.start()]
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


def validate_file(path):
    """
    Validate a single HTML file.
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

    if "<html" not in content.lower():
        messages.append("missing <html element")
        status = "FAIL"

    if 'lang="it"' not in content and "lang='it'" not in content:
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


def _collect_paths(argv):
    """
    Parse CLI arguments into a list of (path, is_explicit) tuples.
    Returns (entries, error_message).
    error_message is non-None when CLI is invalid or an explicit path is missing.
    """
    if not argv:
        return [(p, False) for p in DEFAULT_PATHS], None

    entries = []
    for arg in argv:
        if os.path.isfile(arg):
            entries.append((arg, True))
        elif os.path.isdir(arg):
            for dirpath, _dirs, filenames in os.walk(arg):
                for fn in sorted(filenames):
                    if fn.lower().endswith(".html"):
                        entries.append((os.path.join(dirpath, fn), True))
        else:
            return [], f"path not found: '{arg}'"

    return entries, None


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    entries, err = _collect_paths(argv)
    if err:
        print(f"[ERROR] {err}", file=sys.stderr)
        return 2

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

    print()
    print(f"Checked: {total}  OK: {ok}  Warnings: {warnings}  Errors: {errors}")

    if error_list:
        print("\nErrors:")
        for path, msgs in error_list:
            print(f"  {path}")
            for m in msgs:
                print(f"    - {m}")
        print("\nValidation FAILED.")
        return 1

    print("\nValidation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
