#!/usr/bin/env python3
"""Show RadarSimPy integration readiness and next actions from local artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def _latest_file(paths: Sequence[Path]) -> Optional[Path]:
    files = [p for p in paths if p.exists() and p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _glob_latest(base: Path, patterns: Sequence[str]) -> Optional[Path]:
    out: List[Path] = []
    for pattern in patterns:
        out.extend(base.glob(pattern))
    return _latest_file(out)


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _run_git(repo_root: Path, args: List[str]) -> Tuple[bool, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


def _bool(v: Any) -> bool:
    return bool(v)


def _status_str(v: Any) -> str:
    return str(v).strip()


def _build_stage(
    name: str,
    source_json: Optional[Path],
    ready: bool,
    details: Dict[str, Any],
) -> Dict[str, Any]:
    status = "ready" if ready else "blocked"
    if source_json is None and _status_str(details.get("reason", "")) == "report_not_found":
        status = "missing"
    return {
        "name": name,
        "status": status,
        "ready": bool(ready),
        "source_json": str(source_json) if source_json is not None else None,
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Print RadarSimPy integration progress from latest local reports and "
            "suggest next actions."
        )
    )
    p.add_argument("--reports-root", default="docs/reports")
    p.add_argument("--smoke-summary-json", default="")
    p.add_argument("--wrapper-summary-json", default="")
    p.add_argument("--migration-summary-json", default="")
    p.add_argument("--e2e-rollup-json", default="")
    p.add_argument("--output-json", default="")
    p.add_argument("--strict-ready", action="store_true")
    return p.parse_args()


def _resolve_optional_path(raw: str, repo_root: Path) -> Optional[Path]:
    text = str(raw).strip()
    if text == "":
        return None
    p = Path(text).expanduser()
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    return p


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()
    reports_root = Path(str(args.reports_root))
    if not reports_root.is_absolute():
        reports_root = (repo_root / reports_root).resolve()
    else:
        reports_root = reports_root.resolve()

    git_dir = repo_root / ".git"

    smoke_path = _resolve_optional_path(args.smoke_summary_json, repo_root=repo_root)
    if smoke_path is None:
        smoke_path = _latest_file(
            [
                git_dir / "radarsimpy_integration_smoke_gate_hook_latest.json",
            ]
        )
        if smoke_path is None:
            smoke_path = _glob_latest(
                reports_root,
                [
                    "radarsimpy_integration_smoke_gate*.json",
                    "**/radarsimpy_integration_smoke_gate*.json",
                ],
            )

    wrapper_path = _resolve_optional_path(args.wrapper_summary_json, repo_root=repo_root)
    if wrapper_path is None:
        wrapper_path = _latest_file(
            [
                git_dir / "radarsimpy_wrapper_integration_gate_hook_latest.json",
            ]
        )
        if wrapper_path is None:
            wrapper_path = _glob_latest(
                reports_root,
                [
                    "radarsimpy_wrapper_integration_gate*.json",
                    "radarsimpy_wrapper_integration_gate_real/summary*.json",
                    "**/radarsimpy_wrapper_integration_gate*.json",
                ],
            )

    migration_path = _resolve_optional_path(args.migration_summary_json, repo_root=repo_root)
    if migration_path is None:
        migration_path = _glob_latest(
            reports_root,
            [
                "radarsimpy_migration_stepwise*/summary.json",
                "integration_full_real_e2e_*/radarsimpy_migration_stepwise_summary.json",
            ],
        )

    e2e_rollup_path = _resolve_optional_path(args.e2e_rollup_json, repo_root=repo_root)
    if e2e_rollup_path is None:
        e2e_rollup_path = _glob_latest(
            reports_root,
            [
                "integration_full_real_e2e_*/_status_rollup.json",
            ],
        )

    stages: List[Dict[str, Any]] = []
    next_actions: List[str] = []

    if smoke_path is None:
        stages.append(
            _build_stage(
                name="integration_smoke_gate",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run: PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_integration_smoke_gate.py "
            "--output-summary-json docs/reports/radarsimpy_integration_smoke_gate_manual.json"
        )
    else:
        smoke = _load_json(smoke_path)
        smoke_ready = _bool(smoke.get("pass"))
        stages.append(
            _build_stage(
                name="integration_smoke_gate",
                source_json=smoke_path,
                ready=smoke_ready,
                details={
                    "pass": _bool(smoke.get("pass")),
                    "step_count": int(smoke.get("step_count", 0)),
                    "pass_count": int(smoke.get("pass_count", 0)),
                    "fail_count": int(smoke.get("fail_count", 0)),
                },
            )
        )
        if not smoke_ready:
            next_actions.append(
                "Run: PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_integration_smoke_gate.py "
                "--output-summary-json docs/reports/radarsimpy_integration_smoke_gate_manual.json"
            )

    if wrapper_path is None:
        stages.append(
            _build_stage(
                name="wrapper_integration_gate",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run: PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py "
            "--output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json"
        )
    else:
        wrapper = _load_json(wrapper_path)
        wrapper_ready = _bool(wrapper.get("pass"))
        stages.append(
            _build_stage(
                name="wrapper_integration_gate",
                source_json=wrapper_path,
                ready=wrapper_ready,
                details={
                    "pass": _bool(wrapper.get("pass")),
                    "check_count": int(wrapper.get("check_count", 0)),
                    "pass_count": int(wrapper.get("pass_count", 0)),
                    "fail_count": int(wrapper.get("fail_count", 0)),
                    "with_real_runtime": _bool(wrapper.get("with_real_runtime")),
                },
            )
        )
        if not wrapper_ready:
            next_actions.append(
                "Run: PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py "
                "--output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json"
            )

    if migration_path is None:
        stages.append(
            _build_stage(
                name="migration_stepwise",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run: PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_migration_stepwise.py "
            "--output-root docs/reports/radarsimpy_migration_stepwise_manual "
            "--output-summary-json docs/reports/radarsimpy_migration_stepwise_manual/summary.json "
            "--trial-free-tier-geometry --require-runtime-provider-mode --require-radarsimpy-simulation-used"
        )
    else:
        migration = _load_json(migration_path)
        migration_ready = _status_str(migration.get("migration_status", "")) == "ready"
        summary = migration.get("summary")
        summary_map = dict(summary) if isinstance(summary, Mapping) else {}
        stages.append(
            _build_stage(
                name="migration_stepwise",
                source_json=migration_path,
                ready=migration_ready,
                details={
                    "migration_status": _status_str(migration.get("migration_status", "")),
                    "candidate_backend_count": int(summary_map.get("candidate_backend_count", 0)),
                    "pass_count": int(summary_map.get("pass_count", 0)),
                    "fail_count": int(summary_map.get("fail_count", 0)),
                    "blocked_count": int(summary_map.get("blocked_count", 0)),
                },
            )
        )
        if not migration_ready:
            next_actions.append(
                "Run: PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_migration_stepwise.py "
                "--output-root docs/reports/radarsimpy_migration_stepwise_manual "
                "--output-summary-json docs/reports/radarsimpy_migration_stepwise_manual/summary.json "
                "--trial-free-tier-geometry --require-runtime-provider-mode --require-radarsimpy-simulation-used"
            )

    if e2e_rollup_path is None:
        stages.append(
            _build_stage(
                name="real_e2e",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run: PYTHON_BIN=.venv/bin/python RUN_RADARSIMPY_MIGRATION_STEPWISE=1 "
            "RUN_RADARSIMPY_PERIODIC_LOCK=1 RADARSIMPY_PILOT_TRIAL_FREE_TIER_GEOMETRY=1 "
            "RADARSIMPY_MIGRATION_TRIAL_FREE_TIER_GEOMETRY=1 scripts/run_integration_full_real_e2e.sh"
        )
    else:
        e2e = _load_json(e2e_rollup_path)
        all_passed = _bool(e2e.get("all_steps_passed"))
        step_rcs = e2e.get("step_rcs")
        step_map = dict(step_rcs) if isinstance(step_rcs, Mapping) else {}
        required_steps = [
            "radarsimpy_pilot",
            "radarsimpy_migration_stepwise",
            "radarsimpy_periodic_manifest",
            "radarsimpy_periodic_parity_lock",
        ]
        missing_required = [name for name in required_steps if name not in step_map]
        required_ok = all(int(step_map.get(name, 1)) == 0 for name in required_steps if name in step_map)
        e2e_ready = bool(all_passed and required_ok and len(missing_required) == 0)
        stages.append(
            _build_stage(
                name="real_e2e",
                source_json=e2e_rollup_path,
                ready=e2e_ready,
                details={
                    "all_steps_passed": all_passed,
                    "failed_steps": list(e2e.get("failed_steps", [])),
                    "required_steps_present": int(len(required_steps) - len(missing_required)),
                    "required_steps_total": int(len(required_steps)),
                    "missing_required_steps": missing_required,
                },
            )
        )
        if not e2e_ready:
            next_actions.append(
                "Run: PYTHON_BIN=.venv/bin/python RUN_RADARSIMPY_MIGRATION_STEPWISE=1 "
                "RUN_RADARSIMPY_PERIODIC_LOCK=1 RADARSIMPY_PILOT_TRIAL_FREE_TIER_GEOMETRY=1 "
                "RADARSIMPY_MIGRATION_TRIAL_FREE_TIER_GEOMETRY=1 scripts/run_integration_full_real_e2e.sh"
            )

    required_stages = stages
    ready_count = sum(1 for s in required_stages if _bool(s.get("ready")))
    blocked_count = sum(1 for s in required_stages if not _bool(s.get("ready")))
    overall_ready = bool(blocked_count == 0)

    ok_head, head_commit = _run_git(repo_root, ["rev-parse", "--short", "HEAD"])
    ok_branch, branch = _run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])

    snapshot: Dict[str, Any] = {
        "report_name": "radarsimpy_progress_snapshot",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "reports_root": str(reports_root),
        "overall_ready": overall_ready,
        "ready_count": int(ready_count),
        "stage_count": int(len(required_stages)),
        "blocked_count": int(blocked_count),
        "git": {
            "head_commit_short": head_commit if ok_head else "",
            "branch": branch if ok_branch else "",
        },
        "stages": stages,
        "next_actions": next_actions,
    }

    print("RadarSimPy progress snapshot")
    print(f"workspace_root={snapshot['workspace_root']}")
    print(f"overall_ready={snapshot['overall_ready']}")
    print(
        f"progress={snapshot['ready_count']}/{snapshot['stage_count']} ready "
        f"({(100.0 * snapshot['ready_count'] / max(snapshot['stage_count'], 1)):.1f}%), "
        f"blocked={snapshot['blocked_count']}"
    )
    for stage in stages:
        print(
            f"- {stage['name']}: {stage['status']} "
            f"(source={stage['source_json'] or '-'})"
        )

    if len(next_actions) == 0:
        print("next_actions:")
        print("- All RadarSimPy integration checks are green.")
    else:
        print("next_actions:")
        for action in next_actions:
            print(f"- {action}")

    if str(args.output_json).strip() != "":
        out_path = Path(str(args.output_json)).expanduser()
        if not out_path.is_absolute():
            out_path = (repo_root / out_path).resolve()
        else:
            out_path = out_path.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        print(f"wrote {out_path}")

    if bool(args.strict_ready) and (not overall_ready):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
