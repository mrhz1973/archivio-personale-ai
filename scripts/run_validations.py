"""
ARCH-0136..ARCH-0139, ARCH-0147..ARCH-0158, ARCH-0630..ARCH-0649 — Local validation runner.

Runs local validations only. Designed to be safe-by-default:

- only local validations using the Python standard library;
- no network calls, no external APIs;
- no report opening, no browser launch, no auto-open of files;
- never reads or writes personal files;
- writes no user-facing output to disk;
- no destructive operations (no move, no rename, no delete on user files).

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
        "first-run check",
        [sys.executable, "scripts/run_first_time_check.py"],
        True,
    ),
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


def _run_step(label, argv, quiet=False):
    if not quiet:
        print(f"[RUN]  {label}")
    result = subprocess.run(argv, cwd=str(_REPO), capture_output=True, text=True)
    if result.returncode == 0:
        if not quiet:
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
        description=(
            "Run local project validations only. "
            "Stdlib only; no network/API; no report opening; "
            "no personal files; no destructive operations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Safety: local validations only; no network or external API; "
            "no report opening or browser launch; no personal files; "
            "no destructive operations.\n"
            "\n"
            "Exit codes:\n"
            "  0  all checks passed (or --list)\n"
            "  1  one or more checks failed"
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only essential checks (py_compile + validate_reports --help). "
             "Skips all full-only steps: first-run check, unittest discover, synthetic demo.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List planned checks without running them, then exit 0.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress [RUN] and [OK] lines; always print summary and errors.",
    )
    parser.add_argument(
        "--no-demo",
        action="store_true",
        help="Skip the synthetic demo step in full mode (useful for debug).",
    )
    args = parser.parse_args(argv)

    if args.list:
        print("Planned checks (--list mode; no checks are executed):")
        for label, _, skip_in_quick in _STEPS:
            mode = "quick+full" if not skip_in_quick else "full only "
            print(f"  [{mode}]  {label}")
        return 0

    failures = []
    skipped = []
    ok_count = 0

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
            if not args.quiet:
                print(f"[SKIP] {label} (--quick)")
            skipped.append(label)
            continue
        if args.no_demo and label == "synthetic demo":
            if not args.quiet:
                print(f"[SKIP] {label} (--no-demo)")
            skipped.append(label)
            continue
        rc = _run_step(label, cmd, quiet=args.quiet)
        if rc != 0:
            failures.append(label)
        else:
            ok_count += 1

    print()
    mode_str = "quick" if args.quick else "full"
    total_run = ok_count + len(failures)
    parts = [
        f"{total_run} run",
        f"{ok_count} OK",
        f"{len(failures)} failed",
        f"{len(skipped)} skipped",
    ]
    print(f"Summary ({mode_str}): {', '.join(parts)}")
    if failures:
        print(f"Failed: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
