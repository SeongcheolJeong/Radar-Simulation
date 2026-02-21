#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _write_reference_scene(root: Path) -> Path:
    scene_json = root / "scene_analytic_reference.json"
    scene_json.write_text(
        json.dumps(
            {
                "scene_id": "sionna_parity_reference",
                "backend": {
                    "type": "analytic_targets",
                    "n_chirps": 4,
                    "chirp_interval_s": 4.0e-5,
                    "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                    "rx_pos_m": [
                        [0.0, 0.00185, 0.0],
                        [0.0, 0.0037, 0.0],
                        [0.0, 0.00555, 0.0],
                        [0.0, 0.0074, 0.0],
                    ],
                    "targets": [
                        {
                            "range_m": 25.0,
                            "radial_velocity_mps": 0.0,
                            "az_deg": 0.0,
                            "el_deg": 0.0,
                            "amp": 1.0,
                            "range_amp_exponent": 2.0,
                            "path_id": "ref_path",
                        }
                    ],
                    "noise_sigma": 0.0,
                },
                "radar": {
                    "fc_hz": 77e9,
                    "slope_hz_per_s": 20e12,
                    "fs_hz": 20e6,
                    "samples_per_chirp": 1024,
                },
                "map_config": {
                    "nfft_range": 1024,
                    "nfft_doppler": 64,
                    "nfft_angle": 32,
                    "range_bin_limit": 128,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return scene_json


def _write_candidate_scene(root: Path) -> Path:
    sionna_paths_json = root / "sionna_paths.json"
    sionna_paths_json.write_text(
        json.dumps(
            {
                "version": 1,
                "paths_by_chirp": [
                    [
                        {
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (25.0 * 25.0),
                            "path_id": "cand_path_0",
                            "material_tag": "sionna_rt",
                            "reflection_order": 1,
                        }
                    ],
                    [
                        {
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (25.0 * 25.0),
                            "path_id": "cand_path_1",
                            "material_tag": "sionna_rt",
                            "reflection_order": 1,
                        }
                    ],
                    [
                        {
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (25.0 * 25.0),
                            "path_id": "cand_path_2",
                            "material_tag": "sionna_rt",
                            "reflection_order": 1,
                        }
                    ],
                    [
                        {
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 1.0 / (25.0 * 25.0),
                            "path_id": "cand_path_3",
                            "material_tag": "sionna_rt",
                            "reflection_order": 1,
                        }
                    ],
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    scene_json = root / "scene_sionna_candidate.json"
    scene_json.write_text(
        json.dumps(
            {
                "scene_id": "sionna_parity_candidate",
                "backend": {
                    "type": "sionna_rt",
                    "n_chirps": 4,
                    "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                    "rx_pos_m": [
                        [0.0, 0.00185, 0.0],
                        [0.0, 0.0037, 0.0],
                        [0.0, 0.00555, 0.0],
                        [0.0, 0.0074, 0.0],
                    ],
                    "sionna_paths_json": str(sionna_paths_json),
                    "noise_sigma": 0.0,
                },
                "radar": {
                    "fc_hz": 77e9,
                    "slope_hz_per_s": 20e12,
                    "fs_hz": 20e6,
                    "samples_per_chirp": 1024,
                },
                "map_config": {
                    "nfft_range": 1024,
                    "nfft_doppler": 64,
                    "nfft_angle": 32,
                    "range_bin_limit": 128,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return scene_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_sionna_parity_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        ref_scene = _write_reference_scene(root)
        cand_scene = _write_candidate_scene(root)
        out_root = root / "parity_run"
        out_json = out_root / "summary.json"

        proc = subprocess.run(
            [
                "python3",
                "scripts/run_scene_backend_parity.py",
                "--reference-scene-json",
                str(ref_scene),
                "--candidate-scene-json",
                str(cand_scene),
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene backend parity completed." in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["reference_backend_type"] == "analytic_targets"
        assert payload["candidate_backend_type"] == "sionna_rt"
        assert payload["parity"]["pass"] is True

    print("validate_scene_backend_parity_sionna_rt: pass")


if __name__ == "__main__":
    run()
