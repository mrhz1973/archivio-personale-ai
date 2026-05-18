"""
Generate a static HTML report from classifications JSON.

This report is dry-run only. It does not modify, move, rename, delete,
overwrite, or reorganize source archive files.
"""

import argparse
import html
import json
import sys
from pathlib import Path


def fmt_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def build_html(data: dict) -> str:
    meta = data.get("metadata") or {}
    summary = data.get("summary", {})
    classifications = data.get("classifications", [])
    category_counts = summary.get("categories_count", {})
    policy_counts = summary.get("location_policy_counts", {})

    source = html.escape(str(summary.get("source", "")))
    total_files = int(summary.get("total_files", 0) or 0)
    low_confidence_count = int(summary.get("low_confidence_count", 0) or 0)
    keep_in_place_count = int(policy_counts.get("keep_in_place", 0) or 0)
    classify_only_count = int(policy_counts.get("classify_only", 0) or 0)

    category_rows = ""
    for category, count in category_counts.items():
        category_rows += (
            f"<tr><td>{html.escape(str(category))}</td>"
            f"<td>{int(count)}</td></tr>\n"
        )

    policy_rows = ""
    for policy, count in policy_counts.items():
        policy_rows += (
            f"<tr><td>{html.escape(str(policy))}</td>"
            f"<td>{int(count)}</td></tr>\n"
        )

    low_confidence = sorted(
        [item for item in classifications if float(item.get("confidence", 0) or 0) < 0.60],
        key=lambda item: float(item.get("confidence", 0) or 0),
    )[:50]

    low_rows = ""
    for item in low_confidence:
        low_rows += (
            "<tr>"
            f"<td>{html.escape(str(item.get('relative_path', '')))}</td>"
            f"<td>{html.escape(str(item.get('category', '')))}</td>"
            f"<td>{html.escape(str(item.get('location_policy', '')))}</td>"
            f"<td>{float(item.get('confidence', 0) or 0):.2f}</td>"
            f"<td>{html.escape(', '.join(item.get('signals', [])))}</td>"
            "</tr>\n"
        )

    sample_rows = ""
    for item in classifications[:100]:
        suggested_folder = item.get("suggested_folder")
        if suggested_folder is None:
            suggested_folder = "(mantieni nella cartella attuale)"
        sample_rows += (
            "<tr>"
            f"<td>{html.escape(str(item.get('relative_path', '')))}</td>"
            f"<td>{html.escape(str(item.get('category', '')))}</td>"
            f"<td>{html.escape(str(item.get('location_policy', '')))}</td>"
            f"<td>{html.escape(str(suggested_folder))}</td>"
            f"<td>{float(item.get('confidence', 0) or 0):.2f}</td>"
            f"<td>{fmt_size(int(item.get('size_bytes', 0) or 0))}</td>"
            f"<td>{html.escape(', '.join(item.get('signals', [])))}</td>"
            "</tr>\n"
        )

    metadata_section = ""
    if meta:
        mode_raw = str(meta.get("mode", ""))
        mode_label = ("Modalità: classificazione dry-run"
                      if mode_raw == "dry_run_classification" else html.escape(mode_raw))
        meta_rows = ""
        for label, key in [
            ("Versione schema", "schema_version"),
            ("Generato il", "generated_at_iso"),
            ("Strumento", "tool"),
            ("Strumento input", "input_tool"),
            ("Schema input", "input_schema_version"),
        ]:
            val = meta.get(key)
            if val is not None and str(val):
                meta_rows += f"<tr><td>{label}</td><td>{html.escape(str(val))}</td></tr>\n"
        if mode_raw:
            meta_rows += f"<tr><td>Modalità</td><td>{mode_label}</td></tr>\n"
        metadata_section = f"""
  <h2>Informazioni classificazione</h2>
  <table>
    <thead><tr><th>Campo</th><th>Valore</th></tr></thead>
    <tbody>{meta_rows}</tbody>
  </table>
"""

    buckets = summary.get("confidence_buckets")
    confidence_stats = ""
    if buckets and isinstance(buckets, dict):
        h = int(buckets.get("high", 0) or 0)
        m = int(buckets.get("medium", 0) or 0)
        lo = int(buckets.get("low", 0) or 0)
        confidence_stats = (
            f'<div class="stat">Confidenza alta<span>{h}</span></div>'
            f'<div class="stat">Confidenza media<span>{m}</span></div>'
            f'<div class="stat">Confidenza bassa<span>{lo}</span></div>'
        )

    root_file_count = summary.get("root_file_count")
    context_bound_count = summary.get("context_bound_count")
    extra_stats = ""
    if root_file_count is not None:
        extra_stats += f'<div class="stat">File in radice<span>{int(root_file_count)}</span></div>'
    if context_bound_count is not None:
        extra_stats += f'<div class="stat">File context-bound<span>{int(context_bound_count)}</span></div>'

    low_section = ""
    if low_rows:
        low_section = f"""
        <h2>Elementi con bassa confidenza (primi 50)</h2>
        <table>
          <thead><tr><th>Percorso</th><th>Categoria</th><th>Politica posizione</th><th>Confidenza</th><th>Segnali</th></tr></thead>
          <tbody>{low_rows}</tbody>
        </table>
        """

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Archivio Personale AI — Report Classificazione</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; color: #222; }}
    h1 {{ color: #333; }}
    h2 {{ margin-top: 2em; color: #444; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .stat {{ display: inline-block; margin: 0 2em 1em 0; }}
    .stat span {{ display: block; font-size: 2em; font-weight: bold; color: #2255aa; }}
    .safety-note {{ background: #f8f8e8; border: 1px solid #cccc88; padding: 0.7em 1em; margin: 1em 0; border-radius: 4px; font-size: 0.95em; }}
  </style>
</head>
<body>
  <h1>Archivio Personale AI — Report Classificazione</h1>
  <p><strong>Origine:</strong> {source}</p>

  <div class="safety-note">
    <strong>Nota:</strong> Solo revisione. Report statico, classificazione dry-run.
    Nessun file viene spostato, cancellato o rinominato da questo script.
    I file già dentro cartelle esistenti sono marcati <strong>keep_in_place</strong> per preservare il contesto.
  </div>
{metadata_section}
  <h2>Riepilogo</h2>
  <div>
    <div class="stat">File totali<span>{total_files}</span></div>
    <div class="stat">Mantieni nella posizione attuale<span>{keep_in_place_count}</span></div>
    <div class="stat">Solo classificazione (radice)<span>{classify_only_count}</span></div>
    <div class="stat">Bassa confidenza<span>{low_confidence_count}</span></div>
    {confidence_stats}
    {extra_stats}
  </div>

  <h2>Politica posizione</h2>
  <table>
    <thead><tr><th>Politica</th><th>Conteggio</th></tr></thead>
    <tbody>{policy_rows}</tbody>
  </table>

  <h2>Categoria</h2>
  <table>
    <thead><tr><th>Categoria</th><th>Conteggio</th></tr></thead>
    <tbody>{category_rows}</tbody>
  </table>

  {low_section}

  <h2>Classificazioni campione (prime 100)</h2>
  <table>
    <thead><tr><th>Percorso</th><th>Categoria</th><th>Politica posizione</th><th>Cartella suggerita</th><th>Confidenza</th><th>Dimensione</th><th>Segnali</th></tr></thead>
    <tbody>{sample_rows}</tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a static Italian HTML report from a classifications JSON. "
            "Reads the classification JSON produced by classify_inventory.py. "
            "Produces a static review-only HTML report. "
            "Writes only the HTML file at --output. "
            "Never modifies, moves, renames, or deletes source files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Safety:\n"
            "  Input JSON is read-only. No source file is modified.\n"
            "  The HTML report is static and review-only.\n"
            "  Only the HTML file at --output is written.\n\n"
            "Exit codes:\n"
            "  0  report written\n"
            "  1  input file not found"
        ),
    )
    parser.add_argument("--input", required=True, help="Classifications JSON file path (read-only input).")
    parser.add_argument("--output", required=True, help="Output HTML file path (only file written).")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with input_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_html(data), encoding="utf-8")

    print(f"Classification report written to: {output_path}")


if __name__ == "__main__":
    main()
