#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run repeated PO-SBR physical full-track bundles and emit one stability report "
            "for local radar-developer readiness tracking."
        )
    )
    p.add_argument("--output-root", required=True, help="Output root directory for campaign artifacts")
    p.add_argument("--output-summary-json", required=True, help="Output stability summary JSON path")
    p.add_argument("--runs", type=int, default=2, help="Number of repeated bundle runs (default: 2)")
    p.add_argument("--n-chirps", type=int, default=8, help="Chirps per profile run")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="Samples per chirp")
    p.add_argument(
        "--strict-stable",
        action="store_true",
        help="Exit non-zero unless campaign_status=stable",
    )
    p.add_argument(
        "--python-bin",
        default=str(sys.executable),
        help="Python interpreter used for subprocess runner calls",
    )
    p.add_argument("--sionna-runtime-provider", default=None, help="Optional sionna runtime provider override")
    p.add_argument(
        "--sionna-runtime-required-modules",
        default=None,
        help="Optional sionna required modules CSV override",
    )
    p.add_argument("--po-sbr-runtime-provider", default=None, help="Optional PO-SBR runtime provider override")
    p.add_argument(
        "--po-sbr-runtime-required-modules",
        default=None,
        help="Optional PO-SBR required modules CSV override",
    )
    p.add_argument("--po-sbr-repo-root", default=None, help="Optional PO-SBR repo root override")
    p.add_argument("--po-sbr-geometry-path", default=None, help="Optional PO-SBR geometry path override")
    return p.parse_args()


def _run_cmd(cmd: List[str], cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
        "cmd": cmd,
    }


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _build_optional_bundle_overrides(args: argparse.Namespace) -> List[str]:
    out: List[str] = []

    def add_opt(flag: str, value: Any, allow_empty: bool = False) -> None:
        if value is None:
            return
        raw_text = str(value)
        text = raw_text.strip()
        if (not allow_empty) and text == "":
            return
        out.extend([flag, raw_text if allow_empty else text])

    add_opt("--sionna-runtime-provider", args.sionna_runtime_provider)
    add_opt("--sionna-runtime-required-modules", args.sionna_runtime_required_modules, allow_empty=True)
    add_opt("--po-sbr-runtime-provider", args.po_sbr_runtime_provider)
    add_opt("--po-sbr-runtime-required-modules", args.po_sbr_runtime_required_modules, allow_empty=True)
    add_opt("--po-sbr-repo-root", args.po_sbr_repo_root)
    add_opt("--po-sbr-geometry-path", args.po_sbr_geometry_path)
    return out


def _run_summary_row(
    run_index: int,
    run_root: Path,
    matrix_summary_json: Path,
    bundle_summary_json: Path,
    run_bundle: Mapping[str, Any],
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "run_index": int(run_index),
        "run_root": str(run_root),
        "matrix_summary_json": str(matrix_summary_json),
        "bundle_summary_json": str(bundle_summary_json),
        "run_bundle": dict(run_bundle),
        "run_ok": bool(run_bundle.get("ok", False)),
        "full_track_status": None,
        "matrix_status": None,
        "gate_blocked_profile_count": None,
        "informational_blocked_profile_count": None,
        "po_sbr_executed_profile_count": None,
        "required_profile_count": None,
        "missing_profile_count": None,
    }
    if not row["run_ok"]:
        return row
    if not bundle_summary_json.exists():
        return row
    payload = _load_json(bundle_summary_json)
    row["full_track_status"] = str(payload.get("full_track_status", "")).strip() or None
    row["matrix_status"] = str(payload.get("matrix_status", "")).strip() or None
    summary = payload.get("summary")
    if isinstance(summary, Mapping):
        row["gate_blocked_profile_count"] = int(summary.get("gate_blocked_profile_count", 0))
        row["informational_blocked_profile_count"] = int(summary.get("informational_blocked_profile_count", 0))
        row["po_sbr_executed_profile_count"] = int(summary.get("po_sbr_executed_profile_count", 0))
        row["required_profile_count"] = int(summary.get("required_profile_count", 0))
        row["missing_profile_count"] = int(summary.get("missing_profile_count", 0))
    return row


