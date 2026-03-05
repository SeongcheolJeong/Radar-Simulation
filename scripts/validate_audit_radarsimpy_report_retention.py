#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("json root must be object")
    return raw


def main() -> None:
    repo_root = Path.cwd().resolve()
    script = repo_root / "scripts" / "audit_radarsimpy_report_retention.py"
    if not script.exists():
        raise FileNotFoundError(script)

    with tempfile.TemporaryDirectory(prefix="retention_audit_test_") as td:
        root = Path(td)
        reports = root / "docs" / "reports"
        reports.mkdir(parents=True, exist_ok=True)

        # Group A: 5 checkpoint files
        for idx in range(5):
            _write_json(
                reports / f"radarsimpy_wrapper_integration_gate_checkpoint_2026_03_05T11330{idx}_000000Z_test.json",
                {"idx": idx},
            )
        # Group B: 3 checkpoint files
        for idx in range(3):
            _write_json(
                reports / f"radarsimpy_integration_smoke_gate_checkpoint_2026_03_05T11331{idx}_000000Z_test.json",
                {"idx": idx},
            )
        # Non-target file
        _write_json(reports / "radarsimpy_wrapper_integration_gate_production_latest.json", {"ok": True})

        output_json = root / "audit.json"
        output_md = root / "audit.md"

        cmd = [
            "python3",
            str(script),
            "--reports-root",
            str(reports),
            "--keep-per-group",
            "2",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout + "\n" + proc.stderr)

        payload = _load_json(output_json)
        summary = payload.get("summary", {})
        action = payload.get("action", {})
        if int(summary.get("matched_count", -1)) != 8:
            raise AssertionError("matched_count mismatch")
        if int(summary.get("group_count", -1)) != 2:
            raise AssertionError("group_count mismatch")
        if int(summary.get("prunable_count", -1)) != 4:
            raise AssertionError("prunable_count mismatch")
        if bool(payload.get("apply")):
            raise AssertionError("apply flag mismatch")
        if int(action.get("deleted_count", -1)) != 0:
            raise AssertionError("deleted_count mismatch for audit-only run")

        cmd_apply = cmd[:]
        cmd_apply.insert(-4, "--apply")
        proc_apply = subprocess.run(
            cmd_apply, cwd=str(repo_root), capture_output=True, text=True, check=False
        )
        if proc_apply.returncode != 0:
            raise RuntimeError(proc_apply.stdout + "\n" + proc_apply.stderr)

        payload_apply = _load_json(output_json)
        action_apply = payload_apply.get("action", {})
        if int(action_apply.get("deleted_count", -1)) != 4:
            raise AssertionError("deleted_count mismatch for apply run")
        if int(action_apply.get("failed_delete_count", -1)) != 0:
            raise AssertionError("failed_delete_count mismatch for apply run")

        remaining = sorted(p.name for p in reports.glob("radarsimpy_*_checkpoint_*.json"))
        if len(remaining) != 4:
            raise AssertionError(f"remaining checkpoint count mismatch: {remaining}")

    print("validate_audit_radarsimpy_report_retention: pass")


if __name__ == "__main__":
    main()
