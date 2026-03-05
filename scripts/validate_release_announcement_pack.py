#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def _as_obj(v: Any, key: str) -> Mapping[str, Any]:
    if not isinstance(v, Mapping):
        raise ValueError(f"{key} must be object")
    return v


def _as_nonempty_str(v: Any, key: str) -> str:
    text = str(v).strip()
    if text == "":
        raise ValueError(f"{key} must be non-empty string")
    return text


def _as_bool(v: Any, key: str) -> bool:
    if not isinstance(v, bool):
        raise ValueError(f"{key} must be boolean")
    return bool(v)


def _as_nonneg_int(v: Any, key: str) -> int:
    if isinstance(v, bool):
        raise ValueError(f"{key} must be integer")
    if not isinstance(v, int):
        raise ValueError(f"{key} must be integer")
    if int(v) < 0:
        raise ValueError(f"{key} must be >= 0")
    return int(v)


def _resolve_path(repo_root: Path, raw: str) -> Path:
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    return p


def main() -> None:
    p = argparse.ArgumentParser(description="Validate release announcement pack contract")
    p.add_argument("--pack-json", default="docs/reports/release_announcement_pack_latest.json")
    p.add_argument("--repo-root", default=".")
    args = p.parse_args()

    repo_root = _resolve_path(Path.cwd(), str(args.repo_root))
    pack_path = _resolve_path(repo_root, str(args.pack_json))
    if not pack_path.exists():
        raise FileNotFoundError(f"pack json not found: {pack_path}")

    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    root = _as_obj(payload, "root")

    version = _as_nonempty_str(root.get("version"), "version")
    if version != "release_announcement_pack_v1":
        raise ValueError(f"version mismatch: {version}")

    status = _as_obj(root.get("status"), "status")
    sources = _as_obj(root.get("sources"), "sources")
    docs = _as_obj(root.get("docs"), "docs")
    templates = _as_obj(root.get("templates"), "templates")

    _as_nonempty_str(status.get("release_date"), "status.release_date")
    _as_nonempty_str(status.get("generated_at_utc"), "status.generated_at_utc")
    _as_nonempty_str(status.get("branch"), "status.branch")
    _as_nonempty_str(status.get("head_commit_short"), "status.head_commit_short")
    _as_nonempty_str(status.get("head_commit"), "status.head_commit")

    production_gate_ready = _as_bool(status.get("production_gate_ready"), "status.production_gate_ready")
    readiness_ready = _as_bool(status.get("readiness_ready"), "status.readiness_ready")
    parity_pass = _as_bool(status.get("parity_pass"), "status.parity_pass")
    frontend_e2e_pass = _as_bool(status.get("frontend_e2e_pass"), "status.frontend_e2e_pass")
    _as_bool(status.get("retention_audit_apply"), "status.retention_audit_apply")
    _as_nonneg_int(
        status.get("retention_audit_deleted_count"), "status.retention_audit_deleted_count"
    )
    _as_nonneg_int(
        status.get("retention_audit_failed_delete_count"),
        "status.retention_audit_failed_delete_count",
    )
    _as_nonneg_int(
        status.get("retention_audit_prunable_count"), "status.retention_audit_prunable_count"
    )
    overall_ready = _as_bool(status.get("overall_ready"), "status.overall_ready")

    expected_overall = bool(production_gate_ready and readiness_ready and parity_pass and frontend_e2e_pass)
    if overall_ready != expected_overall:
        raise ValueError(
            f"status.overall_ready mismatch: expected={expected_overall}, actual={overall_ready}"
        )

    for key in (
        "production_gate_json",
        "readiness_json",
        "parity_json",
        "frontend_e2e_json",
        "retention_audit_json",
    ):
        pth = _resolve_path(repo_root, _as_nonempty_str(sources.get(key), f"sources.{key}"))
        if not pth.exists() or not pth.is_file():
            raise FileNotFoundError(f"missing source file for {key}: {pth}")

    for key in ("release_notes", "onepager_en", "onepager_ko", "templates"):
        pth = _resolve_path(repo_root, _as_nonempty_str(docs.get(key), f"docs.{key}"))
        if not pth.exists() or not pth.is_file():
            raise FileNotFoundError(f"missing doc file for {key}: {pth}")

    for key in (
        "slack_en",
        "slack_ko",
        "email_subject_en",
        "email_subject_ko",
        "email_body_en",
        "email_body_ko",
    ):
        text = _as_nonempty_str(templates.get(key), f"templates.{key}")
        if len(text) < 20:
            raise ValueError(f"templates.{key} too short")

    print("validate_release_announcement_pack: pass")


if __name__ == "__main__":
    main()
