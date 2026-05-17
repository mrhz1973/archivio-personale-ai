"""
Rule-based dry-run classifier for inventory JSON files.

This script reads metadata produced by inventory_readonly.py and writes
classification suggestions. It never reads source file contents and never
moves, renames, deletes, overwrites, or reorganizes files.
"""

import argparse
import json
import sys
from pathlib import Path
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

    return {
        "relative_path": relative_path,
        "filename": filename,
        "extension": extension,
        "size_bytes": int(file_info.get("size_bytes", 0) or 0),
        "category": category,
        "confidence": round(confidence, 2),
        "signals": signals,
        "suggested_folder": category,
        "dry_run_only": True,
    }


def build_category_counts(classifications: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in classifications:
        category = str(item.get("category", "Misc"))
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def classify_inventory(data: dict[str, Any]) -> dict[str, Any]:
    files = data.get("files", [])
    if not isinstance(files, list):
        raise ValueError("Invalid inventory JSON: 'files' must be a list.")

    classifications = [classify_file(item) for item in files if isinstance(item, dict)]
    low_confidence = [item for item in classifications if item.get("confidence", 0) < 0.60]

    summary = {
        "source": data.get("summary", {}).get("source", ""),
        "total_files": len(classifications),
        "categories_count": build_category_counts(classifications),
        "low_confidence_count": len(low_confidence),
        "dry_run_only": True,
    }

    return {
        "summary": summary,
        "classifications": classifications,
        "errors": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rule-based dry-run classifier for Archivio Personale AI inventory files."
    )
    parser.add_argument("--input", required=True, help="Input inventory JSON path.")
    parser.add_argument("--output", required=True, help="Output classifications JSON path.")
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
    print(f"Classifications written to: {output_path}")
    print(f"Files classified: {total}, low confidence: {low}")


if __name__ == "__main__":
    main()
