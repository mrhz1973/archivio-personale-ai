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
    summary = data.get("summary", {})
    files = data.get("files", [])
    errors = data.get("errors", [])

    source = html.escape(str(summary.get("source", "")))
    total_files = summary.get("total_files", 0)
    total_size = summary.get("total_size_bytes", 0)
    ext_counts = summary.get("extensions_count", {})
    skipped = summary.get("skipped_count", 0)
    err_count = summary.get("errors_count", 0)

    # Top 10 extensions
    top_ext_rows = ""
    for ext, count in list(ext_counts.items())[:10]:
        top_ext_rows += f"<tr><td>{html.escape(ext)}</td><td>{count}</td></tr>\n"

    # Top 20 largest files
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

    # Errors
    error_section = ""
    if errors:
        rows = "".join(
            f"<tr><td>{html.escape(e.get('path',''))}</td><td>{html.escape(e.get('error',''))}</td></tr>\n"
            for e in errors
        )
        error_section = f"""
        <h2>Errors ({err_count})</h2>
        <table>
          <thead><tr><th>Path</th><th>Error</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Archivio Personale AI — Inventory Report</title>
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
  </style>
</head>
<body>
  <h1>Archivio Personale AI — Inventory Report</h1>
  <p><strong>Source:</strong> {source}</p>

  <h2>Summary</h2>
  <div>
    <div class="stat">Total files<span>{total_files}</span></div>
    <div class="stat">Total size<span>{fmt_size(total_size)}</span></div>
    <div class="stat">Skipped<span>{skipped}</span></div>
    <div class="stat">Errors<span>{err_count}</span></div>
  </div>

  <h2>Top Extensions</h2>
  <table>
    <thead><tr><th>Extension</th><th>Count</th></tr></thead>
    <tbody>{top_ext_rows}</tbody>
  </table>

  <h2>Largest Files (top 20)</h2>
  <table>
    <thead><tr><th>Path</th><th>Size</th><th>Extension</th></tr></thead>
    <tbody>{largest_rows}</tbody>
  </table>

  {error_section}
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate a static HTML report from an inventory JSON."
    )
    parser.add_argument("--input", required=True, help="Inventory JSON file path.")
    parser.add_argument("--output", required=True, help="Output HTML file path.")
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
