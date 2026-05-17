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


_PRIORITY_LABELS = {
    "review_only": "solo revisione",
    "higher_review_value": "priorità alta di revisione",
    "medium_review": "priorità media",
    "low_context_risk_review": "rischio contesto basso / verifica prudente",
    "manual_review": "revisione manuale",
    "keep_in_place": "mantieni nella posizione attuale",
    "classify_only": "solo classificazione",
}


def _priority_label(value: str) -> str:
    return _PRIORITY_LABELS.get(value, value)


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
        <h2>Candidati ordinamento radice (primi 200)</h2>
        <p>Solo file nella cartella radice. Sono candidati per revisione manuale, non istruzioni di spostamento.</p>
        <table>
          <thead><tr><th>Percorso</th><th>Categoria</th><th>Confidenza</th><th>Destinazione proposta</th><th>Stato</th></tr></thead>
          <tbody>{sort_rows}</tbody>
        </table>
        """
        if sort_rows
        else "<h2>Candidati ordinamento radice</h2><p>Nessun candidato trovato nella radice.</p>"
    )

    priority_section = (
        f"""
        <h2>Conteggio priorità revisione duplicati</h2>
        <table>
          <thead><tr><th>Priorità</th><th>Gruppi</th></tr></thead>
          <tbody>{priority_rows}</tbody>
        </table>
        """
        if priority_rows
        else ""
    )

    # Embed duplicate groups as JSON in a non-executable script element.
    # Replacing "</" with "<\/" prevents the HTML parser from closing the element prematurely.
    _groups_raw = json.dumps(duplicate_groups, ensure_ascii=False)
    groups_json_str = _groups_raw.replace("</", "<\\/")

    known_priorities = sorted({
        str(g.get("review_priority", "")) for g in duplicate_groups if g.get("review_priority")
    })
    priority_options = "\n".join(
        f'<option value="{html.escape(p)}">{html.escape(p)}</option>'
        for p in known_priorities
    )

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Archivio Personale AI — Report Azioni Proposte</title>
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
    .filters button {{ padding: 4px 10px; border: 1px solid #bbb; border-radius: 3px; background: #fff; cursor: pointer; font-size: 0.9em; }}
    #group-count {{ font-weight: bold; color: #2255aa; }}
    #dup-tbody tr.hidden {{ display: none; }}
    #dup-empty-state {{ color: #888; font-style: italic; margin-top: 0.5em; display: none; }}
  </style>
</head>
<body>
  <h1>Archivio Personale AI — Report Azioni Proposte</h1>
  <p><strong>Origine:</strong> {source}</p>
  <p class="warning">
    <strong>Solo revisione:</strong> questo report illustra cosa potrebbe essere fatto. Non sposta, rinomina,
    cancella, sovrascrive o riorganizza alcun file. I file già dentro cartelle rimangono protetti
    dalla politica keep_in_place.<br>
    <strong>Lo spazio recuperabile è solo teorico</strong> — assume di mantenere una copia per gruppo
    e non è un'istruzione di cancellazione. Nessuna cancellazione è proposta.<br>
    <strong>File dentro cartelle/progetti</strong> richiedono cautela extra prima di qualsiasi azione manuale futura.
  </p>

  <h2>Riepilogo</h2>
  <div>
    <div class="stat">File totali<span>{total_files}</span></div>
    <div class="stat">Mantieni nella posizione attuale<span>{keep_in_place_count}</span></div>
    <div class="stat">Candidati radice<span>{root_sort_count}</span></div>
    <div class="stat">Gruppi duplicati<span>{duplicate_groups_count}</span></div>
    <div class="stat">File duplicati<span>{duplicate_files_count}</span></div>
    <div class="stat">Spazio teorico recuperabile<span>{fmt_size(potential_reclaimable)}</span></div>
  </div>

  {sort_section}
  {priority_section}

  <h2>Gruppi duplicati esatti (ordinati per spazio teorico recuperabile)</h2>
  <p>I duplicati esatti si basano su hash SHA-256 identici. Tutti i {duplicate_groups_count} gruppi sono caricati; usa i filtri per restringere la lista.</p>

  <details style="margin-bottom:1em;padding:0.8em 1em;background:#eef4ff;border:1px solid #b3cce8;border-radius:4px;">
    <summary style="cursor:pointer;font-weight:bold;">Come usare questo report</summary>
    <ul style="margin:0.5em 0 0 1em;font-size:0.9em;">
      <li><strong>Cerca nei percorsi</strong> — digita parte di un percorso per filtrare i gruppi.</li>
      <li><strong>Priorità</strong> — filtra per priorità di revisione assegnata a ciascun gruppo.</li>
      <li><strong>File dentro cartelle/progetti</strong> — un file è dentro un progetto quando si trova in una cartella esistente; serve cautela extra prima di qualsiasi azione manuale futura.</li>
      <li><strong>Cross-folder</strong> — gruppi in cui le copie duplicate si trovano in più cartelle principali.</li>
      <li><strong>Stesso nome file</strong> — gruppi in cui tutti i file duplicati hanno lo stesso nome.</li>
      <li><strong>Spazio recuperabile</strong> è teorico: assume di tenere esattamente una copia per gruppo. Non è un'istruzione di cancellazione. Nessuna cancellazione è proposta.</li>
    </ul>
  </details>

  <div class="filters">
    <label>
      Cerca nei percorsi:&nbsp;
      <input type="text" id="path-filter" placeholder="digita per filtrare per percorso…">
    </label>
    <label>
      Priorità:&nbsp;
      <select id="priority-filter">
        <option value="">tutti</option>
        {priority_options}
      </select>
    </label>
    <label>
      <input type="checkbox" id="cb-context-bound">
      mostra solo gruppi con file dentro cartelle/progetti
    </label>
    <label>
      <input type="checkbox" id="cb-reclaimable">
      mostra solo gruppi con spazio teorico recuperabile &gt; 0
    </label>
    <label>
      <input type="checkbox" id="cb-cross-folder">
      mostra solo gruppi presenti in più cartelle principali
    </label>
    <label>
      <input type="checkbox" id="cb-same-filename">
      mostra solo gruppi dove tutti i file hanno lo stesso nome
    </label>
    <button id="btn-reset-filters" type="button">Azzera filtri</button>
    <span>Visualizzati <span id="group-count">…</span> di {duplicate_groups_count} gruppi
      &nbsp;|&nbsp; Spazio teorico recuperabile (filtrato): <span id="filtered-reclaimable">…</span>
    </span>
  </div>

  <table id="dup-table">
    <thead>
      <tr>
        <th>SHA-256</th>
        <th>Priorità revisione / Motivo</th>
        <th>Conteggio</th>
        <th>Spazio teorico recuperabile</th>
        <th>Dimensione totale</th>
        <th>File</th>
        <th>Stato</th>
      </tr>
    </thead>
    <tbody id="dup-tbody"></tbody>
  </table>
  <p id="dup-empty-state">Nessun gruppo duplicato corrisponde ai filtri selezionati.</p>

  <script type="application/json" id="dup-data">{groups_json_str}</script>
  <script>
  (function () {{
    var GROUPS = JSON.parse(document.getElementById('dup-data').textContent);

    var PRIORITY_LABELS = {{
      "review_only": "solo revisione",
      "higher_review_value": "priorità alta di revisione",
      "medium_review": "priorità media",
      "low_context_risk_review": "rischio contesto basso / verifica prudente",
      "manual_review": "revisione manuale",
      "keep_in_place": "mantieni nella posizione attuale",
      "classify_only": "solo classificazione"
    }};

    function priorityLabel(v) {{
      return PRIORITY_LABELS[v] || v;
    }}

    function fmtSize(bytes) {{
      var v = Number(bytes) || 0;
      var units = ["B","KB","MB","GB","TB"];
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
      var files = g.files || [];
      var filesHtml = "<ul>" + files.map(function(f) {{
        var folder = f.top_level_folder;
        var folderHtml = folder ? "[<em>" + escHtml(folder) + "</em>] " : "";
        return "<li>" +
          escHtml(f.relative_path || "") + " " +
          folderHtml +
          "(" + priorityLabel(escHtml(f.location_policy || "")) + ", " +
          (f.context_bound ? "dentro cartella/progetto" : "non in cartella/progetto") + ", " +
          fmtSize(f.size_bytes || 0) + ")" +
          "</li>";
      }}).join("") + "</ul>";
      var sha = escHtml((g.sha256 || "").substring(0, 16)) + "…";
      var tr = document.createElement("tr");
      var topFolders = files.map(function(f){{return f.top_level_folder||"";}});
      var uniqueFolders = topFolders.filter(function(v,i){{return topFolders.indexOf(v)===i;}});
      var basenames = files.map(function(f){{
        var p = (f.relative_path||"").replace(/\\/g,"/");
        return p.split("/").pop().toLowerCase();
      }});
      var sameFilename = basenames.length > 0 && basenames.every(function(b){{return b===basenames[0];}});
      tr.setAttribute("data-priority", g.review_priority || "");
      tr.setAttribute("data-has-context", files.some(function(f){{return f.context_bound;}}) ? "1" : "0");
      tr.setAttribute("data-reclaimable", String(g.potential_reclaimable_bytes || 0));
      tr.setAttribute("data-paths", files.map(function(f){{return (f.relative_path||"").toLowerCase();}}).join("|"));
      tr.setAttribute("data-cross-folder", uniqueFolders.length > 1 ? "1" : "0");
      tr.setAttribute("data-same-filename", sameFilename ? "1" : "0");
      tr.innerHTML =
        "<td>" + sha + "</td>" +
        "<td>" + priorityLabel(escHtml(g.review_priority || "")) + "<br><small>" + escHtml(g.review_priority_reason || "") + "</small></td>" +
        "<td>" + (g.count || 0) + "</td>" +
        "<td>" + fmtSize(g.potential_reclaimable_bytes || 0) + "</td>" +
        "<td>" + fmtSize(g.total_size_bytes || 0) + "</td>" +
        "<td>" + filesHtml + "</td>" +
        "<td>" + priorityLabel(escHtml(g.status || "")) + "</td>";
      return tr;
    }}

    var tbody = document.getElementById("dup-tbody");
    var emptyState = document.getElementById("dup-empty-state");
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
      emptyState.style.display = visible === 0 ? "" : "none";
    }}

    document.getElementById("path-filter").addEventListener("input", applyFilters);
    document.getElementById("priority-filter").addEventListener("change", applyFilters);
    document.getElementById("cb-context-bound").addEventListener("change", applyFilters);
    document.getElementById("cb-reclaimable").addEventListener("change", applyFilters);
    document.getElementById("cb-cross-folder").addEventListener("change", applyFilters);
    document.getElementById("cb-same-filename").addEventListener("change", applyFilters);
    document.getElementById("btn-reset-filters").addEventListener("click", function() {{
      document.getElementById("path-filter").value = "";
      document.getElementById("priority-filter").value = "";
      document.getElementById("cb-context-bound").checked = false;
      document.getElementById("cb-reclaimable").checked = false;
      document.getElementById("cb-cross-folder").checked = false;
      document.getElementById("cb-same-filename").checked = false;
      applyFilters();
    }});

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
