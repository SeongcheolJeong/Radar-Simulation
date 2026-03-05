#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class ReportFile:
    path: Path
    relpath: str
    mtime_epoch: float
    size_bytes: int
    group: str


def _resolve_path(base: Path, raw: str) -> Path:
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = (base / p).resolve()
    else:
        p = p.resolve()
    return p


def _iso_from_epoch(epoch: float) -> str:
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat()


def _group_for_name(name: str) -> str | None:
    if not name.endswith(".json"):
        return None
    if not name.startswith("radarsimpy_"):
        return None
    if "_checkpoint_" in name:
        prefix, tail = name.split("_checkpoint_", 1)
        token = tail[:-5]
        if token == "":
            return None
        if not token[0].isdigit():
            return None
        return prefix + "_checkpoint"
    if name.startswith("radarsimpy_progress_snapshot_"):
        token = name[len("radarsimpy_progress_snapshot_") : -5]
        if token == "":
            return None
        if not token[0].isdigit():
            return None
        return "radarsimpy_progress_snapshot"
    return None


def _discover_reports(reports_root: Path) -> List[ReportFile]:
    items: List[ReportFile] = []
    if not reports_root.exists():
        return items
    for path in reports_root.iterdir():
        if not path.is_file():
            continue
        group = _group_for_name(path.name)
        if group is None:
            continue
        stat = path.stat()
        items.append(
            ReportFile(
                path=path,
                relpath=str(path.relative_to(reports_root.parent)),
                mtime_epoch=float(stat.st_mtime),
                size_bytes=int(stat.st_size),
                group=group,
            )
        )
    return items


def _sort_newest_first(rows: Sequence[ReportFile]) -> List[ReportFile]:
    return sorted(rows, key=lambda r: (r.mtime_epoch, r.path.name), reverse=True)


def _plan_retention(
    rows: Sequence[ReportFile], keep_per_group: int
) -> Tuple[Dict[str, List[ReportFile]], Dict[str, List[ReportFile]]]:
    kept: Dict[str, List[ReportFile]] = {}
    pruned: Dict[str, List[ReportFile]] = {}

    group_rows: Dict[str, List[ReportFile]] = {}
    for row in rows:
        group_rows.setdefault(row.group, []).append(row)

    for group, values in sorted(group_rows.items()):
        ordered = _sort_newest_first(values)
        kept[group] = ordered[:keep_per_group]
        pruned[group] = ordered[keep_per_group:]

    return kept, pruned


def _sum_size(rows: Iterable[ReportFile]) -> int:
    return int(sum(int(r.size_bytes) for r in rows))


def _build_group_summary(
    group: str,
    kept_rows: Sequence[ReportFile],
    pruned_rows: Sequence[ReportFile],
) -> Dict[str, Any]:
    all_rows = list(kept_rows) + list(pruned_rows)
    ordered_all = _sort_newest_first(all_rows)
    newest = ordered_all[0] if ordered_all else None
    oldest = ordered_all[-1] if ordered_all else None
    return {
        "group": group,
        "total_count": len(all_rows),
        "kept_count": len(kept_rows),
        "prunable_count": len(pruned_rows),
        "total_size_bytes": _sum_size(all_rows),
        "prunable_size_bytes": _sum_size(pruned_rows),
        "newest": None
        if newest is None
        else {
            "path": newest.relpath,
            "mtime_utc": _iso_from_epoch(newest.mtime_epoch),
            "size_bytes": newest.size_bytes,
        },
        "oldest": None
        if oldest is None
        else {
            "path": oldest.relpath,
            "mtime_utc": _iso_from_epoch(oldest.mtime_epoch),
            "size_bytes": oldest.size_bytes,
        },
    }


def _apply_prune(rows: Sequence[ReportFile]) -> Tuple[int, List[str], List[str]]:
    deleted = 0
    deleted_paths: List[str] = []
    failed_paths: List[str] = []
    for row in rows:
        try:
            os.remove(row.path)
            deleted += 1
            deleted_paths.append(row.relpath)
        except OSError:
            failed_paths.append(row.relpath)
    return deleted, deleted_paths, failed_paths


