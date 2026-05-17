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

    # Embed all duplicate groups as JSON for client-side filtering.
    groups_json = json.dumps(duplicate_groups, ensure_ascii=False)

    known_priorities = sorted({
        str(g.get("review_priority", "")) for g in duplicate_groups if g.get("review_priority")
    })
    priority_options = "\n".join(
        f'<option value="{html.escape(p)}">{html.escape(p)}</option>'
        for p in known_priorities
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
    .warning {{ padding: 1em; background: #fff6d8; border: 1px solid #e5c45b; margin-bottom: 1em; }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 1em; align-items: center;
                padding: 0.8em 1em; background: #f5f5f5; border: 1px solid #ddd;
                margin-bottom: 1em; border-radius: 4px; }}
    .filters label {{ font-size: 0.9em; }}
    .filters input[type=text] {{ padding: 4px 8px; border: 1px solid #bbb; border-radius: 3px; width: 260px; }}
    .filters select {{ padding: 4px 8px; border: 1px solid #bbb; border-radius: 3px; }}
    #group-count {{ font-weight: bold; color: #2255aa; }}
    #dup-tbody tr.hidden {{ display: none; }}
  </style>
</head>
<body>
  <h1>Archivio Personale AI — Proposed Actions Report</h1>
  <p><strong>Source:</strong> {source}</p>
  <p class="warning">
    <strong>Review only:</strong> this report asks what could be done. It does not move, rename,
    delete, overwrite, or reorganize any file. Files already inside folders remain protected by
    the keep_in_place policy.<br>
    <strong>Potential reclaimable size is theoretical</strong> — it assumes keeping one copy per
    group and is not a delete instruction. No deletion is proposed.<br>
    <strong>Context-bound files</strong> (inside project or work folders) require extra caution
    before any future manual action.
  </p>

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

  <h2>Exact Duplicate Groups (sorted by potential reclaimable size)</h2>
  <p>Exact duplicate candidates are based on identical SHA-256 hashes. All {duplicate_groups_count} groups are loaded; use the filters below to narrow the list.</p>

  <details style="margin-bottom:1em;padding:0.8em 1em;background:#eef4ff;border:1px solid #b3cce8;border-radius:4px;">
    <summary style="cursor:pointer;font-weight:bold;">How to use this report</summary>
    <ul style="margin:0.5em 0 0 1em;font-size:0.9em;">
      <li><strong>Search paths</strong> — type any part of a folder or file path to filter groups.</li>
      <li><strong>Priority</strong> — filter by review priority assigned to each duplicate group.</li>
      <li><strong>Context-bound</strong> — a file is context-bound when it lives inside an existing project or work folder; extra caution is needed before any future manual action.</li>
      <li><strong>Cross-folder</strong> — groups where duplicate copies span more than one top-level folder.</li>
      <li><strong>Same filename</strong> — groups where every duplicate file has the same filename.</li>
      <li><strong>Potential reclaimable</strong> is theoretical: it assumes keeping exactly one copy per group. It is not a delete instruction. No deletion is proposed.</li>
    </ul>
  </details>

  <div class="filters">
    <label>
      Search paths:&nbsp;
      <input type="text" id="path-filter" placeholder="type to filter by file path…">
    </label>
    <label>
      Priority:&nbsp;
      <select id="priority-filter">
        <option value="">all</option>
        {priority_options}
      </select>
    </label>
    <label>
      <input type="checkbox" id="cb-context-bound">
      show only groups with context-bound files
    </label>
    <label>
      <input type="checkbox" id="cb-reclaimable">
      show only groups with potential reclaimable &gt; 0
    </label>
    <label>
      <input type="checkbox" id="cb-cross-folder">
      show only groups spanning multiple top-level folders
    </label>
    <label>
      <input type="checkbox" id="cb-same-filename">
      show only groups where all files have the same filename
    </label>
    <span>Showing <span id="group-count">…</span> of {duplicate_groups_count} groups
      &nbsp;|&nbsp; Filtered potential reclaimable (theoretical): <span id="filtered-reclaimable">…</span>
    </span>
  </div>

  <table id="dup-table">
    <thead>
      <tr>
        <th>SHA-256</th>
        <th>Review Priority / Reason</th>
        <th>Count</th>
        <th>Potential Reclaimable</th>
        <th>Total Size</th>
        <th>Files</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody id="dup-tbody"></tbody>
  </table>

  <script>
  (function () {{
    var GROUPS = {groups_json};

    function fmtSize(bytes) {{
      var units = ["B","KB","MB","GB","TB"];
      var v = bytes;
      for (var i = 0; i < units.length; i++) {{
        if (v < 1024 || i === units.length - 1) return v.toFixed(1) + " " + units[i];
        v /= 1024;
      }}
    }}

    function escHtml(s) {{
      return String(s)
        .replace(/&/g,"&amp;").replace(/</g,"&lt;")
        .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
    }}

    function buildRow(g) {{
      var filesHtml = "<ul>" + g.files.map(function(f) {{
        return "<li>" +
          escHtml(f.relative_path) + " " +
          "[<em>" + escHtml(f.top_level_folder) + "</em>] " +
          "(" + escHtml(f.location_policy) + ", " +
          (f.context_bound ? "context-bound" : "not context-bound") + ", " +
          fmtSize(f.size_bytes || 0) + ")" +
          "</li>";
      }}).join("") + "</ul>";
      var sha = escHtml((g.sha256 || "").substring(0, 16)) + "…";
      var tr = document.createElement("tr");
      var topFolders = g.files.map(function(f){{return f.top_level_folder||"";}});
      var uniqueFolders = topFolders.filter(function(v,i){{return topFolders.indexOf(v)===i;}});
      var basenames = g.files.map(function(f){{
        var p = (f.relative_path||"").replace(/\\/g,"/");
        return p.split("/").pop().toLowerCase();
      }});
      var sameFilename = basenames.length > 0 && basenames.every(function(b){{return b===basenames[0];}});
      tr.setAttribute("data-priority", g.review_priority || "");
      tr.setAttribute("data-has-context", g.files.some(function(f){{return f.context_bound;}}) ? "1" : "0");
      tr.setAttribute("data-reclaimable", String(g.potential_reclaimable_bytes || 0));
      tr.setAttribute("data-paths", g.files.map(function(f){{return (f.relative_path||"").toLowerCase();}}).join("|"));
      tr.setAttribute("data-cross-folder", uniqueFolders.length > 1 ? "1" : "0");
      tr.setAttribute("data-same-filename", sameFilename ? "1" : "0");
      tr.innerHTML =
        "<td>" + sha + "</td>" +
        "<td>" + escHtml(g.review_priority || "") + "<br><small>" + escHtml(g.review_priority_reason || "") + "</small></td>" +
        "<td>" + (g.count || 0) + "</td>" +
        "<td>" + fmtSize(g.potential_reclaimable_bytes || 0) + "</td>" +
        "<td>" + fmtSize(g.total_size_bytes || 0) + "</td>" +
        "<td>" + filesHtml + "</td>" +
        "<td>" + escHtml(g.status || "") + "</td>";
      return tr;
    }}

    var tbody = document.getElementById("dup-tbody");
    var rows = GROUPS.map(buildRow);
    rows.forEach(function(r) {{ tbody.appendChild(r); }});

    function applyFilters() {{
      var pathQ = document.getElementById("path-filter").value.toLowerCase().trim();
      var prioQ = document.getElementById("priority-filter").value;
      var cbCtx = document.getElementById("cb-context-bound").checked;
      var cbRec = document.getElementById("cb-reclaimable").checked;
      var cbCross = document.getElementById("cb-cross-folder").checked;
      var cbSame = document.getElementById("cb-same-filename").checked;
      var visible = 0;
      var filteredReclaimable = 0;
      rows.forEach(function(r) {{
        var show = true;
        if (pathQ && r.getAttribute("data-paths").indexOf(pathQ) === -1) show = false;
        if (prioQ && r.getAttribute("data-priority") !== prioQ) show = false;
        if (cbCtx && r.getAttribute("data-has-context") !== "1") show = false;
        if (cbRec && parseInt(r.getAttribute("data-reclaimable"), 10) <= 0) show = false;
        if (cbCross && r.getAttribute("data-cross-folder") !== "1") show = false;
        if (cbSame && r.getAttribute("data-same-filename") !== "1") show = false;
        r.classList.toggle("hidden", !show);
        if (show) {{
          visible++;
          filteredReclaimable += parseInt(r.getAttribute("data-reclaimable"), 10) || 0;
        }}
      }});
      document.getElementById("group-count").textContent = visible;
      document.getElementById("filtered-reclaimable").textContent = fmtSize(filteredReclaimable);
    }}

    document.getElementById("path-filter").addEventListener("input", applyFilters);
    document.getElementById("priority-filter").addEventListener("change", applyFilters);
    document.getElementById("cb-context-bound").addEventListener("change", applyFilters);
    document.getElementById("cb-reclaimable").addEventListener("change", applyFilters);
    document.getElementById("cb-cross-folder").addEventListener("change", applyFilters);
    document.getElementById("cb-same-filename").addEventListener("change", applyFilters);

    applyFilters();
  }})();
  </script>
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
