#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence


PROFILE_FAMILY_BY_ID: Dict[str, str] = {
    "single_target_range25_v1": "equivalence_strict",
    "single_target_az20_range25_v1": "equivalence_strict",
    "single_target_vel3_range25_v1": "equivalence_strict",
    "dual_target_split_range25_v1": "realism_informational",
    "single_target_material_loss_range25_v1": "realism_informational",
    "mesh_dihedral_range25_v1": "realism_informational",
    "mesh_trihedral_range25_v1": "realism_informational",
    "single_target_ghost_comp_v1": "realism_informational",
    "single_target_clutter_comp_v1": "realism_informational",
}
DEFAULT_PROFILES = tuple(PROFILE_FAMILY_BY_ID.keys())
DEFAULT_GATE_FAMILIES = ("equivalence_strict",)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run backend golden-path + KPI campaign across scene-equivalence profiles "
            "and summarize divergence for radar-developer tracking."
        )
    )
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output matrix summary JSON path")
    p.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Profile id to include (repeatable, comma-separated allowed). Default: built-in matrix",
    )
    p.add_argument("--n-chirps", type=int, default=8, help="Chirps per profile run")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="Samples per chirp")
    p.add_argument(
        "--strict-all-ready",
        action="store_true",
        help="Exit non-zero unless every gate-required profile campaign_status is ready",
    )
    p.add_argument(
        "--gate-profile-family",
        action="append",
        default=[],
        help=(
            "Profile family to treat as gate-required (repeatable, comma-separated allowed). "
            "Default: equivalence_strict"
        ),
    )
    p.add_argument(
        "--python-bin",
        default=str(sys.executable),
        help="Python interpreter used for subprocess runner calls",
    )

    p.add_argument(
        "--sionna-runtime-provider",
        default=None,
        help="Optional override for sionna runtime provider",
    )
    p.add_argument(
        "--sionna-runtime-required-modules",
        default=None,
        help="Optional override for sionna required modules CSV",
    )
    p.add_argument(
        "--po-sbr-runtime-provider",
        default=None,
        help="Optional override for PO-SBR runtime provider",
    )
    p.add_argument(
        "--po-sbr-runtime-required-modules",
        default=None,
        help="Optional override for PO-SBR required modules CSV",
    )
    p.add_argument(
        "--po-sbr-repo-root",
        default=None,
        help="Optional override for PO-SBR repo root",
    )
    p.add_argument(
        "--po-sbr-geometry-path",
        default=None,
        help="Optional override for PO-SBR geometry path",
    )
    p.add_argument(
        "--radar-compensation-lock-json",
        default=None,
        help="Optional profile compensation lock JSON passed through to golden-path runner",
    )
    return p.parse_args()


def _parse_profiles(items: Sequence[str]) -> List[str]:
    if len(items) == 0:
        return list(DEFAULT_PROFILES)
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            profile = str(token).strip()
            if profile == "":
                continue
            if profile not in out:
                out.append(profile)
    if len(out) == 0:
        raise ValueError("at least one profile must be selected")
    return out


def _parse_gate_profile_families(items: Sequence[str]) -> List[str]:
    if len(items) == 0:
        return list(DEFAULT_GATE_FAMILIES)
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            family = str(token).strip()
            if family == "":
                continue
            if family not in out:
                out.append(family)
    if len(out) == 0:
        raise ValueError("at least one gate profile family must be selected")
    return out


def _profile_family_for_id(profile: str) -> str:
    return str(PROFILE_FAMILY_BY_ID.get(profile, "custom")).strip() or "custom"


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _run_cmd(cmd: List[str], cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
        "cmd": cmd,
    }


def _build_optional_golden_overrides(args: argparse.Namespace) -> List[str]:
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
    add_opt(
        "--sionna-runtime-required-modules",
        args.sionna_runtime_required_modules,
        allow_empty=True,
    )
    add_opt("--po-sbr-runtime-provider", args.po_sbr_runtime_provider)
    add_opt(
        "--po-sbr-runtime-required-modules",
        args.po_sbr_runtime_required_modules,
        allow_empty=True,
    )
    add_opt("--po-sbr-repo-root", args.po_sbr_repo_root)
    add_opt("--po-sbr-geometry-path", args.po_sbr_geometry_path)
    add_opt("--radar-compensation-lock-json", args.radar_compensation_lock_json)
    return out


