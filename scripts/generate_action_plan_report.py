"""
Generate a static HTML report from proposed actions JSON.

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
    root_sort_candidates = data.get("root_sort_candidates", [])
    duplicate_groups = data.get("duplicate_groups", [])
    priority_counts = summary.get("duplicate_priority_counts", {})

    source = html.escape(str(summary.get("source", "")))
    total_files = int(summary.get("total_files", 0) or 0)
    root_sort_count = int(summary.get("root_sort_candidates_count", 0) or 0)
    duplicate_groups_count = int(summary.get("duplicate_groups_count", 0) or 0)
    duplicate_files_count = int(summary.get("duplicate_files_count", 0) or 0)
    keep_in_place_count = int(summary.get("keep_in_place_count", 0) or 0)
    potential_reclaimable = int(summary.get("potential_reclaimable_bytes", 0) or 0)

    sort_rows = ""
    for item in root_sort_candidates[:200]:
        sort_rows += (
            "<tr>"
            f"<td>{html.escape(str(item.get('relative_path', '')))}</td>"
            f"<td>{html.escape(str(item.get('category', '')))}</td>"
            f"<td>{float(item.get('confidence', 0) or 0):.2f}</td>"
            f"<td>{html.escape(str(item.get('proposed_destination_relative_path', '')))}</td>"
            f"<td>{html.escape(str(item.get('status', '')))}</td>"
            "</tr>\n"
        )

    priority_rows = ""
    for priority, count in priority_counts.items():
        priority_rows += (
            "<tr>"
            f"<td>{html.escape(str(priority))}</td>"
            f"<td>{int(count)}</td>"
            "</tr>\n"
        )

    duplicate_rows = ""
    for group in duplicate_groups[:100]:
        files_html = "<ul>" + "".join(
            f"<li>{html.escape(str(file.get('relative_path', '')))} "
            f"[{html.escape(str(file.get('top_level_folder', '')))}] "
            f"({html.escape(str(file.get('location_policy', '')))}, {fmt_size(int(file.get('size_bytes', 0) or 0))})</li>"
            for file in group.get("files", [])
        ) + "</ul>"
        duplicate_rows += (
            "<tr>"
            f"<td>{html.escape(str(group.get('sha256', ''))[:16])}…</td>"
            f"<td>{html.escape(str(group.get('review_priority', '')))}</td>"
            f"<td>{int(group.get('count', 0) or 0)}</td>"
            f"<td>{fmt_size(int(group.get('potential_reclaimable_bytes', 0) or 0))}</td>"
            f"<td>{fmt_size(int(group.get('total_size_bytes', 0) or 0))}</td>"
            f"<td>{files_html}</td>"
            f"<td>{html.escape(str(group.get('status', '')))}</td>"
            "</tr>\n"
        )

    sort_section = (
        f"""
        <h2>Root Sort Candidates (first 200)</h2>
        <p>These are root-level files only. They are candidates for manual review, not move instructions.</p>
        <table>
          <thead><tr><th>Path</th><th>Category</th><th>Confidence</th><th>Proposed Destination</th><th>Status</th></tr></thead>
          <tbody>{sort_rows}</tbody>
        </table>
        """
        if sort_rows
        else "<h2>Root Sort Candidates</h2><p>No root-level sortable candidates found.</p>"
    )

    priority_section = (
        f"""
        <h2>Duplicate Review Priority Counts</h2>
        <table>
          <thead><tr><th>Priority</th><th>Groups</th></tr></thead>
          <tbody>{priority_rows}</tbody>
        </table>
        """
        if priority_rows
        else ""
    )

    duplicate_section = (
        f"""
        <h2>Exact Duplicate Groups (first 100, sorted by potential reclaimable size)</h2>
        <p>Exact duplicate candidates are based on identical SHA-256 hashes. Potential reclaimable size is theoretical and assumes keeping one copy; it is not a delete instruction.</p>
        <table>
          <thead><tr><th>SHA-256</th><th>Review Priority</th><th>Count</th><th>Potential Reclaimable</th><th>Total Size</th><th>Files</th><th>Status</th></tr></thead>
          <tbody>{duplicate_rows}</tbody>
        </table>
        """
        if duplicate_rows
        else "<h2>Exact Duplicate Groups</h2><p>No exact duplicate groups found.</p>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Archivio Personale AI — Proposed Actions Report</title>
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
  <h1>Archivio Personale AI — Proposed Actions Report</h1>
  <p><strong>Source:</strong> {source}</p>
  <p class="warning"><strong>Review only:</strong> this report asks what could be done. It does not move, rename, delete, overwrite, or reorganize any file. Files already inside folders remain protected by the keep_in_place policy.</p>

  <h2>Summary</h2>
  <div>
    <div class="stat">Total files<span>{total_files}</span></div>
    <div class="stat">Keep in place<span>{keep_in_place_count}</span></div>
    <div class="stat">Root candidates<span>{root_sort_count}</span></div>
    <div class="stat">Duplicate groups<span>{duplicate_groups_count}</span></div>
    <div class="stat">Duplicate files<span>{duplicate_files_count}</span></div>
    <div class="stat">Potential reclaimable<span>{fmt_size(potential_reclaimable)}</span></div>
  </div>

  {sort_section}
  {priority_section}
  {duplicate_section}
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a static HTML report from proposed actions JSON."
    )
    parser.add_argument("--input", required=True, help="Proposed actions JSON file path.")
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

    print(f"Proposed actions report written to: {output_path}")


if __name__ == "__main__":
    main()
