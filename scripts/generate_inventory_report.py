"""
Generate a static HTML report from an inventory JSON file.
Never modifies source archive files.
"""

import argparse
import html
import json
import sys
from pathlib import Path


def fmt_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def build_html(data: dict) -> str:
    meta = data.get("metadata", {})
    summary = data.get("summary", {})
    files = data.get("files", [])
    errors = data.get("errors", [])

    source = html.escape(str(summary.get("source", "")))
    total_files = summary.get("total_files", 0)
    total_size_bytes = summary.get("total_size_bytes", 0)
    total_size_human = summary.get("total_size_human", "")
    size_display = html.escape(total_size_human) if total_size_human else fmt_size(total_size_bytes)
    dirs_scanned = summary.get("directories_scanned", None)
    ignored_dirs = summary.get("ignored_dirs_count", None)
    ext_counts = summary.get("extensions_count", {})
    skipped = summary.get("skipped_count", 0)
    err_count = summary.get("errors_count", 0)

    # Metadata section (optional — graceful if absent)
    metadata_section = ""
    if meta:
        schema_ver = html.escape(str(meta.get("schema_version", "")))
        gen_at = html.escape(str(meta.get("generated_at_iso", "")))
        tool = html.escape(str(meta.get("tool", "")))
        mode = html.escape(str(meta.get("mode", "")))
        mode_label = "Modalità: sola lettura" if meta.get("mode") == "read_only" else html.escape(str(meta.get("mode", "")))
        rows = ""
        if schema_ver:
            rows += f"<tr><td>Versione schema</td><td>{schema_ver}</td></tr>\n"
        if gen_at:
            rows += f"<tr><td>Generato il</td><td>{gen_at}</td></tr>\n"
        if tool:
            rows += f"<tr><td>Strumento</td><td>{tool}</td></tr>\n"
        if mode:
            rows += f"<tr><td>Modalità</td><td>{mode_label}</td></tr>\n"
        if rows:
            metadata_section = f"""
  <h2>Informazioni report</h2>
  <table>
    <thead><tr><th>Campo</th><th>Valore</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
"""

    # Optional extra summary stats
    extra_stats = ""
    if dirs_scanned is not None:
        extra_stats += f'<div class="stat">Directory scansionate<span>{dirs_scanned}</span></div>\n    '
    if ignored_dirs is not None:
        extra_stats += f'<div class="stat">Directory ignorate<span>{ignored_dirs}</span></div>\n    '

    # Top 10 extensions
    top_ext_rows = ""
    for ext, count in list(ext_counts.items())[:10]:
        top_ext_rows += f"<tr><td>{html.escape(ext)}</td><td>{count}</td></tr>\n"

    # Top 20 largest files (review list — no action proposed)
    largest = sorted(files, key=lambda f: f.get("size_bytes", 0), reverse=True)[:20]
    largest_rows = ""
    for f in largest:
        largest_rows += (
            f"<tr>"
            f"<td>{html.escape(f.get('relative_path', ''))}</td>"
            f"<td>{fmt_size(f.get('size_bytes', 0))}</td>"
            f"<td>{html.escape(f.get('extension', '') or '(none)')}</td>"
            f"</tr>\n"
        )

    # Errori
    error_section = ""
    if errors:
        rows = "".join(
            f"<tr><td>{html.escape(e.get('path',''))}</td><td>{html.escape(e.get('error',''))}</td></tr>\n"
            for e in errors
        )
        error_section = f"""
  <h2>Errori ({err_count})</h2>
  <table>
    <thead><tr><th>Percorso</th><th>Errore</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
"""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Archivio Personale AI — Report Inventario</title>
  <style>
    body {{ font-family: sans-serif; margin: 2em; color: #222; }}
    h1 {{ color: #333; }}
    h2 {{ margin-top: 2em; color: #444; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .stat {{ display: inline-block; margin: 0 2em 1em 0; }}
    .stat span {{ display: block; font-size: 2em; font-weight: bold; color: #2255aa; }}
    .safety-note {{ background: #f8f8e8; border: 1px solid #cccc88; padding: 0.7em 1em; margin: 1em 0; border-radius: 4px; font-size: 0.95em; }}
  </style>
</head>
<body>
  <h1>Archivio Personale AI — Report Inventario</h1>
  <p><strong>Origine:</strong> {source}</p>

  <div class="safety-note">
    <strong>Nota:</strong> Solo revisione. Nessuna cancellazione proposta.
    Nessuno spostamento automatico. Nessuna rinomina automatica.
  </div>
{metadata_section}
  <h2>Riepilogo</h2>
  <div>
    <div class="stat">File totali<span>{total_files}</span></div>
    <div class="stat">Dimensione totale<span>{size_display}</span></div>
    <div class="stat">File ignorati<span>{skipped}</span></div>
    <div class="stat">Errori<span>{err_count}</span></div>
    {extra_stats}
  </div>

  <h2>Estensioni</h2>
  <table>
    <thead><tr><th>Estensione</th><th>Conteggio</th></tr></thead>
    <tbody>{top_ext_rows}</tbody>
  </table>

  <h2>File più grandi — lista di revisione (primi 20)</h2>
  <table>
    <thead><tr><th>Percorso</th><th>Dimensione</th><th>Estensione</th></tr></thead>
    <tbody>{largest_rows}</tbody>
  </table>
{error_section}
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a static HTML report from an inventory JSON. "
            "Reads --input JSON and writes only the HTML file at --output. "
            "Never modifies source archive files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Safety:\n"
            "  Input JSON is read-only. No archive file is modified.\n"
            "  Only the HTML file at --output is written.\n\n"
            "Exit codes:\n"
            "  0  report written\n"
            "  1  input file not found"
        ),
    )
    parser.add_argument("--input", required=True, help="Inventory JSON file path (read-only input).")
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

    html_content = build_html(data)
    with output_path.open("w", encoding="utf-8") as fp:
        fp.write(html_content)

    print(f"Report written to: {output_path}")


if __name__ == "__main__":
    main()
