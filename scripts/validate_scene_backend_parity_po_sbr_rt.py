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
                "scene_id": "po_sbr_parity_reference",
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
                            "range_m": 23.0,
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
    po_sbr_paths_json = root / "po_sbr_paths.json"
    amp = 1.0 / (23.0 * 23.0)
    po_sbr_paths_json.write_text(
        json.dumps(
            {
                "version": 1,
                "paths": [
                    {
                        "chirp_index": 0,
                        "range_m": 23.0,
                        "range_mode": "one_way",
                        "radial_velocity_mps": 0.0,
                        "az_deg": 0.0,
                        "el_deg": 0.0,
                        "amp": amp,
                        "path_id": "po_path_0",
                        "reflection_order": 1,
                    },
                    {
                        "chirp_index": 1,
                        "range_m": 23.0,
                        "range_mode": "one_way",
                        "radial_velocity_mps": 0.0,
                        "az_deg": 0.0,
                        "el_deg": 0.0,
                        "amp": amp,
                        "path_id": "po_path_1",
                        "reflection_order": 1,
                    },
                    {
                        "chirp_index": 2,
                        "range_m": 23.0,
                        "range_mode": "one_way",
                        "radial_velocity_mps": 0.0,
                        "az_deg": 0.0,
                        "el_deg": 0.0,
                        "amp": amp,
                        "path_id": "po_path_2",
                        "reflection_order": 1,
                    },
                    {
                        "chirp_index": 3,
                        "range_m": 23.0,
                        "range_mode": "one_way",
                        "radial_velocity_mps": 0.0,
                        "az_deg": 0.0,
                        "el_deg": 0.0,
                        "amp": amp,
                        "path_id": "po_path_3",
                        "reflection_order": 1,
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    scene_json = root / "scene_po_sbr_candidate.json"
    scene_json.write_text(
        json.dumps(
            {
                "scene_id": "po_sbr_parity_candidate",
                "backend": {
                    "type": "po_sbr_rt",
                    "n_chirps": 4,
                    "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                    "rx_pos_m": [
                        [0.0, 0.00185, 0.0],
                        [0.0, 0.0037, 0.0],
                        [0.0, 0.00555, 0.0],
                        [0.0, 0.0074, 0.0],
                    ],
                    "po_sbr_paths_json": str(po_sbr_paths_json),
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
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_parity_") as td:
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
        assert payload["candidate_backend_type"] == "po_sbr_rt"
        assert payload["parity"]["pass"] is True

    print("validate_scene_backend_parity_po_sbr_rt: pass")


if __name__ == "__main__":
    run()
