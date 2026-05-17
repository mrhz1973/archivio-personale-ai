"""
ARCH-0136..ARCH-0139 — Local validation runner. Standard library only.

Does not open reports, does not use the network, does not modify reports/ or
personal files. Safe to run at any point in the dev workflow.

Exit codes:
  0   all checks passed
  1   one or more checks failed
"""

import argparse
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).parent.parent

_COMPILE_TARGETS = [
    "scripts/inventory_readonly.py",
    "scripts/classify_inventory.py",
    "scripts/generate_action_plan.py",
    "scripts/generate_inventory_report.py",
    "scripts/generate_classification_report.py",
    "scripts/generate_action_plan_report.py",
    "scripts/validate_reports.py",
]

# Each step: (label, argv, skip_in_quick)
_STEPS = [
    (
        "py_compile",
        [sys.executable, "-m", "py_compile"] + _COMPILE_TARGETS,
        False,
    ),
    (
        "unittest discover",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        True,   # skipped in --quick mode
    ),
    (
        "validate_reports --help",
        [sys.executable, "scripts/validate_reports.py", "--help"],
        False,
    ),
]


def _run_step(label, argv):
    print(f"[RUN]  {label}")
    result = subprocess.run(argv, cwd=str(_REPO), capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK]   {label}")
    else:
        print(f"[FAIL] {label}")
        if result.stdout.strip():
            print(result.stdout.rstrip())
        if result.stderr.strip():
            print(result.stderr.rstrip())
    return result.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run local project validations (stdlib only, no network, no report opening).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit codes:\n  0  all checks passed\n  1  one or more checks failed",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only essential checks (skip unittest discover).",
    )
    args = parser.parse_args(argv)

    failures = []
    for label, cmd, skip_in_quick in _STEPS:
        if args.quick and skip_in_quick:
            print(f"[SKIP] {label} (--quick)")
            continue
        rc = _run_step(label, cmd)
        if rc != 0:
            failures.append(label)

    print()
    if failures:
        print(f"FAILED ({len(failures)} check(s)): {', '.join(failures)}")
        return 1
    mode = "quick" if args.quick else "full"
    print(f"All checks passed ({mode} mode).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
