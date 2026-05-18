"""
Synthetic end-to-end demo — stdlib only, no network, no personal files.

Runs the full pipeline on a temporary directory of innocuous synthetic files:
  1. inventory_readonly   → inventory.json
  2. classify_inventory   → classifications.json
  3. generate_action_plan → proposed_actions.json
  4. generate_inventory_report    → inventory_report.html
  5. generate_classification_report → classification_report.html
  6. generate_action_plan_report  → action_plan_report.html
  7. validate_reports     → structural check on all three HTML files

--quick runs only steps 1–3 (inventory → classify → inventory report).

Output goes to a temporary directory (deleted on exit unless --keep-temp).
Never writes to reports/, never opens a browser, never uses network or API.

After each run a demo_manifest.json is written inside the temp dir (unless
--no-manifest). The manifest contains: mode, temp_dir basename, timestamps,
exit_code, per-step results, and a list of generated files. It is purely
temporary and synthetic — never commit it or write it to reports/.

Exit codes:
  0  all steps passed (or --list)
  1  one or more steps failed
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_PYTHON = sys.executable

_FULL_STEPS_NAMES = [
    "inventory_readonly",
    "classify_inventory",
    "generate_action_plan",
    "generate_inventory_report",
    "generate_classification_report",
    "generate_action_plan_report",
    "validate_reports",
]

_QUICK_STEPS_NAMES = [
    "inventory_readonly",
    "classify_inventory",
    "generate_inventory_report",
]

_EXPECTED_SCRIPTS = [
    "scripts/inventory_readonly.py",
    "scripts/classify_inventory.py",
    "scripts/generate_action_plan.py",
    "scripts/generate_inventory_report.py",
    "scripts/generate_classification_report.py",
    "scripts/generate_action_plan_report.py",
    "scripts/validate_reports.py",
]


def _run(label, argv, *, quiet=False):
    """Run a subprocess step from repo root. Print result. Return (ok, returncode)."""
    cmd = [_PYTHON] + [str(a) for a in argv]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
    ok = result.returncode == 0
    if not quiet or not ok:
        status = "[OK]  " if ok else "[FAIL]"
        if not quiet or not ok:
            print(f"{status} {label}")
        if not ok:
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    print(f"       {line}")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    print(f"       {line}")
    return ok, result.returncode


def _make_synthetic_source(base: Path) -> Path:
    """Create a small synthetic directory tree with innocuous files."""
    src = base / "source"
    src.mkdir()
    (src / "note.txt").write_text("synthetic note", encoding="utf-8")
    (src / "document.pdf").write_bytes(b"%PDF synthetic")
    (src / "photo.jpg").write_bytes(b"\xff\xd8\xff synthetic jpg")
    sub = src / "subfolder"
    sub.mkdir()
    (sub / "report.docx").write_bytes(b"synthetic docx")
    (sub / "archive.zip").write_bytes(b"PK synthetic zip")
    return src


def _check_expected_scripts():
    """Return list of expected script paths that are missing."""
    return [s for s in _EXPECTED_SCRIPTS if not (_REPO_ROOT / s).exists()]


def _build_steps(tmpdir: Path, src: Path):
    """Return all pipeline steps as (label, argv) tuples."""
    scripts = _REPO_ROOT / "scripts"
    inventory_json = tmpdir / "inventory.json"
    classifications_json = tmpdir / "classifications.json"
    proposed_actions_json = tmpdir / "proposed_actions.json"
    inventory_html = tmpdir / "inventory_report.html"
    classification_html = tmpdir / "classification_report.html"
    action_plan_html = tmpdir / "action_plan_report.html"

    return [
        ("inventory_readonly",
         [scripts / "inventory_readonly.py", "--source", src, "--output", inventory_json]),
        ("classify_inventory",
         [scripts / "classify_inventory.py", "--input", inventory_json, "--output", classifications_json]),
        ("generate_action_plan",
         [scripts / "generate_action_plan.py",
          "--inventory", inventory_json,
          "--classifications", classifications_json,
          "--output", proposed_actions_json]),
        ("generate_inventory_report",
         [scripts / "generate_inventory_report.py", "--input", inventory_json, "--output", inventory_html]),
        ("generate_classification_report",
         [scripts / "generate_classification_report.py", "--input", classifications_json, "--output", classification_html]),
        ("generate_action_plan_report",
         [scripts / "generate_action_plan_report.py", "--input", proposed_actions_json, "--output", action_plan_html]),
        ("validate_reports",
         [scripts / "validate_reports.py", inventory_html, classification_html, action_plan_html]),
    ]


def _collect_generated_files(tmpdir: Path):
    """Return list of file records relative to tmpdir (excludes source/ input tree and manifest)."""
    source_dir = tmpdir / "source"
    records = []
    for f in sorted(tmpdir.rglob("*")):
        if not f.is_file():
            continue
        try:
            f.relative_to(source_dir)
            continue  # skip source/ input files
        except ValueError:
            pass
        if f.name == "demo_manifest.json":
            continue  # skip manifest itself to avoid circular reference
        rel = str(f.relative_to(tmpdir))
        ext = f.suffix.lstrip(".").lower() or "bin"
        records.append({"path": rel, "type": ext, "size": f.stat().st_size})
    records.sort(key=lambda r: r["path"])
    return records


def _write_manifest(tmpdir: Path, mode: str, started_at: str, finished_at: str,
                    exit_code: int, step_results: list):
    """Write demo_manifest.json inside tmpdir. Stores basename only — no absolute paths."""
    _mode_value = f"synthetic_demo_{mode}"  # e.g. synthetic_demo_full, synthetic_demo_quick
    manifest = {
        "metadata": {
            "schema_version": "1.0",
            "tool": "run_synthetic_demo.py",
            "mode": _mode_value,
            "safety_profile": "synthetic_temp_only_no_personal_files",
        },
        "safety": {
            "uses_personal_files": False,
            "uses_network": False,
            "uses_api": False,
            "writes_reports_dir": False,
            "opens_browser": False,
        },
        "mode": mode,
        "temp_dir": tmpdir.name,  # basename only: no personal/home path
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "steps_total": len(step_results),
        "steps_ok": sum(1 for s in step_results if s["status"] == "ok"),
        "steps_failed": sum(1 for s in step_results if s["status"] != "ok"),
        "steps": step_results,
        "generated_files": _collect_generated_files(tmpdir),
    }
    (tmpdir / "demo_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Run the full pipeline on synthetic data. "
            "Uses only synthetic fixture files in a temporary directory. "
            "Never uses personal files, never writes to reports/, "
            "never uses network or API, never opens a browser. "
            "Temporary directory is deleted on exit unless --keep-temp."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Safety:\n"
            "  Synthetic files only — no personal archive files touched.\n"
            "  All output goes to a temporary directory.\n"
            "  No writes to reports/. No network. No API. No browser.\n\n"
            "Exit codes:\n"
            "  0  all steps passed (or --list)\n"
            "  1  one or more steps failed"
        ),
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary directory and print its path instead of deleting it.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a minimal end-to-end pipeline (inventory -> classify -> inventory report).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List planned steps without executing them, then exit 0.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-step OK output and header. Failures and summary are always printed.",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="Skip writing demo_manifest.json (useful for debugging; default is manifest on).",
    )
    args = parser.parse_args(argv)

    if args.list:
        names = _QUICK_STEPS_NAMES if args.quick else _FULL_STEPS_NAMES
        mode = "quick" if args.quick else "full"
        print(f"Planned steps ({mode} mode) — list only, pipeline not executed:")
        for name in names:
            print(f"  {name}")
        return 0

    tmpdir = Path(tempfile.mkdtemp(prefix="archivio_demo_"))
    try:
        return _run_pipeline(
            tmpdir,
            keep_temp=args.keep_temp,
            quick=args.quick,
            no_manifest=args.no_manifest,
            quiet=args.quiet,
        )
    except Exception as exc:
        print(f"[ERROR] unexpected exception: {exc}")
        return 1
    finally:
        if args.keep_temp:
            manifest_path = tmpdir / "demo_manifest.json"
            print(f"\nTemp directory kept at: {tmpdir}")
            if manifest_path.exists():
                print(f"Manifest:              {manifest_path}")
        else:
            shutil.rmtree(tmpdir, ignore_errors=True)


def _run_pipeline(tmpdir: Path, *, keep_temp: bool, quick: bool = False,
                  no_manifest: bool = False, quiet: bool = False) -> int:
    missing = _check_expected_scripts()
    if missing:
        for m in missing:
            print(f"[FAIL] missing expected script: {m}")
        return 1

    src = _make_synthetic_source(tmpdir)
    all_steps = _build_steps(tmpdir, src)

    quick_names = set(_QUICK_STEPS_NAMES)
    steps = [(lbl, argv) for lbl, argv in all_steps if not quick or lbl in quick_names]

    mode = "quick" if quick else "full"
    if not quiet:
        print(f"=== Archivio Personale AI — synthetic end-to-end demo ({mode}) ===")
        print(f"Working in: {tmpdir}\n")

    started_at = datetime.datetime.now().isoformat(timespec="seconds")
    ok_count = 0
    fail_count = 0
    step_results = []

    for label, argv in steps:
        ok, rc = _run(label, argv, quiet=quiet)
        step_results.append({
            "label": label,
            "command": label,  # safe: step name only, no absolute paths
            "returncode": rc,
            "status": "ok" if ok else "fail",
        })
        if ok:
            ok_count += 1
        else:
            fail_count += 1

    finished_at = datetime.datetime.now().isoformat(timespec="seconds")
    total = ok_count + fail_count
    exit_code = 0 if fail_count == 0 else 1

    if not no_manifest:
        _write_manifest(tmpdir, mode, started_at, finished_at, exit_code, step_results)

    if not quiet:
        print()
        print(f"Steps: {total}  OK: {ok_count}  Failed: {fail_count}  Dir: {tmpdir}")
    else:
        print(f"Steps: {total}  OK: {ok_count}  Failed: {fail_count}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