def _render_markdown(payload: Mapping[str, Any]) -> str:
    summary = payload.get("summary", {})
    group_rows = payload.get("groups", [])
    action = payload.get("action", {})
    lines: List[str] = []
    lines.append("# RadarSimPy Report Retention Audit")
    lines.append("")
    lines.append(f"- generated_at_utc: {payload.get('generated_at_utc', '-')}")
    lines.append(f"- reports_root: {payload.get('reports_root', '-')}")
    lines.append(f"- keep_per_group: {payload.get('keep_per_group', '-')}")
    lines.append(f"- apply: {payload.get('apply', False)}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- matched_count: {summary.get('matched_count', 0)}")
    lines.append(f"- group_count: {summary.get('group_count', 0)}")
    lines.append(f"- total_size_bytes: {summary.get('total_size_bytes', 0)}")
    lines.append(f"- prunable_count: {summary.get('prunable_count', 0)}")
    lines.append(f"- prunable_size_bytes: {summary.get('prunable_size_bytes', 0)}")
    lines.append("")
    lines.append("## Action")
    lines.append("")
    lines.append(f"- deleted_count: {action.get('deleted_count', 0)}")
    lines.append(f"- failed_delete_count: {action.get('failed_delete_count', 0)}")
    lines.append("")
    lines.append("## Groups")
    lines.append("")
    for row in group_rows:
        lines.append(
            f"- {row.get('group')}: total={row.get('total_count')}, "
            f"kept={row.get('kept_count')}, prunable={row.get('prunable_count')}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit/prune RadarSimPy checkpoint report artifacts with per-group retention."
    )
    parser.add_argument("--reports-root", default="docs/reports")
    parser.add_argument("--keep-per-group", type=int, default=8)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete prunable files. Without this flag, only audit output is generated.",
    )
    parser.add_argument(
        "--output-json",
        default="docs/reports/radarsimpy_report_retention_audit_latest.json",
    )
    parser.add_argument(
        "--output-md",
        default="docs/reports/radarsimpy_report_retention_audit_latest.md",
    )
    args = parser.parse_args()

    if int(args.keep_per_group) < 1:
        raise ValueError("--keep-per-group must be >= 1")

    repo_root = Path.cwd().resolve()
    reports_root = _resolve_path(repo_root, str(args.reports_root))
    output_json = _resolve_path(repo_root, str(args.output_json))
    output_md = _resolve_path(repo_root, str(args.output_md))

    rows = _discover_reports(reports_root)
    kept, prunable = _plan_retention(rows, int(args.keep_per_group))

    prunable_all: List[ReportFile] = []
    groups_payload: List[Dict[str, Any]] = []
    for group in sorted(kept.keys()):
        kept_rows = kept.get(group, [])
        prune_rows = prunable.get(group, [])
        prunable_all.extend(prune_rows)
        groups_payload.append(_build_group_summary(group, kept_rows, prune_rows))

    deleted_count = 0
    deleted_paths: List[str] = []
    failed_paths: List[str] = []
    if bool(args.apply):
        deleted_count, deleted_paths, failed_paths = _apply_prune(prunable_all)

    payload: Dict[str, Any] = {
        "report_name": "radarsimpy_report_retention_audit",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reports_root": str(reports_root),
        "keep_per_group": int(args.keep_per_group),
        "apply": bool(args.apply),
        "summary": {
            "matched_count": len(rows),
            "group_count": len(groups_payload),
            "total_size_bytes": _sum_size(rows),
            "prunable_count": len(prunable_all),
            "prunable_size_bytes": _sum_size(prunable_all),
        },
        "groups": groups_payload,
        "action": {
            "deleted_count": int(deleted_count),
            "failed_delete_count": len(failed_paths),
            "deleted_paths": deleted_paths,
            "failed_paths": failed_paths,
        },
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")

    print("audit_radarsimpy_report_retention: done")
    print(f"  matched_count: {payload['summary']['matched_count']}")
    print(f"  group_count: {payload['summary']['group_count']}")
    print(f"  prunable_count: {payload['summary']['prunable_count']}")
    print(f"  apply: {payload['apply']}")
    print(f"  deleted_count: {payload['action']['deleted_count']}")
    print(f"  output_json: {output_json}")
    print(f"  output_md: {output_md}")


if __name__ == "__main__":
    main()