def _summarize_profile_row(
    profile: str,
    profile_family_hint: str,
    gate_families: Sequence[str],
    golden_json: Path,
    kpi_json: Path,
    run_steps: Mapping[str, Any],
) -> Dict[str, Any]:
    gate_family_set = set(gate_families)
    profile_family = str(profile_family_hint).strip() or "custom"
    row = {
        "profile": profile,
        "profile_family": profile_family,
        "gate_required": bool(profile_family in gate_family_set),
        "golden_summary_json": str(golden_json),
        "kpi_summary_json": str(kpi_json),
        "run_steps": dict(run_steps),
        "run_ok": False,
        "golden_summary": None,
        "kpi_summary": None,
        "campaign_status": None,
        "blockers": [],
        "parity_fail_count": None,
        "divergence_pairs": [],
    }

    if not all(bool(step.get("ok", False)) for step in run_steps.values()):
        return row
    if not golden_json.exists() or not kpi_json.exists():
        return row

    golden = _load_json(golden_json)
    kpi = _load_json(kpi_json)
    family_from_golden = str(golden.get("scene_profile_family", "")).strip()
    if family_from_golden != "":
        row["profile_family"] = family_from_golden
        row["gate_required"] = bool(family_from_golden in gate_family_set)
    row["run_ok"] = True
    row["golden_summary"] = golden.get("summary")
    row["kpi_summary"] = kpi.get("summary")
    row["campaign_status"] = str(kpi.get("campaign_status", "")).strip()
    row["blockers"] = list(kpi.get("blockers", []) if isinstance(kpi.get("blockers"), list) else [])

    summary = kpi.get("summary")
    if isinstance(summary, Mapping):
        row["parity_fail_count"] = int(summary.get("parity_fail_count", 0))

    divergence_pairs: List[Dict[str, Any]] = []
    comparisons = kpi.get("comparisons")
    if isinstance(comparisons, list):
        for item in comparisons:
            if not isinstance(item, Mapping):
                continue
            if not bool(item.get("compared", False)):
                continue
            parity = item.get("parity")
            if not isinstance(parity, Mapping):
                continue
            if bool(parity.get("pass", False)):
                continue
            divergence_pairs.append(
                {
                    "reference_backend": str(item.get("reference_backend", "")),
                    "candidate_backend": str(item.get("candidate_backend", "")),
                    "failures": parity.get("failures", []),
                }
            )
    row["divergence_pairs"] = divergence_pairs
    return row


