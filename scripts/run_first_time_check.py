"""
ARCH-0335..ARCH-0344 — First-run readiness check.
Standard library only. No network, no personal files, no reports/ reads.

Verifies:
  - Python version >= 3.8
  - Expected scripts exist: run_validations.py, run_synthetic_demo.py
  - Expected docs exist: docs/COMMANDS.md, README.md

Exit codes:
  0   all checks passed (or --list)
  1   one or more checks failed
"""

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).parent.parent

# (check_label, callable_that_returns_bool_or_error_msg)
_CHECKS = []


def _check_python_version():
    """Verify Python >= 3.8."""
    if sys.version_info >= (3, 8):
        return True
    return f"Python {sys.version_info.major}.{sys.version_info.minor} < 3.8 required"


def _check_script_exists(script_path):
    """Return True if script exists, error msg if not."""
    full_path = _REPO / script_path
    if full_path.exists():
        return True
    return f"{script_path} not found"


def _check_doc_exists(doc_path):
    """Return True if doc exists, error msg if not."""
    full_path = _REPO / doc_path
    if full_path.exists():
        return True
    return f"{doc_path} not found"


_CHECKS = [
    ("Python >= 3.8", _check_python_version),
    ("scripts/run_validations.py exists", lambda: _check_script_exists("scripts/run_validations.py")),
    ("scripts/run_synthetic_demo.py exists", lambda: _check_script_exists("scripts/run_synthetic_demo.py")),
    ("docs/COMMANDS.md exists", lambda: _check_doc_exists("docs/COMMANDS.md")),
    ("README.md exists", lambda: _check_doc_exists("README.md")),
]


def main():
    parser = argparse.ArgumentParser(
        description="First-run readiness check. Verifies Python version, required scripts, and docs."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List planned checks without running them; exit 0"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress [OK] lines; keep [FAIL] and summary"
    )
    args = parser.parse_args()

    if args.list:
        for label, _ in _CHECKS:
            print(label)
        return 0

    ok_count = 0
    failures = []

    for label, check_fn in _CHECKS:
        result = check_fn()
        if result is True:
            if not args.quiet:
                print(f"[OK]   {label}")
            ok_count += 1
        else:
            error_msg = result if isinstance(result, str) else "check failed"
            print(f"[FAIL] {label}: {error_msg}")
            failures.append(label)

    print()
    total = ok_count + len(failures)
    parts = [f"{total} checked", f"{ok_count} OK"]
    if failures:
        parts.append(f"{len(failures)} failed")
    print(f"Summary: {', '.join(parts)}")

    if failures:
        print(f"Failed: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
