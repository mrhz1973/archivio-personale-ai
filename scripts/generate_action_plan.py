"""
Generate a dry-run action plan from inventory and classification JSON files.

The action plan is review-only. It never moves, renames, deletes, overwrites,
or reorganizes source archive files.

It proposes two safe kinds of information:
- root-level media/archive files that may be candidates for manual sorting;
- exact duplicate groups based on SHA-256 hashes, for manual review only.
"""

import argparse
import json
import sys
from pathlib import PurePosixPath, Path
from typing import Any


ROOT_SORTABLE_CATEGORIES = {
    "Images": "Foto",
    "Videos": "Video",
    "Audio": "Audio",
    "Archives": "Archivi",
    "Books": "Libri",
}


def normalize_relative_path(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def is_root_file(relative_path: str) -> bool:
    normalized = normalize_relative_path(relative_path)
    if not normalized:
        return False
    return PurePosixPath(normalized).parent == PurePosixPath(".")


def build_classification_lookup(classifications_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = classifications_data.get("classifications", [])
    if not isinstance(items, list):
        raise ValueError("Invalid classifications JSON: 'classifications' must be a list.")
    lookup: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        rel = normalize_relative_path(str(item.get("relative_path", "")))
        if rel:
            lookup[rel] = item
    return lookup


def build_inventory_lookup(inventory_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = inventory_data.get("files", [])
    if not isinstance(items, list):
        raise ValueError("Invalid inventory JSON: 'files' must be a list.")
    lookup: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        rel = normalize_relative_path(str(item.get("relative_path", "")))
        if rel:
            lookup[rel] = item
    return lookup


def proposed_destination(folder: str, relative_path: str) -> str:
    filename = PurePosixPath(normalize_relative_path(relative_path)).name
    return str(PurePosixPath(folder) / filename)


def build_sort_candidates(
    inventory_lookup: dict[str, dict[str, Any]],
    classification_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for rel, info in sorted(inventory_lookup.items()):
        classification = classification_lookup.get(rel, {})
        category = str(classification.get("category", "Misc"))
        location_policy = str(classification.get("location_policy", "classify_only"))

        if location_policy != "classify_only":
            continue
        if not is_root_file(rel):
            continue
        if category not in ROOT_SORTABLE_CATEGORIES:
            continue

        target_folder = ROOT_SORTABLE_CATEGORIES[category]
        candidates.append(
            {
                "action_type": "root_sort_candidate",
                "status": "requires_manual_approval",
                "relative_path": rel,
                "category": category,
                "confidence": float(classification.get("confidence", 0) or 0),
                "proposed_destination_relative_path": proposed_destination(target_folder, rel),
                "reason": "Root-level file in a safe sortable category. This is a suggestion only.",
                "dry_run_only": True,
            }
        )

    return candidates


def build_duplicate_groups(
    inventory_lookup: dict[str, dict[str, Any]],
    classification_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_hash: dict[str, list[dict[str, Any]]] = {}

    for rel, info in inventory_lookup.items():
        digest = str(info.get("sha256", ""))
        if not digest:
            continue
        by_hash.setdefault(digest, []).append(info)

    groups: list[dict[str, Any]] = []
    for digest, files in by_hash.items():
        if len(files) < 2:
            continue

        file_entries = []
        total_size = 0
        for info in sorted(files, key=lambda item: normalize_relative_path(str(item.get("relative_path", "")))):
            rel = normalize_relative_path(str(info.get("relative_path", "")))
            size = int(info.get("size_bytes", 0) or 0)
            total_size += size
            classification = classification_lookup.get(rel, {})
            file_entries.append(
                {
                    "relative_path": rel,
                    "size_bytes": size,
                    "category": classification.get("category", "Misc"),
                    "location_policy": classification.get("location_policy", "classify_only"),
                    "context_bound": bool(classification.get("context_bound", False)),
                }
            )

        groups.append(
            {
                "action_type": "duplicate_group",
                "status": "review_only",
                "sha256": digest,
                "count": len(file_entries),
                "total_size_bytes": total_size,
                "files": file_entries,
                "reason": "Exact duplicate candidates based on identical SHA-256. Review manually; no deletion is proposed.",
                "dry_run_only": True,
            }
        )

    return sorted(groups, key=lambda group: (group["count"], group["total_size_bytes"]), reverse=True)


def build_action_plan(inventory_data: dict[str, Any], classifications_data: dict[str, Any]) -> dict[str, Any]:
    inventory_lookup = build_inventory_lookup(inventory_data)
    classification_lookup = build_classification_lookup(classifications_data)

    sort_candidates = build_sort_candidates(inventory_lookup, classification_lookup)
    duplicate_groups = build_duplicate_groups(inventory_lookup, classification_lookup)

    policy_counts = classifications_data.get("summary", {}).get("location_policy_counts", {})
    duplicate_files_count = sum(int(group["count"]) for group in duplicate_groups)

    return {
        "summary": {
            "source": inventory_data.get("summary", {}).get("source", ""),
            "total_files": len(inventory_lookup),
            "root_sort_candidates_count": len(sort_candidates),
            "duplicate_groups_count": len(duplicate_groups),
            "duplicate_files_count": duplicate_files_count,
            "keep_in_place_count": int(policy_counts.get("keep_in_place", 0) or 0),
            "classify_only_count": int(policy_counts.get("classify_only", 0) or 0),
            "dry_run_only": True,
        },
        "root_sort_candidates": sort_candidates,
        "duplicate_groups": duplicate_groups,
        "errors": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a review-only action plan for Archivio Personale AI."
    )
    parser.add_argument("--inventory", required=True, help="Input inventory JSON path.")
    parser.add_argument("--classifications", required=True, help="Input classifications JSON path.")
    parser.add_argument("--output", required=True, help="Output proposed actions JSON path.")
    args = parser.parse_args()

    inventory_path = Path(args.inventory).resolve()
    classifications_path = Path(args.classifications).resolve()
    output_path = Path(args.output).resolve()

    for label, path in (("inventory", inventory_path), ("classifications", classifications_path)):
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    with inventory_path.open("r", encoding="utf-8") as fp:
        inventory_data = json.load(fp)
    with classifications_path.open("r", encoding="utf-8") as fp:
        classifications_data = json.load(fp)

    result = build_action_plan(inventory_data, classifications_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2, ensure_ascii=False)

    summary = result["summary"]
    print(f"Action plan written to: {output_path}")
    print(
        "Root sort candidates: "
        f"{summary['root_sort_candidates_count']}, "
        f"duplicate groups: {summary['duplicate_groups_count']}, "
        f"duplicate files: {summary['duplicate_files_count']}"
    )


if __name__ == "__main__":
    main()
