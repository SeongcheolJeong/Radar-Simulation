#!/usr/bin/env python3
"""Validate pre-push hook local-artifact mode does not modify tracked reports."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, List


TRACKED_REPORTS = [
    "docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json",
    "docs/reports/po_sbr_operator_handoff_closure_2026_03_01.json",
    "docs/reports/po_sbr_post_change_gate_2026_03_01.json",
    "docs/reports/po_sbr_progress_snapshot_2026_03_01.json",
]

HOOK_REPORTS = {
    "post_change_gate": ".git/po_sbr_post_change_gate_hook_latest.json",
    "merged_checkpoint": ".git/po_sbr_physical_full_track_merged_checkpoint_hook_latest.json",
    "operator_handoff_closure": ".git/po_sbr_operator_handoff_closure_hook_latest.json",
}


def _run(repo_root: Path, args: List[str]) -> str:
    out = subprocess.check_output(args, cwd=str(repo_root), text=True)
    return out.strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_json(path: Path) -> Dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    hook_path = repo_root / ".githooks/pre-push"
    if not hook_path.exists():
        raise FileNotFoundError(f"missing pre-push hook: {hook_path}")

    tracked_paths = [repo_root / rel for rel in TRACKED_REPORTS]
    for path in tracked_paths:
        if not path.exists():
            raise FileNotFoundError(f"missing tracked report: {path}")

    before = {str(path): _sha256(path) for path in tracked_paths}

    branch = _run(repo_root, ["git", "branch", "--show-current"])
    head = _run(repo_root, ["git", "rev-parse", "HEAD"])
    base = _run(repo_root, ["git", "rev-parse", "HEAD~1"])
    stdin_line = (
        f"refs/heads/{branch} {head} "
        f"refs/heads/{branch} {base}\n"
    )

    proc = subprocess.run(
        ["bash", str(hook_path)],
        cwd=str(repo_root),
        input=stdin_line,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "pre-push hook simulation failed:\n"
            f"return_code={proc.returncode}\n"
            f"stdout={proc.stdout}\n"
            f"stderr={proc.stderr}"
        )

    after = {str(path): _sha256(path) for path in tracked_paths}
    changed = [
        path for path in sorted(before.keys())
        if before[path] != after[path]
    ]
    if changed:
        joined = "\n".join(changed)
        raise RuntimeError(
            "tracked reports were modified by hook run:\n"
            f"{joined}"
        )

    post_change_path = repo_root / HOOK_REPORTS["post_change_gate"]
    merged_path = repo_root / HOOK_REPORTS["merged_checkpoint"]
    closure_path = repo_root / HOOK_REPORTS["operator_handoff_closure"]
    for path in (post_change_path, merged_path, closure_path):
        if not path.exists():
            raise FileNotFoundError(f"missing hook artifact: {path}")

    post_change = _load_json(post_change_path)
    merged = _load_json(merged_path)
    closure = _load_json(closure_path)

    if str(post_change.get("overall_status", "")) != "ready":
        raise RuntimeError("hook post-change gate overall_status is not ready")
    if str(post_change.get("closure_status", "")) not in {"pass", "skipped"}:
        raise RuntimeError("hook post-change gate closure_status is not pass/skipped")
    if not bool(merged.get("ready", False)):
        raise RuntimeError("hook merged checkpoint ready=false")
    if str(closure.get("overall_status", "")) != "ready":
        raise RuntimeError("hook closure overall_status is not ready")

    print("validate_po_sbr_pre_push_hook_local_artifacts: pass")
    print(f"  simulated_branch: {branch}")
    print(f"  simulated_head: {head}")
    print(f"  simulated_base: {base}")
    print(f"  hook_post_change_json: {post_change_path}")
    print(f"  hook_merged_checkpoint_json: {merged_path}")
    print(f"  hook_closure_json: {closure_path}")
    print("  tracked_report_changes: 0")


if __name__ == "__main__":
    main()

