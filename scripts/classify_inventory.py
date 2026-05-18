"""
Rule-based dry-run classifier for inventory JSON files.

This script reads metadata produced by inventory_readonly.py and writes
classification suggestions. It never reads source file contents and never
moves, renames, deletes, overwrites, or reorganizes files.

Context preservation rule:
files that are already inside a subfolder are treated as context-bound and
default to keep_in_place. This prevents a PDF, spreadsheet, image, or other
file that belongs to a project folder from being suggested for relocation just
because of its extension.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath, Path
from typing import Any


EXTENSION_CATEGORIES = {
    # Documents
    ".pdf": ("Documents", 0.70),
    ".doc": ("Documents", 0.70),
    ".docx": ("Documents", 0.70),
    ".odt": ("Documents", 0.70),
    ".rtf": ("Documents", 0.65),

    # Spreadsheets
    ".xls": ("Spreadsheets", 0.72),
    ".xlsx": ("Spreadsheets", 0.72),
    ".ods": ("Spreadsheets", 0.72),
    ".csv": ("Spreadsheets", 0.65),

    # Presentations
    ".ppt": ("Presentations", 0.72),
    ".pptx": ("Presentations", 0.72),
    ".odp": ("Presentations", 0.72),

    # Images
    ".jpg": ("Images", 0.72),
    ".jpeg": ("Images", 0.72),
    ".png": ("Images", 0.72),
    ".gif": ("Images", 0.65),
    ".webp": ("Images", 0.65),
    ".tif": ("Images", 0.70),
    ".tiff": ("Images", 0.70),
    ".bmp": ("Images", 0.65),
    ".heic": ("Images", 0.70),

    # Video
    ".mp4": ("Videos", 0.72),
    ".mov": ("Videos", 0.72),
    ".avi": ("Videos", 0.68),
    ".mkv": ("Videos", 0.68),
    ".wmv": ("Videos", 0.65),

    # Audio
    ".mp3": ("Audio", 0.72),
    ".wav": ("Audio", 0.72),
    ".flac": ("Audio", 0.72),
    ".m4a": ("Audio", 0.68),
    ".ogg": ("Audio", 0.65),

    # Archives
    ".zip": ("Archives", 0.72),
    ".rar": ("Archives", 0.72),
    ".7z": ("Archives", 0.72),
    ".tar": ("Archives", 0.68),
    ".gz": ("Archives", 0.65),

    # Software / installers
    ".exe": ("Software", 0.78),
    ".msi": ("Software", 0.78),
    ".apk": ("Software", 0.72),
    ".dmg": ("Software", 0.72),
    ".iso": ("Disk Images", 0.70),

    # Notes / code / data
    ".txt": ("Text Notes", 0.62),
    ".md": ("Text Notes", 0.62),
    ".json": ("Data", 0.60),
    ".xml": ("Data", 0.60),
    ".html": ("Web Files", 0.60),
    ".htm": ("Web Files", 0.60),
    ".py": ("Code", 0.70),
    ".js": ("Code", 0.70),
    ".css": ("Code", 0.65),
    ".ps1": ("Code", 0.65),

    # Books
    ".epub": ("Books", 0.75),
    ".mobi": ("Books", 0.75),
}


KEYWORD_CATEGORIES = [
    ("Auto", ("auto", "tesla", "macchina", "veicolo", "bollo", "assicurazione", "tagliando", "pneumatici", "gomme")),
    ("Casa", ("casa", "mutuo", "affitto", "condominio", "utenza", "utenze", "enel", "gas", "acqua", "luce")),
    ("Lavoro", ("lavoro", "contratto", "busta", "stipendio", "cedolino", "missione", "turni", "presenze")),
    ("Finanze", ("fattura", "ricevuta", "scontrino", "pagamento", "bonifico", "banca", "estratto", "iban")),
    ("Sanita", ("sanita", "sanità", "medico", "referto", "analisi", "ricetta", "ospedale", "visita")),
    ("Viaggi", ("viaggio", "hotel", "volo", "biglietto", "prenotazione", "booking", "itinerario")),
    ("Foto Personali", ("foto", "photo", "immagine", "vacanza", "vacanze", "album")),
]


def normalize_text(value: str) -> str:
    return value.replace("\\", "/").lower()


def normalized_relative_path(relative_path: str) -> str:
    return relative_path.replace("\\", "/")


def is_context_bound(relative_path: str) -> bool:
    """Return True when the file is already inside a subfolder.

    Files already stored inside a folder likely belong to that folder's context,
    such as a project folder that contains PDFs, spreadsheets, images, notes,
    and other supporting files. The classifier must preserve that context.
    """

    normalized = normalized_relative_path(relative_path).strip("/")
    if not normalized:
        return False
    return PurePosixPath(normalized).parent != PurePosixPath(".")


def classify_file(file_info: dict[str, Any]) -> dict[str, Any]:
    relative_path = str(file_info.get("relative_path", ""))
    filename = str(file_info.get("filename", ""))
    extension = str(file_info.get("extension", "")).lower()
    haystack = normalize_text(f"{relative_path} {filename}")

    signals: list[str] = []

    keyword_match: tuple[str, str] | None = None
    for category, keywords in KEYWORD_CATEGORIES:
        for keyword in keywords:
            if keyword in haystack:
                keyword_match = (category, keyword)
                break
        if keyword_match:
            break

    ext_category, ext_confidence = EXTENSION_CATEGORIES.get(extension, ("Misc", 0.30))

    if keyword_match:
        category, keyword = keyword_match
        signals.append(f"keyword:{keyword}")
        if extension in EXTENSION_CATEGORIES:
            signals.append(f"extension:{extension}->{ext_category}")
            confidence = max(0.80, min(0.95, ext_confidence + 0.15))
        else:
            confidence = 0.78
    else:
        category = ext_category
        confidence = ext_confidence
        if extension:
            signals.append(f"extension:{extension}")
        else:
            signals.append("no_extension")

    context_bound = is_context_bound(relative_path)
    if context_bound:
        location_policy = "keep_in_place"
        suggested_folder = None
        signals.append("context:inside_existing_folder")
    else:
        location_policy = "classify_only"
        suggested_folder = category
        signals.append("context:root_file")

    return {
        "relative_path": relative_path,
        "filename": filename,
        "extension": extension,
        "size_bytes": int(file_info.get("size_bytes", 0) or 0),
        "category": category,
        "confidence": round(confidence, 2),
        "signals": signals,
        "location_policy": location_policy,
        "context_bound": context_bound,
        "suggested_folder": suggested_folder,
        "dry_run_only": True,
    }


def build_category_counts(classifications: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in classifications:
        category = str(item.get("category", "Misc"))
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


def build_location_policy_counts(classifications: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in classifications:
        policy = str(item.get("location_policy", "classify_only"))
        counts[policy] = counts.get(policy, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


def build_confidence_buckets(classifications: list[dict[str, Any]]) -> dict[str, int]:
    """Bucket confidences: high >= 0.75, medium >= 0.55, low < 0.55."""
    high = medium = low = 0
    for item in classifications:
        c = item.get("confidence", 0)
        if c >= 0.75:
            high += 1
        elif c >= 0.55:
            medium += 1
        else:
            low += 1
    return {"high": high, "medium": medium, "low": low}


def classify_inventory(data: dict[str, Any]) -> dict[str, Any]:
    files = data.get("files", [])
    if not isinstance(files, list):
        raise ValueError("Invalid inventory JSON: 'files' must be a list.")

    classifications = [classify_file(item) for item in files if isinstance(item, dict)]
    classifications.sort(key=lambda x: x.get("relative_path", ""))

    low_confidence = [item for item in classifications if item.get("confidence", 0) < 0.60]
    root_file_count = sum(1 for item in classifications if not item.get("context_bound", False))
    context_bound_count = sum(1 for item in classifications if item.get("context_bound", False))

    input_meta = data.get("metadata", {})
    generated_at = datetime.now(tz=timezone.utc).isoformat()

    metadata = {
        "schema_version": "1.0",
        "generated_at_iso": generated_at,
        "tool": "classify_inventory.py",
        "mode": "dry_run_classification",
        "input_tool": str(input_meta.get("tool", "")),
        "input_schema_version": str(input_meta.get("schema_version", "")),
    }

    summary = {
        "source": data.get("summary", {}).get("source", ""),
        "total_files": len(classifications),
        "categories_count": build_category_counts(classifications),
        "location_policy_counts": build_location_policy_counts(classifications),
        "low_confidence_count": len(low_confidence),
        "confidence_buckets": build_confidence_buckets(classifications),
        "root_file_count": root_file_count,
        "context_bound_count": context_bound_count,
        "dry_run_only": True,
    }

    return {
        "metadata": metadata,
        "summary": summary,
        "classifications": classifications,
        "errors": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rule-based dry-run classifier for Archivio Personale AI inventory files. "
            "Reads only the inventory JSON produced by inventory_readonly.py. "
            "Uses only metadata and relative paths already present in the JSON. "
            "Produces dry-run classification suggestions. "
            "Writes only the JSON file at --output. "
            "Never modifies, moves, renames, or deletes source files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Safety:\n"
            "  Input JSON is read-only. No source file is modified.\n"
            "  All suggestions are dry-run only (dry_run_only: true in output).\n"
            "  Only the JSON file at --output is written.\n\n"
            "Exit codes:\n"
            "  0  classifications written\n"
            "  1  input file not found"
        ),
    )
    parser.add_argument("--input", required=True, help="Input inventory JSON path (read-only).")
    parser.add_argument("--output", required=True, help="Output classifications JSON path (only file written).")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with input_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    result = classify_inventory(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2, ensure_ascii=False)

    total = result["summary"]["total_files"]
    low = result["summary"]["low_confidence_count"]
    keep = result["summary"]["location_policy_counts"].get("keep_in_place", 0)
    print(f"Classifications written to: {output_path}")
    print(f"Files classified: {total}, keep in place: {keep}, low confidence: {low}")


if __name__ == "__main__":
    main()
