#!/usr/bin/env python3
import argparse
import json
import math
import platform
from pathlib import Path
from typing import Any, Dict

import numpy as np

from avxsim.constants import C0
from avxsim.runtime_coupling import detect_runtime_modules
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


DEFAULT_RUNTIME_PROVIDER = (
    "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run RadarSimPy runtime pilot for scene pipeline integration")
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output summary JSON path")
    p.add_argument("--scene-id", default="radarsimpy_runtime_pilot_v1", help="Scene id")
    p.add_argument("--n-chirps", type=int, default=8, help="Number of chirps")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="ADC samples per chirp")
    p.add_argument(
        "--radarsimpy-runtime-provider",
        default=DEFAULT_RUNTIME_PROVIDER,
        help="Runtime provider spec for radarsimpy_rt backend",
    )
    p.add_argument(
        "--radarsimpy-repo-root",
        default="external/radarsimpy",
        help="RadarSimPy reference repository root",
    )
    p.add_argument("--target-range-m", type=float, default=25.0, help="Synthetic target range (one-way meters)")
    p.add_argument("--target-az-deg", type=float, default=0.0, help="Synthetic target azimuth (deg)")
    p.add_argument("--target-el-deg", type=float, default=0.0, help="Synthetic target elevation (deg)")
    p.add_argument(
        "--target-radial-velocity-mps",
        type=float,
        default=0.0,
        help="Synthetic target radial velocity (m/s)",
    )
    p.add_argument(
        "--runtime-failure-policy",
        default="use_static",
        choices=("use_static", "error"),
        help="Runtime failure policy for radarsimpy provider (default: use_static)",
    )
    p.add_argument(
        "--simulation-mode",
        default="radarsimpy_adc",
        choices=("auto", "analytic_paths", "radarsimpy_adc"),
        help="Provider simulation mode (default: radarsimpy_adc)",
    )
    p.add_argument(
        "--fallback-to-analytic-on-error",
        action="store_true",
        help="Allow provider to fallback to analytic paths when real simulation fails",
    )
    p.add_argument(
        "--runtime-device",
        default="cpu",
        choices=("cpu", "gpu"),
        help="RadarSimPy simulation device",
    )
    p.add_argument(
        "--trial-free-tier-geometry",
        action="store_true",
        help="Use 1 TX / 1 RX geometry to satisfy free-tier channel limits",
    )
    p.add_argument(
        "--require-real-simulation",
        action="store_true",
        help="Fail when provider_runtime_info.simulation_used is not true",
    )
    p.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Write blocked summary instead of failing when unexpected runtime errors occur",
    )
    return p.parse_args()


def _collect_diagnostics(repo_root: Path) -> Dict[str, Any]:
    system = platform.system()
    module_report = detect_runtime_modules(["radarsimpy"])
    missing_modules = [name for name, item in module_report.items() if not bool(item.get("available", False))]

    preflight_blockers = []
    if not repo_root.exists():
        preflight_blockers.append("missing_repo")
    if len(missing_modules) > 0:
        preflight_blockers.append("missing_required_modules")

    diagnostics = {
        "platform": system,
        "repo_root": str(repo_root),
        "repo_exists": bool(repo_root.exists()),
        "module_report": module_report,
        "missing_modules": missing_modules,
        "preflight_blockers": preflight_blockers,
    }
    return diagnostics


