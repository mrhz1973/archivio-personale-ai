"""
ARCH-0136..ARCH-0139, ARCH-0147..ARCH-0158 — Local validation runner.
Standard library only. No network, no report opening, no personal files.

Exit codes:
  0   all checks passed (or --list)
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
# skip_in_quick=True  → runs in full mode only
# skip_in_quick=False → runs in both quick and full mode
_STEPS = [
    (
        "py_compile",
        [sys.executable, "-m", "py_compile"] + _COMPILE_TARGETS,
        False,
    ),
    (
        "unittest discover",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        True,
    ),
    (
        "validate_reports --help",
        [sys.executable, "scripts/validate_reports.py", "--help"],
        False,
    ),
    (
        "synthetic demo",
        [sys.executable, "scripts/run_synthetic_demo.py"],
        True,
    ),
]


def _check_compile_targets():
    """Return list of compile targets that do not exist under _REPO."""
    return [t for t in _COMPILE_TARGETS if not (_REPO / t).exists()]


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
        epilog=(
            "Exit codes:\n"
            "  0  all checks passed (or --list)\n"
            "  1  one or more checks failed"
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only essential checks (skip unittest discover).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List planned checks without running them, then exit 0.",
    )
    args = parser.parse_args(argv)

    if args.list:
        print("Planned checks:")
        for label, _, skip_in_quick in _STEPS:
            mode = "quick+full" if not skip_in_quick else "full only "
            print(f"  [{mode}] {label}")
        return 0

    failures = []

    # Robustness check: verify all compile targets exist before running py_compile
    missing = _check_compile_targets()
    if missing:
        print(f"[FAIL] py_compile: missing expected targets: {', '.join(missing)}")
        failures.append("py_compile")
        run_steps = [(l, c, s) for l, c, s in _STEPS if l != "py_compile"]
    else:
        run_steps = list(_STEPS)

    for label, cmd, skip_in_quick in run_steps:
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