def main() -> None:
    args = parse_args()

    if int(args.runs) <= 0:
        raise ValueError("--runs must be > 0")
    if int(args.n_chirps) <= 0:
        raise ValueError("--n-chirps must be > 0")
    if int(args.samples_per_chirp) <= 0:
        raise ValueError("--samples-per-chirp must be > 0")

    cwd = Path.cwd().resolve()
    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = (cwd / output_root).resolve()
    else:
        output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    output_summary_json = Path(args.output_summary_json).expanduser()
    if not output_summary_json.is_absolute():
        output_summary_json = (cwd / output_summary_json).resolve()
    else:
        output_summary_json = output_summary_json.resolve()
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    python_path = Path(str(args.python_bin)).expanduser()
    if not python_path.is_absolute():
        python_path = (cwd / python_path).resolve()
    python_bin = str(python_path)
    bundle_overrides = _build_optional_bundle_overrides(args=args)

    rows: List[Dict[str, Any]] = []
    for i in range(int(args.runs)):
        run_index = int(i + 1)
        run_root = output_root / f"run_{run_index:02d}"
        run_root.mkdir(parents=True, exist_ok=True)
        matrix_summary_json = run_root / "scene_backend_kpi_scenario_matrix.json"
        bundle_summary_json = run_root / "po_sbr_physical_full_track_bundle.json"

        run_bundle = _run_cmd(
            [
                python_bin,
                "scripts/run_po_sbr_physical_full_track_bundle.py",
                "--output-root",
                str(run_root / "bundle_outputs"),
                "--matrix-summary-json",
                str(matrix_summary_json),
                "--output-summary-json",
                str(bundle_summary_json),
                "--n-chirps",
                str(int(args.n_chirps)),
                "--samples-per-chirp",
                str(int(args.samples_per_chirp)),
                *bundle_overrides,
            ],
            cwd=cwd,
        )
        rows.append(
            _run_summary_row(
                run_index=run_index,
                run_root=run_root,
                matrix_summary_json=matrix_summary_json,
                bundle_summary_json=bundle_summary_json,
                run_bundle=run_bundle,
            )
        )

    run_error_count = int(sum(1 for row in rows if not bool(row.get("run_ok", False))))
    full_track_blocked_count = int(
        sum(1 for row in rows if str(row.get("full_track_status", "")).strip() not in ("ready",))
    )
    matrix_not_ready_count = int(
        sum(1 for row in rows if str(row.get("matrix_status", "")).strip() not in ("ready",))
    )
    gate_blocked_run_count = int(
        sum(1 for row in rows if int(row.get("gate_blocked_profile_count") or 0) > 0)
    )

    blockers: List[str] = []
    if run_error_count > 0:
        blockers.append("bundle_runner_failed")
    if full_track_blocked_count > 0:
        blockers.append("full_track_bundle_not_ready")
    if matrix_not_ready_count > 0:
        blockers.append("matrix_not_ready")
    if gate_blocked_run_count > 0:
        blockers.append("gate_profiles_blocked")

    campaign_status = "stable" if len(blockers) == 0 else "unstable"
    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_root": str(cwd),
        "python_executable": str(Path(sys.executable).resolve()),
        "campaign_status": campaign_status,
        "blockers": blockers,
        "requested_runs": int(args.runs),
        "rows": rows,
        "summary": {
            "requested_runs": int(args.runs),
            "completed_runs": int(len(rows)),
            "run_error_count": run_error_count,
            "full_track_blocked_count": full_track_blocked_count,
            "matrix_not_ready_count": matrix_not_ready_count,
            "gate_blocked_run_count": gate_blocked_run_count,
            "stable_run_count": int(len(rows) - full_track_blocked_count),
        },
    }
    output_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PO-SBR physical full-track stability campaign completed.")
    print(f"  campaign_status: {campaign_status}")
    print(f"  blockers: {blockers}")
    print(f"  requested_runs: {int(args.runs)}")
    print(f"  run_error_count: {run_error_count}")
    print(f"  full_track_blocked_count: {full_track_blocked_count}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_stable) and campaign_status != "stable":
        raise RuntimeError("physical full-track stability campaign is not stable")


if __name__ == "__main__":
    main()
