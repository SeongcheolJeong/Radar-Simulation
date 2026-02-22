#!/usr/bin/env python3
import argparse
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from avxsim.runtime_coupling import detect_runtime_modules
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run PO-SBR runtime pilot (Linux+NVIDIA target)")
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output summary JSON path")
    p.add_argument("--scene-id", default="po_sbr_runtime_pilot_v1", help="Scene id")
    p.add_argument("--n-chirps", type=int, default=8, help="Number of chirps")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="ADC samples per chirp")
    p.add_argument(
        "--po-sbr-repo-root",
        default="external/PO-SBR-Python",
        help="PO-SBR repo root containing POsolver.py",
    )
    p.add_argument(
        "--geometry-path",
        default="geometries/plate.obj",
        help="Geometry path (absolute or relative to --po-sbr-repo-root)",
    )
    p.add_argument("--alpha-deg", type=float, default=180.0, help="Polarization alpha angle")
    p.add_argument("--phi-deg", type=float, default=90.0, help="Observation phi angle")
    p.add_argument("--theta-deg", type=float, default=90.0, help="Observation theta angle")
    p.add_argument("--freq-hz", type=float, default=77e9, help="PO-SBR simulation frequency")
    p.add_argument("--rays-per-lambda", type=float, default=3.0, help="Rays per wavelength")
    p.add_argument("--bounces", type=int, default=2, help="Maximum bounces")
    p.add_argument(
        "--target-radial-velocity-mps",
        type=float,
        default=0.0,
        help="Synthetic radial velocity used for Doppler mapping",
    )
    p.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Write blocked summary instead of failing when runtime prerequisites are not met",
    )
    return p.parse_args()


def _resolve_geometry_path(repo_root: Path, geometry_path: str) -> Path:
    path = Path(str(geometry_path).strip()).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _detect_nvidia_runtime() -> bool:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return False
    try:
        subprocess.run([exe, "--help"], capture_output=True, text=True, check=True)
        return True
    except Exception:
        return False


def _collect_blockers(repo_root: Path, geometry_path: Path) -> Tuple[List[str], Dict[str, Any]]:
    system = platform.system()
    module_report = detect_runtime_modules(["rtxpy", "igl"])
    missing_modules = [name for name, item in module_report.items() if not bool(item.get("available", False))]
    nvidia_ok = _detect_nvidia_runtime()

    blockers: List[str] = []
    if not repo_root.exists():
        blockers.append("missing_repo")
    if not geometry_path.exists():
        blockers.append("missing_geometry")
    if len(missing_modules) > 0:
        blockers.append("missing_required_modules")
    if system != "Linux":
        blockers.append(f"unsupported_platform:{system}")
    if not nvidia_ok:
        blockers.append("missing_nvidia_runtime")

    diagnostics = {
        "platform": system,
        "repo_root": str(repo_root),
        "repo_exists": bool(repo_root.exists()),
        "geometry_path": str(geometry_path),
        "geometry_exists": bool(geometry_path.exists()),
        "module_report": module_report,
        "missing_modules": missing_modules,
        "nvidia_runtime_available": bool(nvidia_ok),
    }
    return blockers, diagnostics


