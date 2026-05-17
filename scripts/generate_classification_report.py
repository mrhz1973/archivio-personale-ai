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
    summary = data.get("summary", {})
    classifications = data.get("classifications", [])
    category_counts = summary.get("categories_count", {})

    source = html.escape(str(summary.get("source", "")))
    total_files = int(summary.get("total_files", 0) or 0)
    low_confidence_count = int(summary.get("low_confidence_count", 0) or 0)

    category_rows = ""
    for category, count in category_counts.items():
        category_rows += (
            f"<tr><td>{html.escape(str(category))}</td>"
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
            f"<td>{float(item.get('confidence', 0) or 0):.2f}</td>"
            f"<td>{html.escape(', '.join(item.get('signals', [])))}</td>"
            "</tr>\n"
        )

    sample_rows = ""
    for item in classifications[:100]:
        sample_rows += (
            "<tr>"
            f"<td>{html.escape(str(item.get('relative_path', '')))}</td>"
            f"<td>{html.escape(str(item.get('category', '')))}</td>"
            f"<td>{float(item.get('confidence', 0) or 0):.2f}</td>"
            f"<td>{fmt_size(int(item.get('size_bytes', 0) or 0))}</td>"
            f"<td>{html.escape(', '.join(item.get('signals', [])))}</td>"
            "</tr>\n"
        )

    low_section = ""
    if low_rows:
        low_section = f"""
        <h2>Low Confidence Items (first 50)</h2>
        <table>
          <thead><tr><th>Path</th><th>Category</th><th>Confidence</th><th>Signals</th></tr></thead>
          <tbody>{low_rows}</tbody>
        </table>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Archivio Personale AI — Classification Report</title>
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
    .warning {{ padding: 1em; background: #fff6d8; border: 1px solid #e5c45b; }}
  </style>
</head>
<body>
  <h1>Archivio Personale AI — Classification Report</h1>
  <p><strong>Source:</strong> {source}</p>
  <p class="warning"><strong>Dry-run only:</strong> this report contains suggestions only. No files were moved, renamed, deleted, overwritten, or reorganized.</p>

  <h2>Summary</h2>
  <div>
    <div class="stat">Total files<span>{total_files}</span></div>
    <div class="stat">Low confidence<span>{low_confidence_count}</span></div>
  </div>

  <h2>Categories</h2>
  <table>
    <thead><tr><th>Category</th><th>Count</th></tr></thead>
    <tbody>{category_rows}</tbody>
  </table>

  {low_section}

  <h2>Sample Classifications (first 100)</h2>
  <table>
    <thead><tr><th>Path</th><th>Category</th><th>Confidence</th><th>Size</th><th>Signals</th></tr></thead>
    <tbody>{sample_rows}</tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a static HTML report from classifications JSON."
    )
    parser.add_argument("--input", required=True, help="Classifications JSON file path.")
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
    output_path.write_text(build_html(data), encoding="utf-8")

    print(f"Classification report written to: {output_path}")


if __name__ == "__main__":
    main()