def _build_scene_payload(args: argparse.Namespace, repo_root: Path) -> Dict[str, Any]:
    static_payload = _build_static_fallback_paths_payload(args=args)
    if bool(args.trial_free_tier_geometry):
        tx_pos_m = [[0.0, 0.0, 0.0]]
        rx_pos_m = [[0.0, 0.00185, 0.0]]
    else:
        tx_pos_m = [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]]
        rx_pos_m = [
            [0.0, 0.00185, 0.0],
            [0.0, 0.0037, 0.0],
            [0.0, 0.00555, 0.0],
            [0.0, 0.0074, 0.0],
        ]
    return {
        "scene_id": str(args.scene_id),
        "backend": {
            "type": "radarsimpy_rt",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": tx_pos_m,
            "rx_pos_m": rx_pos_m,
            "runtime_provider": str(args.radarsimpy_runtime_provider),
            "runtime_required_modules": ["radarsimpy"],
            "runtime_failure_policy": str(args.runtime_failure_policy),
            "runtime_input": {
                "radarsimpy_repo_root": str(repo_root),
                "target_range_m": float(args.target_range_m),
                "target_az_deg": float(args.target_az_deg),
                "target_el_deg": float(args.target_el_deg),
                "target_radial_velocity_mps": float(args.target_radial_velocity_mps),
                "material_tag": "radarsimpy_runtime",
                "path_id_prefix": "radarsimpy_runtime",
                "simulation_mode": str(args.simulation_mode),
                "fallback_to_analytic_on_error": bool(args.fallback_to_analytic_on_error),
                "device": str(args.runtime_device),
            },
            "paths_payload": static_payload,
            "noise_sigma": 0.0,
        },
        "radar": {
            "fc_hz": 77e9,
            "slope_hz_per_s": 20e12,
            "fs_hz": 20e6,
            "samples_per_chirp": int(args.samples_per_chirp),
        },
        "map_config": {
            "nfft_range": int(args.samples_per_chirp),
            "nfft_doppler": 64,
            "nfft_angle": 32,
            "range_bin_limit": min(int(args.samples_per_chirp // 2), 256),
        },
    }


def _build_static_fallback_paths_payload(args: argparse.Namespace) -> Dict[str, Any]:
    n_chirps = int(args.n_chirps)
    fc_hz = float(77e9)
    lam = C0 / fc_hz
    range_m = max(float(args.target_range_m), 1.0e-6)
    az = math.radians(float(args.target_az_deg))
    el = math.radians(float(args.target_el_deg))
    ux = float(math.cos(el) * math.cos(az))
    uy = float(math.cos(el) * math.sin(az))
    uz = float(math.sin(el))
    tau = float(2.0 * range_m / C0)
    doppler_hz = float(2.0 * float(args.target_radial_velocity_mps) / lam)
    amp = float(1.0 / (range_m * range_m))

    paths_by_chirp = []
    for chirp_idx in range(n_chirps):
        paths_by_chirp.append(
            [
                {
                    "delay_s": tau,
                    "doppler_hz": doppler_hz,
                    "unit_direction": [ux, uy, uz],
                    "amp": amp,
                    "path_id": f"radarsimpy_static_c{chirp_idx:04d}",
                    "material_tag": "radarsimpy_static_fallback",
                    "reflection_order": 1,
                }
            ]
        )
    return {"paths_by_chirp": paths_by_chirp}


def _load_runtime_resolution(radar_map_npz: Path) -> Dict[str, Any]:
    payload = np.load(str(radar_map_npz), allow_pickle=False)
    metadata = json.loads(str(payload["metadata_json"]))
    runtime_resolution = metadata.get("runtime_resolution")
    if not isinstance(runtime_resolution, dict):
        raise ValueError("runtime_resolution not found in radar_map metadata")
    return runtime_resolution


def _command_hint(args: argparse.Namespace) -> str:
    return (
        "PYTHONPATH=src python3 scripts/run_scene_runtime_radarsimpy_pilot.py "
        f"--output-root {args.output_root} "
        f"--output-summary-json {args.output_summary_json} "
        f"--radarsimpy-repo-root {args.radarsimpy_repo_root} "
        f"--runtime-failure-policy {args.runtime_failure_policy} "
        f"--simulation-mode {args.simulation_mode} "
        f"--runtime-device {args.runtime_device}"
    )


def main() -> None:
    args = parse_args()
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    out_summary = Path(args.output_summary_json)
    out_summary.parent.mkdir(parents=True, exist_ok=True)

    repo_root = Path(str(args.radarsimpy_repo_root).strip()).expanduser()
    if not repo_root.is_absolute():
        repo_root = (Path.cwd() / repo_root).resolve()
    else:
        repo_root = repo_root.resolve()

    diagnostics = _collect_diagnostics(repo_root=repo_root)
    command_hint = _command_hint(args)
    scene_payload = _build_scene_payload(args=args, repo_root=repo_root)
    scene_json = out_root / "scene_radarsimpy_runtime_pilot.json"
    scene_json.write_text(json.dumps(scene_payload, indent=2), encoding="utf-8")

    try:
        run_out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(out_root / "pipeline_outputs"),
            run_hybrid_estimation=False,
        )
    except Exception as exc:
        blockers = list(diagnostics.get("preflight_blockers", []))
        if len(blockers) == 0:
            blockers = ["runtime_execution_failed"]
        summary = {
            "scene_id": str(args.scene_id),
            "pilot_status": "blocked",
            "blockers": blockers,
            "diagnostics": diagnostics,
            "runtime_failure_policy": str(args.runtime_failure_policy),
            "runtime_error": f"{type(exc).__name__}: {exc}",
            "recommended_command": command_hint,
            "scene_json": str(scene_json),
            "output_dir": None,
            "path_list_json": None,
            "adc_cube_npz": None,
            "radar_map_npz": None,
            "frame_count": 0,
            "path_count": 0,
            "runtime_resolution": None,
        }
        out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("Scene runtime RadarSimPy pilot completed.")
        print("  pilot_status: blocked")
        print(f"  blockers: {blockers}")
        print(f"  output_summary_json: {out_summary}")
        if not bool(args.allow_blocked):
            raise RuntimeError(
                "RadarSimPy runtime pilot failed unexpectedly. Use --allow-blocked to keep blocked report."
            )
        return

    runtime_resolution = _load_runtime_resolution(Path(run_out["radar_map_npz"]))
    runtime_mode = str(runtime_resolution.get("mode", ""))
    fallback_used = runtime_mode == "runtime_failed_fallback_static"
    provider_info = runtime_resolution.get("provider_runtime_info")
    simulation_used = None
    if isinstance(provider_info, dict):
        simulation_used = provider_info.get("simulation_used")
        if simulation_used is not None:
            simulation_used = bool(simulation_used)
    path_payload = json.loads(Path(run_out["path_list_json"]).read_text(encoding="utf-8"))
    path_count = int(sum(len(chirp_paths) for chirp_paths in path_payload))

    blockers = []
    if bool(args.require_real_simulation) and (simulation_used is not True):
        blockers.append("real_simulation_not_used")
    pilot_status = "blocked" if len(blockers) > 0 else "executed"
    summary = {
        "scene_id": str(scene_payload["scene_id"]),
        "pilot_status": pilot_status,
        "blockers": blockers,
        "diagnostics": diagnostics,
        "runtime_failure_policy": str(args.runtime_failure_policy),
        "simulation_mode": str(args.simulation_mode),
        "runtime_device": str(args.runtime_device),
        "trial_free_tier_geometry": bool(args.trial_free_tier_geometry),
        "require_real_simulation": bool(args.require_real_simulation),
        "provider_simulation_used": simulation_used,
        "runtime_fallback_used": bool(fallback_used),
        "recommended_command": command_hint,
        "scene_json": str(scene_json),
        "output_dir": str(out_root / "pipeline_outputs"),
        "path_list_json": str(run_out["path_list_json"]),
        "adc_cube_npz": str(run_out["adc_cube_npz"]),
        "radar_map_npz": str(run_out["radar_map_npz"]),
        "frame_count": int(run_out["frame_count"]),
        "path_count": int(path_count),
        "runtime_resolution": runtime_resolution,
    }
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Scene runtime RadarSimPy pilot completed.")
    print(f"  pilot_status: {pilot_status}")
    print(f"  scene_id: {summary['scene_id']}")
    print(f"  frame_count: {summary['frame_count']}")
    print(f"  path_count: {summary['path_count']}")
    print(f"  runtime_mode: {runtime_mode}")
    print(f"  provider_simulation_used: {simulation_used}")
    print(f"  runtime_fallback_used: {fallback_used}")
    print(f"  blockers: {blockers}")
    print(f"  output_summary_json: {out_summary}")

    if (pilot_status != "executed") and (not bool(args.allow_blocked)):
        raise RuntimeError("RadarSimPy runtime pilot blocked. Use --allow-blocked to keep blocked report.")


if __name__ == "__main__":
    main()