def _build_scene_payload(args: argparse.Namespace, repo_root: Path, geometry_path: Path) -> Dict[str, Any]:
    return {
        "scene_id": str(args.scene_id),
        "backend": {
            "type": "po_sbr_rt",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
            "rx_pos_m": [
                [0.0, 0.00185, 0.0],
                [0.0, 0.0037, 0.0],
                [0.0, 0.00555, 0.0],
                [0.0, 0.0074, 0.0],
            ],
            "runtime_provider": "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr",
            "runtime_required_modules": ["rtxpy", "igl"],
            "runtime_failure_policy": "error",
            "runtime_input": {
                "po_sbr_repo_root": str(repo_root),
                "geometry_path": str(geometry_path),
                "alpha_deg": float(args.alpha_deg),
                "phi_deg": float(args.phi_deg),
                "theta_deg": float(args.theta_deg),
                "freq_hz": float(args.freq_hz),
                "rays_per_lambda": float(args.rays_per_lambda),
                "bounces": int(args.bounces),
                "radial_velocity_mps": float(args.target_radial_velocity_mps),
                "material_tag": "po_sbr_runtime",
            },
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


def _load_runtime_resolution(radar_map_npz: Path) -> Dict[str, Any]:
    payload = np.load(str(radar_map_npz), allow_pickle=False)
    metadata = json.loads(str(payload["metadata_json"]))
    runtime_resolution = metadata.get("runtime_resolution")
    if not isinstance(runtime_resolution, dict):
        raise ValueError("runtime_resolution not found in radar_map metadata")
    return runtime_resolution


def _linux_command_hint(args: argparse.Namespace) -> str:
    return (
        "PYTHONPATH=src python3 scripts/run_scene_runtime_po_sbr_pilot.py "
        f"--output-root {args.output_root} "
        f"--output-summary-json {args.output_summary_json} "
        f"--po-sbr-repo-root {args.po_sbr_repo_root} "
        f"--geometry-path {args.geometry_path}"
    )


def main() -> None:
    args = parse_args()
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    out_summary = Path(args.output_summary_json)
    out_summary.parent.mkdir(parents=True, exist_ok=True)

    repo_root = Path(str(args.po_sbr_repo_root).strip()).expanduser()
    if not repo_root.is_absolute():
        repo_root = (Path.cwd() / repo_root).resolve()
    else:
        repo_root = repo_root.resolve()
    geometry_path = _resolve_geometry_path(repo_root=repo_root, geometry_path=str(args.geometry_path))

    blockers, diagnostics = _collect_blockers(repo_root=repo_root, geometry_path=geometry_path)
    command_hint = _linux_command_hint(args)

    if len(blockers) > 0:
        summary = {
            "scene_id": str(args.scene_id),
            "pilot_status": "blocked",
            "blockers": blockers,
            "diagnostics": diagnostics,
            "recommended_linux_command": command_hint,
            "scene_json": None,
            "output_dir": None,
            "path_list_json": None,
            "adc_cube_npz": None,
            "radar_map_npz": None,
            "frame_count": 0,
            "path_count": 0,
            "runtime_resolution": None,
        }
        out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("Scene runtime PO-SBR pilot completed.")
        print("  pilot_status: blocked")
        print(f"  blockers: {blockers}")
        print(f"  output_summary_json: {out_summary}")
        if not bool(args.allow_blocked):
            raise RuntimeError(
                "PO-SBR runtime prerequisites not met. Re-run on Linux+NVIDIA or use --allow-blocked."
            )
        return

    scene_payload = _build_scene_payload(args=args, repo_root=repo_root, geometry_path=geometry_path)
    scene_json = out_root / "scene_po_sbr_runtime_pilot.json"
    scene_json.write_text(json.dumps(scene_payload, indent=2), encoding="utf-8")
    run_out = run_object_scene_to_radar_map_json(
        scene_json_path=str(scene_json),
        output_dir=str(out_root / "pipeline_outputs"),
        run_hybrid_estimation=False,
    )

    runtime_resolution = _load_runtime_resolution(Path(run_out["radar_map_npz"]))
    path_payload = json.loads(Path(run_out["path_list_json"]).read_text(encoding="utf-8"))
    path_count = int(sum(len(chirp_paths) for chirp_paths in path_payload))
    summary = {
        "scene_id": str(scene_payload["scene_id"]),
        "pilot_status": "executed",
        "blockers": [],
        "diagnostics": diagnostics,
        "recommended_linux_command": command_hint,
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

    print("Scene runtime PO-SBR pilot completed.")
    print("  pilot_status: executed")
    print(f"  scene_id: {summary['scene_id']}")
    print(f"  frame_count: {summary['frame_count']}")
    print(f"  path_count: {summary['path_count']}")
    print(f"  runtime_mode: {runtime_resolution.get('mode')}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()
