#!/usr/bin/env python3
"""Run PO-SBR operator closure gate only when runtime-affecting files changed."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List


RUNTIME_AFFECTING_PREFIXES = (
    "src/avxsim/",
    "frontend/graph_lab/",
)

RUNTIME_AFFECTING_FILE_PREFIXES = (
    "scripts/run_po_sbr_",
    "scripts/validate_po_sbr_",
    "scripts/verify_po_sbr_",
    "scripts/run_scene_backend_",
    "scripts/validate_scene_backend_",
)

RUNTIME_AFFECTING_EXACT_FILES = {
    "scripts/validate_web_e2e_orchestrator_api.py",
    "scripts/generate_po_sbr_physical_full_track_merged_checkpoint.py",
    "scripts/verify_po_sbr_operator_handoff_closure.sh",
    "scripts/verify_po_sbr_physical_full_track_merged_ready.sh",
    "src/avxsim/web_e2e_api.py",
}

MAX_CAPTURE_CHARS = 12000


def _run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _changed_files(repo_root: Path, base_ref: str, head_ref: str) -> List[str]:
    proc = _run_cmd(
        ["git", "diff", "--name-only", f"{base_ref}..{head_ref}"],
        cwd=repo_root,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "git diff failed for changed-file discovery:\n"
            f"cmd=git diff --name-only {base_ref}..{head_ref}\n"
            f"stderr={proc.stderr.strip()}"
        )
    rows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    dedup: List[str] = []
    seen = set()
    for row in rows:
        if row in seen:
            continue
        dedup.append(row)
        seen.add(row)
    return dedup


def _is_runtime_affecting(path: str) -> bool:
    if path.startswith("docs/") or path.startswith("data/"):
        return False
    if path in RUNTIME_AFFECTING_EXACT_FILES:
        return True
    for pref in RUNTIME_AFFECTING_PREFIXES:
        if path.startswith(pref):
            return True
    for pref in RUNTIME_AFFECTING_FILE_PREFIXES:
        if path.startswith(pref):
            return True
    return False


def _truncate_text(text: str, max_chars: int = MAX_CAPTURE_CHARS) -> str:
    raw = str(text)
    if len(raw) <= int(max_chars):
        return raw
    tail = raw[-int(max_chars) :]
    omitted = len(raw) - int(max_chars)
    return f"[truncated {omitted} chars]\n{tail}"


def parse_args() -> argparse.Namespace:
    stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    p = argparse.ArgumentParser(
        description=(
            "Detect runtime-affecting changes in this repo and run PO-SBR operator "
            "handoff closure gate only when required."
        )
    )
    p.add_argument("--base-ref", default="HEAD~1", help="Base git ref for diff (default: HEAD~1)")
    p.add_argument("--head-ref", default="HEAD", help="Head git ref for diff (default: HEAD)")
    p.add_argument(
        "--output-json",
        default=f"docs/reports/po_sbr_post_change_gate_{stamp}.json",
        help="Output report JSON path",
    )
    p.add_argument(
        "--closure-script",
        default="scripts/verify_po_sbr_operator_handoff_closure.sh",
        help="Closure verifier script path",
    )
    p.add_argument(
        "--force-run",
        action="store_true",
        help="Run closure verifier even if no runtime-affecting changes were detected",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when closure execution is required and it fails",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()

    changed = _changed_files(
        repo_root=repo_root,
        base_ref=str(args.base_ref),
        head_ref=str(args.head_ref),
    )
    runtime_affecting = [path for path in changed if _is_runtime_affecting(path)]
    required = bool(runtime_affecting) or bool(args.force_run)

    closure_script = Path(str(args.closure_script))
    if not closure_script.is_absolute():
        closure_script = (repo_root / closure_script).resolve()

    closure_cmd = ["bash", str(closure_script)]
    closure_proc = None
    closure_status = "skipped"
    if required:
        closure_proc = _run_cmd(closure_cmd, cwd=repo_root)
        closure_status = "pass" if closure_proc.returncode == 0 else "fail"

    output_json = Path(str(args.output_json))
    if not output_json.is_absolute():
        output_json = (repo_root / output_json).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "report_name": "po_sbr_post_change_gate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "base_ref": str(args.base_ref),
        "head_ref": str(args.head_ref),
        "changed_files": changed,
        "runtime_affecting_files": runtime_affecting,
        "closure_required": required,
        "forced": bool(args.force_run),
        "closure_script": str(closure_script),
        "closure_status": closure_status,
        "closure_return_code": (
            int(closure_proc.returncode) if closure_proc is not None else None
        ),
        "closure_stdout": (
            _truncate_text(closure_proc.stdout) if closure_proc is not None else ""
        ),
        "closure_stderr": (
            _truncate_text(closure_proc.stderr) if closure_proc is not None else ""
        ),
        "overall_status": (
            "ready"
            if (not required or closure_status == "pass")
            else "blocked"
        ),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"wrote {output_json}")
    print(f"closure_required={required}")
    print(f"closure_status={closure_status}")
    print(f"overall_status={payload['overall_status']}")

    if bool(args.strict) and required and closure_status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