def main() -> None:
    args = parse_args()
    profiles = _parse_profiles(args.profile)
    gate_families = _parse_gate_profile_families(args.gate_profile_family)

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

    summary_json = Path(args.output_summary_json).expanduser()
    if not summary_json.is_absolute():
        summary_json = (cwd / summary_json).resolve()
    else:
        summary_json = summary_json.resolve()
    summary_json.parent.mkdir(parents=True, exist_ok=True)

    python_path = Path(str(args.python_bin)).expanduser()
    if not python_path.is_absolute():
        # Preserve venv launcher paths: resolving symlinks here can collapse
        # to the system interpreter and lose venv-installed dependencies.
        python_path = cwd / python_path
    python_bin = str(python_path)
    golden_overrides = _build_optional_golden_overrides(args=args)

    profile_rows: List[Dict[str, Any]] = []
    for profile in profiles:
        profile_root = output_root / profile
        profile_root.mkdir(parents=True, exist_ok=True)

        golden_json = profile_root / "scene_backend_golden_path.json"
        kpi_json = profile_root / "scene_backend_kpi_campaign.json"

        run_golden = _run_cmd(
            [
                python_bin,
                "scripts/run_scene_backend_golden_path.py",
                "--scene-equivalence-profile",
                profile,
                "--n-chirps",
                str(int(args.n_chirps)),
                "--samples-per-chirp",
                str(int(args.samples_per_chirp)),
                "--strict-nonexecuted",
                "--output-root",
                str(profile_root / "golden_outputs"),
                "--output-summary-json",
                str(golden_json),
                *golden_overrides,
            ],
            cwd=cwd,
        )

        validate_golden = _run_cmd(
            [
                python_bin,
                "scripts/validate_scene_backend_golden_path_report.py",
                "--summary-json",
                str(golden_json),
                "--require-backend-executed",
                "analytic_targets,sionna_rt,po_sbr_rt",
            ],
            cwd=cwd,
        )

        run_kpi = _run_cmd(
            [
                python_bin,
                "scripts/run_scene_backend_kpi_campaign.py",
                "--golden-path-summary-json",
                str(golden_json),
                "--output-summary-json",
                str(kpi_json),
            ],
            cwd=cwd,
        )

        validate_kpi = _run_cmd(
            [
                python_bin,
                "scripts/validate_scene_backend_kpi_campaign_report.py",
                "--summary-json",
                str(kpi_json),
            ],
            cwd=cwd,
        )

        run_steps = {
            "run_golden": run_golden,
            "validate_golden": validate_golden,
            "run_kpi": run_kpi,
            "validate_kpi": validate_kpi,
        }
        profile_rows.append(
            _summarize_profile_row(
                profile=profile,
                profile_family_hint=_profile_family_for_id(profile),
                gate_families=gate_families,
                golden_json=golden_json,
                kpi_json=kpi_json,
                run_steps=run_steps,
            )
        )

    run_error_count = int(sum(1 for row in profile_rows if not bool(row.get("run_ok", False))))
    ready_count = int(sum(1 for row in profile_rows if str(row.get("campaign_status", "")) == "ready"))
    blocked_count = int(sum(1 for row in profile_rows if str(row.get("campaign_status", "")) == "blocked"))

    gated_rows = [row for row in profile_rows if bool(row.get("gate_required", False))]
    gate_profile_count = int(len(gated_rows))
    gate_ready_count = int(sum(1 for row in gated_rows if str(row.get("campaign_status", "")) == "ready"))
    gate_blocked_count = int(
        sum(
            1
            for row in gated_rows
            if bool(row.get("run_ok", False)) and str(row.get("campaign_status", "")) != "ready"
        )
    )

    info_rows = [row for row in profile_rows if not bool(row.get("gate_required", False))]
    info_profile_count = int(len(info_rows))
    info_ready_count = int(sum(1 for row in info_rows if str(row.get("campaign_status", "")) == "ready"))
    info_blocked_count = int(
        sum(
            1
            for row in info_rows
            if bool(row.get("run_ok", False)) and str(row.get("campaign_status", "")) != "ready"
        )
    )

    if run_error_count > 0:
        matrix_status = "failed"
    elif gate_blocked_count > 0:
        matrix_status = "blocked"
    else:
        matrix_status = "ready"

    report = {
        "version": 1,
        "python_bin": python_bin,
        "profiles": profiles,
        "gate_profile_families": gate_families,
        "output_root": str(output_root),
        "matrix_status": matrix_status,
        "summary": {
            "profile_count": int(len(profiles)),
            "ready_profile_count": ready_count,
            "blocked_profile_count": blocked_count,
            "failed_profile_count": run_error_count,
            "gate_profile_count": gate_profile_count,
            "gate_ready_profile_count": gate_ready_count,
            "gate_blocked_profile_count": gate_blocked_count,
            "informational_profile_count": info_profile_count,
            "informational_ready_profile_count": info_ready_count,
            "informational_blocked_profile_count": info_blocked_count,
        },
        "rows": profile_rows,
    }
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Scene backend KPI scenario matrix completed.")
    print(f"  matrix_status: {matrix_status}")
    print(f"  profile_count: {len(profiles)}")
    print(f"  gate_profile_families: {gate_families}")
    print(f"  ready_profiles: {ready_count}")
    print(f"  blocked_profiles: {blocked_count}")
    print(f"  gate_blocked_profiles: {gate_blocked_count}")
    print(f"  failed_profiles: {run_error_count}")
    print(f"  output_summary_json: {summary_json}")

    if bool(args.strict_all_ready) and matrix_status != "ready":
        raise RuntimeError("scenario matrix is not fully ready")


if __name__ == "__main__":
    main()
