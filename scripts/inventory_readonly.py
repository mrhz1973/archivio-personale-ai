"""
Read-only recursive file inventory scanner.
Produces a JSON report. Never modifies source files.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

IGNORED_FILES = {"Zone.Identifier", "Thumbs.db", "desktop.ini"}
IGNORED_DIRS = {".git", "__pycache__", "node_modules"}


def should_ignore_file(name: str) -> bool:
    if name in IGNORED_FILES:
        return True
    if name.startswith("~$"):
        return True
    return False


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_directory(source: Path):
    files = []
    errors = []
    skipped = 0

    for root, dirs, filenames in os.walk(source, followlinks=False):
        # Prune ignored directories in-place so os.walk skips them
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for name in filenames:
            if should_ignore_file(name):
                skipped += 1
                continue

            file_path = Path(root) / name
            rel = file_path.relative_to(source)

            try:
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                digest = sha256_of_file(file_path)
                files.append(
                    {
                        "relative_path": str(rel),
                        "filename": name,
                        "extension": file_path.suffix.lower(),
                        "size_bytes": stat.st_size,
                        "modified_time_iso": mtime,
                        "sha256": digest,
                    }
                )
            except (PermissionError, OSError) as exc:
                errors.append({"path": str(rel), "error": str(exc)})

    return files, errors, skipped


def build_extensions_count(files: list) -> dict:
    counts: dict = {}
    for f in files:
        ext = f["extension"] or "(no extension)"
        counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Read-only file inventory scanner for personal archive. "
            "Reads the source folder and writes a JSON report to --output. "
            "Never modifies, moves, renames, or deletes source files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Safety:\n"
            "  Source folder is read-only. No source file is modified.\n"
            "  Only the JSON file at --output is written.\n\n"
            "Exit codes:\n"
            "  0  scan completed (errors field may be non-empty)\n"
            "  1  fatal error (source not found, not a directory)"
        ),
    )
    parser.add_argument("--source", required=True, help="Folder to scan (read-only, never modified).")
    parser.add_argument("--output", required=True, help="Output JSON file path (only file written).")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()

    if not source.exists():
        print(f"ERROR: Source folder does not exist: {source}", file=sys.stderr)
        sys.exit(1)

    if not source.is_dir():
        print(f"ERROR: Source path is not a directory: {source}", file=sys.stderr)
        sys.exit(1)

    # Safety: never default-write inside source; the user must explicitly choose it
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scanning: {source}")
    files, errors, skipped = scan_directory(source)

    total_size = sum(f["size_bytes"] for f in files)

    result = {
        "summary": {
            "source": str(source),
            "total_files": len(files),
            "total_size_bytes": total_size,
            "extensions_count": build_extensions_count(files),
            "skipped_count": skipped,
            "errors_count": len(errors),
        },
        "files": files,
        "errors": errors,
    }

    with output.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2, ensure_ascii=False)

    print(f"Done. Files found: {len(files)}, skipped: {skipped}, errors: {len(errors)}")
    print(f"Output written to: {output}")


if __name__ == "__main__":
    main()
