#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run first real runtime scene pilot using Mitsuba-backed provider")
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output summary json path")
    p.add_argument("--scene-id", default="mitsuba_runtime_pilot_v1", help="Scene id")
    p.add_argument("--n-chirps", type=int, default=8, help="Number of chirps")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="ADC samples per chirp")
    p.add_argument("--target-range-m", type=float, default=25.0, help="Target sphere center range along +x")
    p.add_argument("--target-radius-m", type=float, default=0.5, help="Target sphere radius")
    p.add_argument("--target-radial-velocity-mps", type=float, default=0.0, help="Target radial velocity along +x")
    return p.parse_args()


def _build_scene_payload(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "scene_id": str(args.scene_id),
        "backend": {
            "type": "sionna_rt",
            "n_chirps": int(args.n_chirps),
            "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
            "rx_pos_m": [
                [0.0, 0.00185, 0.0],
                [0.0, 0.0037, 0.0],
                [0.0, 0.00555, 0.0],
                [0.0, 0.0074, 0.0],
            ],
            "runtime_provider": "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba",
            "runtime_required_modules": ["mitsuba", "drjit"],
            "runtime_failure_policy": "error",
            "runtime_input": {
                "ego_origin_m": [0.0, 0.0, 0.0],
                "chirp_interval_s": 4.0e-5,
                "spheres": [
                    {
                        "center_m": [float(args.target_range_m), 0.0, 0.0],
                        "radius_m": float(args.target_radius_m),
                        "velocity_mps": [float(args.target_radial_velocity_mps), 0.0, 0.0],
                        "amp": 1.0,
                        "range_amp_exponent": 2.0,
                        "path_id_prefix": "mitsuba_pilot_target",
                        "material_tag": "metal",
                        "reflection_order": 1,
                    }
                ],
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


def main() -> None:
    args = parse_args()
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    scene_payload = _build_scene_payload(args)
    scene_json = out_root / "scene_mitsuba_runtime_pilot.json"
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
        "scene_json": str(scene_json),
        "output_dir": str(out_root / "pipeline_outputs"),
        "path_list_json": str(run_out["path_list_json"]),
        "adc_cube_npz": str(run_out["adc_cube_npz"]),
        "radar_map_npz": str(run_out["radar_map_npz"]),
        "frame_count": int(run_out["frame_count"]),
        "path_count": int(path_count),
        "runtime_resolution": runtime_resolution,
    }

    out_summary = Path(args.output_summary_json)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Scene runtime Mitsuba pilot completed.")
    print(f"  scene_id: {summary['scene_id']}")
    print(f"  frame_count: {summary['frame_count']}")
    print(f"  path_count: {summary['path_count']}")
    print(f"  runtime_mode: {runtime_resolution.get('mode')}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()
