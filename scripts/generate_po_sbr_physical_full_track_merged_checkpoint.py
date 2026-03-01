#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Generate merged PO-SBR physical full-track readiness checkpoint JSON "
            "from canonical local report artifacts."
        )
    )
    p.add_argument(
        "--output-json",
        default="docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json",
        help="Output checkpoint JSON path",
    )
    p.add_argument(
        "--merged-readiness-commit",
        default="406146de8e2f7f8504b93f0811f88c01093cc3b6",
        help="Merged readiness commit SHA (default: PR #4 merge commit)",
    )
    p.add_argument(
        "--merged-readiness-pr-number",
        type=int,
        default=4,
        help="Merged readiness pull request number (default: 4)",
    )
    p.add_argument(
        "--merged-readiness-pr-url",
        default="https://github.com/SeongcheolJeong/Radar-Simulation/pull/4",
        help="Merged readiness pull request URL",
    )
    return p.parse_args()


def _run_git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _required_path(raw: str, repo_root: Path) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    if not p.exists():
        raise FileNotFoundError(f"required file not found: {p}")
    return p


def _status(payload: Mapping[str, Any], key: str) -> str | None:
    v = str(payload.get(key, "")).strip()
    if v == "":
        return None
    return v


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()

    head_commit = _run_git(["rev-parse", "HEAD"], cwd=repo_root)
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    upstream = _run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo_root)

    snapshot_commit = _run_git(
        ["rev-parse", "po-sbr-physical-full-track-ready-2026-03-01^{}"], cwd=repo_root
    )
    merged_tag_commit = _run_git(
        ["rev-parse", "po-sbr-physical-full-track-ready-merged-2026-03-01^{}"], cwd=repo_root
    )
    canonical_tag_commit = _run_git(
        ["rev-parse", "po-sbr-physical-full-track-canonical-2026-03-01^{}"], cwd=repo_root
    )

    matrix_json = _required_path(
        "docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_fresh.json",
        repo_root=repo_root,
    )
    bundle_json = _required_path(
        "docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01_fresh.json",
        repo_root=repo_root,
    )
    gate_lock_json = _required_path(
        "docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh3.json",
        repo_root=repo_root,
    )

    matrix = _load_json(matrix_json)
    bundle = _load_json(bundle_json)
    gate_lock = _load_json(gate_lock_json)

    stability = gate_lock.get("stability")
    hardening = gate_lock.get("hardening")
    stability_map = dict(stability) if isinstance(stability, Mapping) else {}
    hardening_map = dict(hardening) if isinstance(hardening, Mapping) else {}

    status = {
        "matrix_status": _status(matrix, "matrix_status"),
        "full_track_status": _status(bundle, "full_track_status"),
        "gate_lock_status": _status(gate_lock, "gate_lock_status"),
        "stability_status": _status(stability_map, "campaign_status"),
        "hardening_status": _status(hardening_map, "hardening_status"),
        "realism_gate_candidate": _status(gate_lock, "realism_gate_candidate"),
        "realism_gate_candidate_status": _status(hardening_map, "realism_gate_candidate_status"),
    }

    ready = bool(
        status["matrix_status"] == "ready"
        and status["full_track_status"] == "ready"
        and status["gate_lock_status"] == "ready"
        and status["stability_status"] == "stable"
        and status["hardening_status"] == "hardened"
        and status["realism_gate_candidate_status"] == "ready"
    )

    output_json = Path(args.output_json).expanduser()
    if not output_json.is_absolute():
        output_json = (repo_root / output_json).resolve()
    else:
        output_json = output_json.resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "version": 3,
        "date_utc": "2026-03-01",
        "workspace_root": str(repo_root),
        "branch": branch,
        "upstream": upstream,
        "generated_from_head_commit": head_commit,
        "merged_readiness_commit": str(args.merged_readiness_commit).strip(),
        "merged_readiness_pr": {
            "number": int(args.merged_readiness_pr_number),
            "url": str(args.merged_readiness_pr_url).strip(),
            "state": "merged",
        },
        "tags": {
            "snapshot_tag": {
                "name": "po-sbr-physical-full-track-ready-2026-03-01",
                "commit": snapshot_commit,
            },
            "merged_tag": {
                "name": "po-sbr-physical-full-track-ready-merged-2026-03-01",
                "commit": merged_tag_commit,
            },
            "canonical_tag": {
                "name": "po-sbr-physical-full-track-canonical-2026-03-01",
                "commit": canonical_tag_commit,
            },
        },
        "artifacts": {
            "matrix_summary_json": str(matrix_json),
            "bundle_summary_json": str(bundle_json),
            "gate_lock_summary_json": str(gate_lock_json),
        },
        "status": status,
        "ready": ready,
    }

    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("generated merged full-track checkpoint")
    print(f"  output_json: {output_json}")
    print(f"  generated_from_head_commit: {head_commit}")
    print(f"  ready: {ready}")


if __name__ == "__main__":
    main()
